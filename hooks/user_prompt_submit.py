#!/usr/bin/env python3
import json

from memory_hooks import (
    build_user_prompt_context,
    capture_ultra_short_prompt,
    is_subagent_event,
    load_payload,
    log_payload,
    maybe_capture_user_prompt,
    prepare_memory_environment,
)


def main() -> int:
    payload = load_payload()
    log_payload(payload, "user-prompt-submit")
    if is_subagent_event(payload):
        return 0

    prepare_memory_environment()
    capture_ultra_short_prompt(payload)
    maybe_capture_user_prompt(payload)
    additional_context = build_user_prompt_context(payload)
    if not additional_context:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": additional_context,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
