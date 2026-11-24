"""Strict reading of untrusted JSON for every CouncilFlow script.

One place owns the fail-closed rules: a repeated object key or a NaN/Infinity
constant is an error, never a silent last-wins value or a nonfinite number.
It also owns ContractError and the bounded text-field checks that the message
and Plan contracts share. This module validates data only; it is not a
transport, sandbox or security boundary.
"""
from __future__ import annotations

import json

MAX_ITEMS = 128
MAX_STRING = 8192


class ContractError(ValueError):
    """A contract rule failed: `code` names the rule, `field` the location."""

    def __init__(self, code, field, detail):
        self.code, self.field, self.detail = code, field, detail
        super().__init__(f"{code} at {field}: {detail}")


def fail(code, field, detail):
    raise ContractError(code, field, detail)


def loads(source, field="$"):
    """Decode JSON text or bytes, rejecting duplicate keys and NaN/Infinity.

    Raises ContractError("duplicate_key" or "nonfinite") for those two rules;
    malformed JSON or encoding raises the usual ValueError/UnicodeError.
    """
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail("duplicate_key", field, key)
            result[key] = value
        return result

    def constant(value):
        fail("nonfinite", field, value)

    return json.loads(source, object_pairs_hook=pairs, parse_constant=constant)


def text(value, field, limit=MAX_STRING):
    """A nonempty single-line string of at most `limit` characters."""
    if type(value) is not str or not value.strip() or len(value) > limit:
        fail("string", field, f"expected nonempty string, at most {limit} characters")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        fail("control", field, "control characters are not allowed")
    return value


def identity(value, field):
    """A bounded identifier such as a plan, task or criterion id."""
    return text(value, field, 128)


def criterion(value, field):
    """Plan text that may keep tabs and LF or CRLF line breaks."""
    if type(value) is not str or not value.strip() or len(value) > MAX_STRING:
        fail("string", field, f"expected nonempty string, at most {MAX_STRING} characters")
    if any((ord(char) < 32 and char not in "\t\r\n") or ord(char) == 127
           for char in value):
        fail("control", field, "control characters other than tabs and line breaks are not allowed")
    if "\r" in value.replace("\r\n", ""):
        fail("control", field, "carriage returns must be part of CRLF line breaks")
    return value
