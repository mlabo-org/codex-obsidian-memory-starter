#!/usr/bin/env python3
from memory_hooks import (
    is_subagent_event,
    load_payload,
    log_payload,
    maybe_capture_episode,
    prepare_memory_environment,
)


def main() -> int:
    payload = load_payload()
    log_payload(payload, "stop")
    if is_subagent_event(payload):
        return 0

    prepare_memory_environment()
    maybe_capture_episode(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
