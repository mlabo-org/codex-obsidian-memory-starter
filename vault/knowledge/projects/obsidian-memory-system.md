# Obsidian Memory System

## Goal

Use Obsidian as a visible local UI for a hippocampus-first memory system where short-lived episodes are the primary intake layer and durable knowledge is downstream.

## Current State

- The old vault prototype was deleted
- The new vault structure is `episodes/`, `knowledge/`, `maps/`, `archive/`, and `templates/`
- Durable categories live inside `knowledge/rules/`, `knowledge/decisions/`, and `knowledge/projects/`
- `~/.codex/AGENTS.md` now governs startup reads and session-end episode writes

## Next Focus

- Refine promotion heuristics from episode to durable note
- Tune episode expiration and cleanup in real use
- Observe whether the new intake path is lighter and less noisy than the old knowledge-first structure
