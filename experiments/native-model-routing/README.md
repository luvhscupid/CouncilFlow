# Native model-routing experiment

This package provides deterministic, offline checks for declared route and
qualification data. It does not dispatch provider requests, authenticate policy,
enforce limits, or isolate operating-system permissions.

`route-policy.json` is intentionally empty and unapproved. A route is eligible
only when policy explicitly approves it, the exact identity matches provider,
route ID, model ID and harness, role/task constraints pass, qualification evidence
is verified and current, required capabilities and reasoning effort match, and
declared limits are present and satisfied. Missing information fails closed.

The native adapter builds explicit `model` and `reasoning_effort` arguments but
does not dispatch. If a host cannot express a distinct model, it returns
`UNSUPPORTED_NATIVE_MODEL_ROUTING`. Requested, host-reported and independently
effective identities stay separate; an absent observation remains null and is
reported as `NATIVE_MODEL_ROUTING_UNVERIFIED`.

```python
from routing import native_child_request, validate_dispatch_observation

identity = {"provider": "provider-id", "route_id": "endpoint-id",
            "model_id": "model-id", "harness": "codex-child"}
request = native_child_request(identity, "low", supports_model=True)
# REQUEST_READY_NOT_DISPATCHED. Use a real host result before recording identity.
```

No example above names an approved route. Synthetic tests can be run with:

```powershell
python -m unittest tests.test_native_model_routing -v
```

See [the technical contract](../../docs/technical/native-model-routing.md),
[host evidence](../../evidence/native-model-routing/native-capability.json), and
[benchmark report](../../docs/benchmarks/native-model-routing.md).
