"""Opt-in metadata-only Claude Code JSON/JSONL ingestion; no host or network access."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

from codex_adapter import _identifier, _reject_constant, _unique_object
from digest import build_digest
from recorder import record, validate, append_jsonl

SUPPORTED = {'system', 'assistant', 'user', 'result', 'stream_event'}
SYSTEM_TYPES = {'init', 'compact_boundary', 'status', 'api_retry', 'hook_started',
                'hook_progress', 'hook_response', 'model_refusal_fallback',
                'model_refusal_no_fallback', 'conversation_reset'}
STREAM_TYPES = {'message_start', 'message_delta', 'message_stop', 'content_block_start',
                'content_block_delta', 'content_block_stop', 'ping', 'error'}
RESULT_TYPES = {'success', 'error_max_turns', 'error_during_execution',
                'error_max_budget_usd', 'error_max_structured_output_retries'}
COUNTERS = {'input': 'input_tokens', 'output': 'output_tokens',
            'cached_input': 'cache_read_input_tokens', 'cache_creation': 'cache_creation_input_tokens'}
MODEL_COUNTERS = {'input': 'inputTokens', 'output': 'outputTokens',
                  'cached_input': 'cacheReadInputTokens', 'cache_creation': 'cacheCreationInputTokens'}


def _tokens(value, issues, line, fields=COUNTERS):
    values = {name: None for name in fields}
    if value is None:
        return values
    if not isinstance(value, dict):
        issues.append(f'line {line}: invalid usage object; contents omitted')
        return values
    for name, field in fields.items():
        count = value.get(field)
        if count is None:
            continue
        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            values[name] = count
        else:
            issues.append(f'line {line}: invalid {field}; value omitted')
    return values


def parse_stream(raw, *, run_id=None, gateway=None, gateway_source='caller-supplied',
                 configured_model=None, upstream_model=None, route=None,
                 repository_revision=None, elapsed_ms=None, process_exit_code=None,
                 cancelled=False, cli_version=None, source='supplied-capture'):
    """Use latest result turn usage, never add message/delta/model snapshots.

    upstream_model is a compatibility alias for a configured hint, never proof
    of the effective upstream. Gateway labels are explicit caller assertions.
    """
    if gateway not in (None, 'xkiro'):
        raise ValueError('only xkiro or unknown gateway is supported')
    if gateway_source not in ('caller-supplied', 'configured', 'synthetic-fixture'):
        raise ValueError('invalid gateway provenance')
    if source not in ('supplied-capture', 'synthetic-fixture'):
        raise ValueError('unsupported source attribution')
    if process_exit_code is not None and (not isinstance(process_exit_code, int) or isinstance(process_exit_code, bool)):
        raise ValueError('exit code must be an integer or unknown')
    if elapsed_ms is not None and (not isinstance(elapsed_ms, int) or isinstance(elapsed_ms, bool) or elapsed_ms < 0):
        raise ValueError('elapsed milliseconds must be nonnegative or unknown')
    if configured_model and upstream_model and configured_model != upstream_model:
        raise ValueError('conflicting configured model hints')
    configured_model = configured_model or upstream_model
    for label in (configured_model, cli_version):
        if label is not None and not _identifier(label):
            raise ValueError('invalid metadata label')
    expected_route = 'claude-code/xkiro/stream-json' if gateway else 'claude-code/unknown/stream-json'
    if route is not None and route != expected_route:
        raise ValueError('route must agree with explicit gateway label')
    run_id = run_id or uuid.uuid4().hex
    issues, safe_events, results, steps = [], [], [], []
    sessions, models, retries_seen = set(), set(), set()
    messages_seen, result_ids = {}, {}
    latest, pending, streaming = None, False, False
    aborted = False
    observed_retry_events = 0
    gateway_retry = None
    reported_versions = set()

    def model_label(value, number):
        if value is None:
            return None
        label = _identifier(value)
        if label:
            models.add(label)
        else:
            issues.append(f'line {number}: invalid model identity omitted')
        return label

    lines = raw.splitlines()
    input_format = 'jsonl'
    try:
        whole = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
        if isinstance(whole, dict):
            lines = [raw]  # --output-format json may be pretty-printed.
            input_format = 'json'
    except (ValueError, UnicodeDecodeError, RecursionError):
        pass
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeDecodeError, RecursionError):
            issues.append(f'line {number}: malformed JSON/encoding; contents omitted')
            safe_events.append({'type': 'malformed'})
            continue
        if not isinstance(event, dict) or not isinstance(event.get('type'), str) or event['type'] not in SUPPORTED:
            issues.append(f'line {number}: unsupported event type; contents omitted')
            safe_events.append({'type': 'unsupported'})
            continue
        if 'schema_version' in event or 'version' in event:
            issues.append(f'line {number}: explicit event version unsupported')
            safe_events.append({'type': 'unsupported-version'})
            continue
        kind = event['type']
        safe = {'type': kind}
        sid = event.get('session_id')
        if sid is not None:
            if isinstance(sid, str) and sid:
                sessions.add(sid)  # Compare in memory; never persist session IDs.
            else:
                issues.append(f'line {number}: invalid session identity')
        extension = event.get('gateway')
        if isinstance(extension, dict) and extension.get('retry_count') is not None:
            count = extension['retry_count']
            if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
                gateway_retry = count  # Latest unverified extension snapshot, not a sum.
            else:
                issues.append(f'line {number}: invalid gateway retry count omitted')
        if kind == 'system':
            subtype = event.get('subtype')
            if not isinstance(subtype, str) or subtype not in SYSTEM_TYPES:
                issues.append(f'line {number}: unsupported system subtype; contents omitted')
            else:
                safe['subtype'] = subtype
                if subtype == 'init':
                    label = model_label(event.get('model'), number)
                    if label: safe['model'] = label
                    version = event.get('claude_code_version')
                    if version is not None:
                        if _identifier(version): reported_versions.add(version)
                        else: issues.append(f'line {number}: invalid reported CLI version omitted')
                elif subtype == 'api_retry':
                    retry_id = event.get('uuid')
                    if isinstance(retry_id, str) and retry_id:
                        if retry_id not in retries_seen:
                            retries_seen.add(retry_id); observed_retry_events += 1
                    else:
                        observed_retry_events += 1
                elif subtype == 'conversation_reset':
                    issues.append(f'line {number}: session reset; whole-session accounting unavailable')
        elif kind == 'assistant':
            main_loop = not event.get('parent_tool_use_id') and not event.get('agent_id')
            if main_loop: pending = True
            message = event.get('message')
            if not isinstance(message, dict):
                issues.append(f'line {number}: invalid assistant message; contents omitted')
            elif main_loop:
                label = model_label(message.get('model'), number)
                if label: safe['model'] = label
                metrics = _tokens(message.get('usage'), issues, number)
                metrics['output'] = None  # Step output may be a placeholder; use result output.
                message_id = message.get('id')
                if message.get('usage') is not None:
                    if not isinstance(message_id, str) or not message_id:
                        issues.append(f'line {number}: step usage has no message identity; not counted')
                    elif message_id in messages_seen:
                        if messages_seen[message_id] != metrics:
                            issues.append(f'line {number}: conflicting duplicate message usage')
                    else:
                        messages_seen[message_id] = metrics
                        steps.append({'step_index': len(steps)+1, 'usage': metrics, 'usage_scope': 'message'})
            if main_loop and event.get('aborted') is True:
                aborted = True
            if event.get('error') is not None:
                safe['error_present'] = True  # Keep no raw error code/text.
        elif kind == 'user':
            if not event.get('isReplay') and not event.get('parent_tool_use_id'):
                pending = True
        elif kind == 'stream_event':
            nested = event.get('event')
            nested_type = nested.get('type') if isinstance(nested, dict) else None
            if not isinstance(nested_type, str) or nested_type not in STREAM_TYPES:
                issues.append(f'line {number}: unsupported partial event; contents omitted')
            else:
                safe['event_type'] = nested_type
                if nested_type == 'message_start':
                    pending, streaming = True, True
                elif nested_type == 'message_stop':
                    streaming = False
                elif nested_type == 'error':
                    issues.append(f'line {number}: partial stream error reported')
                # Incremental token/text/thinking deltas are deliberately not accumulated.
        elif kind == 'result':
            subtype = event.get('subtype')
            if not isinstance(subtype, str) or subtype not in RESULT_TYPES:
                issues.append(f'line {number}: unsupported result subtype')
                safe_events.append({'type': 'unsupported-result'})
                continue
            error = event.get('is_error')
            if error is not None and not isinstance(error, bool):
                issues.append(f'line {number}: invalid result error flag')
            metrics = _tokens(event.get('usage'), issues, number)
            per_model = {}
            model_usage = event.get('modelUsage')
            if model_usage is not None and not isinstance(model_usage, dict):
                issues.append(f'line {number}: invalid cumulative model usage')
            elif isinstance(model_usage, dict):
                for name, counters in model_usage.items():
                    label = _identifier(name)
                    if label: per_model[label] = _tokens(counters, issues, number, MODEL_COUNTERS)
                    else: issues.append(f'line {number}: invalid cumulative model label omitted')
            snapshot = {'subtype': subtype, 'is_error': error is True or subtype != 'success',
                        'usage': metrics, 'model_usage_snapshot': per_model}
            rid = event.get('uuid')
            if isinstance(rid, str) and rid in result_ids:
                if result_ids[rid] != snapshot:
                    issues.append(f'line {number}: conflicting duplicate result')
                safe_events.append({'type': 'duplicate-result'})
                continue
            if isinstance(rid, str): result_ids[rid] = snapshot
            if latest == snapshot and not pending:
                safe_events.append({'type': 'duplicate-result'})
                continue
            latest, pending = snapshot, False
            results.append(snapshot)
            safe.update(snapshot)
        safe_events.append(safe)
    metrics = dict(latest['usage']) if latest and not pending else _tokens(None, issues, 0)
    if streaming:
        issues.append('partial message stream has no message_stop')
    if len(sessions) > 1:
        issues.append('multiple sessions mixed; usage attribution unknown')
        metrics = _tokens(None, issues, 0)
        results, steps = [], []
        for event in safe_events:
            event.pop('usage', None); event.pop('model_usage_snapshot', None)
    notes = ['Only harness-reported counters; gateway/upstream usage and billing are unknown.']
    if len(models) > 1:
        notes.append('model changed or multiple main-loop model labels observed')
    if configured_model: notes.append(f'CONFIGURED model (caller metadata): {configured_model}')
    if models: notes.append('REPORTED main-loop models: ' + ', '.join(sorted(models)))
    notes.append('Effective upstream model UNKNOWN; gateway label provenance: ' + (gateway_source if gateway else 'UNKNOWN'))
    if cancelled or aborted:
        status = 'cancelled'
    elif process_exit_code not in (None, 0) or (latest and latest['is_error']):
        status = 'failed'
    elif not latest or pending:
        status = 'partial'
    else:
        status = 'completed'
    if not latest: notes.append('no result usage event; record usage remains unknown')
    notes.extend(issues)
    reasons = {name: '' if value is not None else 'not reported by final result turn usage' for name, value in metrics.items()}
    item = record(run_id=run_id, harness='claude-code', gateway=gateway, route=expected_route,
                  upstream_model=None, repository_revision=repository_revision, elapsed_ms=elapsed_ms,
                  usage_scope='turn' if latest and not pending and len(sessions) <= 1 else 'unknown',
                  usage={**metrics, 'reported_cost': None, 'availability': {**reasons, 'reported_cost': 'no authoritative xKiro billing data'}},
                  acceptance={'status': 'unknown', 'evidence_ref': None, 'provenance': 'unknown'},
                  source_kind=f'claude-code-json-events-{source}', notes=notes)
    validate(item)
    return {'record': item, 'events_seen': len(safe_events), 'unsupported_or_malformed': issues,
            'complete': status == 'completed' and not issues, 'completion_status': status,
            'process_exit_code': process_exit_code, 'configured_model': configured_model,
            'reported_model': next(iter(models)) if len(models) == 1 else None,
            'reported_models': sorted(models), 'effective_upstream_model': None,
            'result_snapshots': results, 'message_usage': steps, 'session_usage': None,
            'gateway_usage': None, 'upstream_usage': None, 'billing': None,
            'harness_retry_event_count': observed_retry_events or None,
            'gateway_retry_count_snapshot': gateway_retry,
            'source': {'harness': 'claude-code', 'cli_version': cli_version,
                       'reported_cli_versions': sorted(reported_versions), 'source': source,
                       'input_format': input_format, 'metadata_provenance': 'caller-supplied; not independently authenticated',
                       'gateway_provenance': gateway_source if gateway else 'UNKNOWN',
                       'configured_model_status': 'CONFIGURED' if configured_model else 'UNKNOWN',
                       'reported_model_status': 'REPORTED' if models else 'UNKNOWN',
                       'effective_upstream_status': 'UNKNOWN', 'usage_source': 'Claude Code result.usage; not gateway billing',
                       'gateway_retry_source': 'unverified captured extension snapshot, not provider retry accounting',
                       'input_sha256': hashlib.sha256(raw).hexdigest(), 'input_bytes': len(raw),
                       'payload_storage': 'allowlisted-metadata-only'}, 'sanitized_events': safe_events}


def process(raw, *, artifact_dir, **kwargs):
    result = parse_stream(raw, **kwargs)
    safe = (json.dumps({'events': result.pop('sanitized_events')}, sort_keys=True)+'\n').encode()
    result['digest'] = build_digest(safe, b'', exit_code=result['process_exit_code'], command=[],
                                    artifact_dir=artifact_dir, run_id=result['record']['run_id'])
    result['digest']['source_kind'] = 'sanitized-claude-event-metadata; not a process capture'
    if not result['complete']:
        result['digest']['flags'] = sorted(set(result['digest']['flags']) | {'DIGEST_INCOMPLETE'})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('events', nargs='?', help='Explicit JSON or JSONL capture; defaults to stdin')
    parser.add_argument('--artifacts', required=True)
    parser.add_argument('--records')
    parser.add_argument('--run-id')
    parser.add_argument('--gateway', choices=('xkiro',))
    parser.add_argument('--gateway-source', choices=('caller-supplied','configured','synthetic-fixture'), default='caller-supplied')
    parser.add_argument('--configured-model', '--model', dest='configured_model')
    parser.add_argument('--cli-version')
    parser.add_argument('--route')
    parser.add_argument('--revision')
    parser.add_argument('--elapsed-ms', type=int)
    parser.add_argument('--process-exit-code', type=int)
    parser.add_argument('--cancelled', action='store_true')
    parser.add_argument('--source', choices=('supplied-capture','synthetic-fixture'), default='supplied-capture')
    args = parser.parse_args(argv)
    raw = Path(args.events).read_bytes() if args.events else sys.stdin.buffer.read()
    result = process(raw, artifact_dir=args.artifacts, run_id=args.run_id, gateway=args.gateway,
                     gateway_source=args.gateway_source, configured_model=args.configured_model,
                     cli_version=args.cli_version, route=args.route, repository_revision=args.revision,
                     elapsed_ms=args.elapsed_ms, process_exit_code=args.process_exit_code,
                     cancelled=args.cancelled, source=args.source)
    if args.records: append_jsonl(args.records, result['record'])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
