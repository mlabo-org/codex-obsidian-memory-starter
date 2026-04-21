#!/usr/bin/env python3
import json

from memory_hooks import (
    build_session_start_context,
    is_subagent_event,
    load_payload,
    log_payload,
    prepare_memory_environment,
)


def main() -> int:
    payload = load_payload()
    log_payload(payload, "session-start")
    if is_subagent_event(payload):
        return 0

    prepare_memory_environment()
    additional_context = build_session_start_context(payload)
    if not additional_context:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": additional_context,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
