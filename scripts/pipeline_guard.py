#!/usr/bin/env python3
"""
Unified pipeline enforcement for the TrpB MetaDynamics repo.

Modes:
  - Hook mode:   python3 scripts/pipeline_guard.py --hook
                 Reads Claude hook JSON from stdin and exits 0/2.
  - Check mode:  python3 scripts/pipeline_guard.py --check
                 Prints current stage and verification status.
  - Advance:     python3 scripts/pipeline_guard.py --advance
                 Verifies the current stage, then advances on success.
  - Force:       python3 scripts/pipeline_guard.py --force N
                 Human override to set the current stage.
  - CLI gate:    python3 scripts/pipeline_guard.py <command ...>
                 Evaluates whether a command is allowed at the current stage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_EXIT_CODE = 2

STAGE_NAMES = {
    0: "profiler",
    1: "librarian",
    2: "janitor",
    3: "runner",
    4: "skeptic",
    5: "journalist",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def state_path(root: Path) -> Path:
    return root / "PIPELINE_STATE.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def stage_key(stage_num: int) -> str:
    return f"{stage_num}_{STAGE_NAMES[stage_num]}"


def resolve_repo_path(root: Path, rel_path: str) -> Path:
    return root / Path(rel_path)


def load_state(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.exists():
        raise FileNotFoundError(f"Missing state file: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_state(root: Path, state: dict[str, Any]) -> None:
    state["last_updated"] = now_iso()
    path = state_path(root)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def compile_pattern(pattern: str) -> re.Pattern[str]:
    if pattern.startswith("re:"):
        return re.compile(pattern[3:], re.IGNORECASE)
    return re.compile(re.escape(pattern), re.IGNORECASE)


def command_matches(command: str, pattern: str) -> bool:
    return compile_pattern(pattern).search(command) is not None


def format_result(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def format_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def verify_file_exists(root: Path, spec: dict[str, Any]) -> tuple[bool, list[str]]:
    rel_path = spec.get("path")
    if not rel_path:
        return False, ["verification.path is missing"]

    path = resolve_repo_path(root, rel_path)
    exists = path.exists()
    is_nonempty = path.stat().st_size > 0 if exists and path.is_file() else False
    require_nonempty = bool(spec.get("nonempty", False))
    ok = exists and (is_nonempty if require_nonempty else True)

    lines = [f"{format_result(ok)} {rel_path}"]
    if exists and path.is_file():
        lines.append(f"  size={path.stat().st_size} bytes")
    elif not exists:
        lines.append(f"  missing={path}")

    return ok, lines


def verify_files_nonempty(root: Path, spec: dict[str, Any]) -> tuple[bool, list[str]]:
    rel_paths = spec.get("paths", [])
    if not rel_paths:
        return False, ["verification.paths is missing"]

    ok = True
    lines: list[str] = []
    for rel_path in rel_paths:
        path = resolve_repo_path(root, rel_path)
        file_ok = path.exists() and path.is_file() and path.stat().st_size > 0
        ok = ok and file_ok
        lines.append(f"{format_result(file_ok)} {rel_path}")
        if path.exists() and path.is_file():
            lines.append(f"  size={path.stat().st_size} bytes")
        elif not path.exists():
            lines.append(f"  missing={path}")
        else:
            lines.append(f"  not_a_file={path}")
    return ok, lines


def verify_janitor(root: Path, spec: dict[str, Any]) -> tuple[bool, list[str]]:
    required_dirs = spec.get("required_dirs", [])
    path_conflicts = spec.get("path_conflicts", [])

    ok = True
    lines: list[str] = []

    for rel_dir in required_dirs:
        path = resolve_repo_path(root, rel_dir)
        dir_ok = path.is_dir()
        ok = ok and dir_ok
        lines.append(f"{format_result(dir_ok)} dir {rel_dir}")
        if not dir_ok:
            lines.append(f"  missing={path}")

    for conflict in path_conflicts:
        files = conflict.get("files", [])
        forbidden = conflict.get("forbidden_substrings", [])
        label = conflict.get("label", "path_conflict")

        for rel_file in files:
            path = resolve_repo_path(root, rel_file)
            if not path.exists():
                ok = False
                lines.append(f"FAIL {label} {rel_file}")
                lines.append(f"  missing={path}")
                continue

            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                ok = False
                lines.append(f"FAIL {label} {rel_file}")
                lines.append("  file is not UTF-8 text")
                continue

            hits = [needle for needle in forbidden if needle in text]
            conflict_ok = not hits
            ok = ok and conflict_ok
            lines.append(f"{format_result(conflict_ok)} {label} {rel_file}")
            if hits:
                for hit in hits:
                    lines.append(f"  forbidden_reference={hit}")

    return ok, lines


def verify_stage(root: Path, state: dict[str, Any], stage_num: int) -> tuple[bool, list[str]]:
    entry = state["stages"].get(stage_key(stage_num))
    if entry is None:
        return False, [f"Missing stage entry: {stage_key(stage_num)}"]

    spec = entry.get("verification")
    if not spec:
        return False, [f"No verification spec for stage {stage_num}"]

    verify_type = spec.get("type")
    if verify_type == "file_exists":
        return verify_file_exists(root, spec)
    if verify_type == "files_nonempty":
        return verify_files_nonempty(root, spec)
    if verify_type == "janitor":
        return verify_janitor(root, spec)

    return False, [f"Unsupported verification type: {verify_type}"]


def blocked_message(
    root: Path,
    state: dict[str, Any],
    command: str,
    required_stage: int,
    matched_patterns: list[str],
) -> str:
    current_stage = int(state["current_stage"])
    current_name = state.get("stage_name", STAGE_NAMES.get(current_stage, "unknown"))
    required_name = STAGE_NAMES.get(required_stage, "unknown")
    check_cmd = "python3 scripts/pipeline_guard.py --check"
    advance_cmd = "python3 scripts/pipeline_guard.py --advance"
    state_file = format_path(state_path(root), root)

    matched = ", ".join(matched_patterns)
    return "\n".join(
        [
            "PIPELINE GATE BLOCKED: Cannot run command at the current stage.",
            "",
            f"Current stage: {current_stage} ({current_name})",
            f"Required stage: {required_stage} ({required_name})",
            f"Matched rule(s): {matched}",
            f"Command: {command}",
            "",
            f"To check stage: {check_cmd}",
            f"To advance:     {advance_cmd}",
            "",
            f"Read {state_file} to see the stage verification requirements.",
        ]
    )


def evaluate_command(root: Path, state: dict[str, Any], command: str) -> tuple[bool, str]:
    current_stage = int(state["current_stage"])
    blocked_map = state.get("blocked_tools_until_stage", {})

    for required_stage in sorted(int(key) for key in blocked_map.keys()):
        if current_stage >= required_stage:
            continue

        patterns = blocked_map.get(str(required_stage), [])
        matches = [pattern for pattern in patterns if command_matches(command, pattern)]
        if matches:
            return False, blocked_message(root, state, command, required_stage, matches)

    return True, ""


def print_status(root: Path, state: dict[str, Any]) -> None:
    current = int(state["current_stage"])
    print(f"Repo root: {root}")
    print(f"Campaign: {state.get('campaign_id', '?')}")
    print(f"Current stage: {current} ({STAGE_NAMES.get(current, '?')})")
    print()

    for stage_num in sorted(STAGE_NAMES):
        key = stage_key(stage_num)
        entry = state["stages"].get(key, {})
        status = entry.get("status", "unknown")
        marker = " <-- YOU ARE HERE" if stage_num == current else ""
        artifact = entry.get("artifact")
        verified_by = entry.get("verified_by")
        line = f"  {key}: {status}"
        if entry.get("completed_at"):
            line += f" (completed {entry['completed_at']})"
        elif entry.get("started_at"):
            line += f" (started {entry['started_at']})"
        if verified_by:
            line += f" [verified_by: {verified_by}]"
        if artifact:
            artifact_path = resolve_repo_path(root, artifact)
            line += f" [artifact: {'OK' if artifact_path.exists() else 'MISSING'}]"
        line += marker
        print(line)

        ok, details = verify_stage(root, state, stage_num)
        print(f"    verification: {format_result(ok)}")
        for detail in details:
            print(f"      {detail}")
        print()


def advance_stage(root: Path) -> int:
    state = load_state(root)
    current = int(state["current_stage"])

    print_status(root, state)
    if current >= max(STAGE_NAMES):
        print("Already at final stage (journalist). Nothing to advance.")
        return 0

    ok, details = verify_stage(root, state, current)
    if not ok:
        print(f"CANNOT ADVANCE: Stage {current} ({STAGE_NAMES[current]}) verification failed.")
        for detail in details:
            print(f"  {detail}")
        return 1

    current_key = stage_key(current)
    next_stage = current + 1
    next_key = stage_key(next_stage)

    state["stages"][current_key]["status"] = "complete"
    state["stages"][current_key]["completed_at"] = today()
    state["stages"][current_key]["verified_by"] = "pipeline_guard"

    state["stages"][next_key]["status"] = "in_progress"
    state["stages"][next_key]["started_at"] = today()

    state["current_stage"] = next_stage
    state["stage_name"] = STAGE_NAMES[next_stage]

    save_state(root, state)
    print(f"Advanced: {current} ({STAGE_NAMES[current]}) -> {next_stage} ({STAGE_NAMES[next_stage]})")
    return 0


def force_stage(root: Path, new_stage: int) -> int:
    if new_stage not in STAGE_NAMES:
        print(f"ERROR: invalid stage {new_stage}. Choose 0-{max(STAGE_NAMES)}.")
        return 1

    state = load_state(root)
    for stage_num in sorted(STAGE_NAMES):
        key = stage_key(stage_num)
        entry = state["stages"][key]
        if stage_num < new_stage:
            entry["status"] = "complete"
            entry.setdefault("completed_at", today())
        elif stage_num == new_stage:
            entry["status"] = "in_progress"
            entry["started_at"] = today()
            entry.pop("completed_at", None)
        else:
            entry["status"] = "not_started"
            entry.pop("started_at", None)
            entry.pop("completed_at", None)
            if entry.get("verified_by") == "pipeline_guard":
                entry["verified_by"] = None

    state["current_stage"] = new_stage
    state["stage_name"] = STAGE_NAMES[new_stage]
    save_state(root, state)
    print(f"FORCED to stage {new_stage} ({STAGE_NAMES[new_stage]})")
    return 0


def extract_hook_command(stdin_text: str) -> str:
    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError:
        return ""

    tool_input = payload.get("tool_input", payload)
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def run_hook_mode(root: Path) -> int:
    if not state_path(root).exists():
        return 0

    stdin_text = sys.stdin.read()
    command = extract_hook_command(stdin_text)
    if not command:
        return 0

    state = load_state(root)
    allowed, message = evaluate_command(root, state, command)
    if allowed:
        return 0

    print(message)
    return BLOCK_EXIT_CODE


def run_cli_gate(root: Path, command_tokens: list[str]) -> int:
    if not command_tokens:
        print("ERROR: no command provided.")
        return 1

    state = load_state(root)
    command = " ".join(command_tokens)
    allowed, message = evaluate_command(root, state, command)
    if allowed:
        print(f"ALLOW: {command}")
        return 0

    print(message)
    return BLOCK_EXIT_CODE


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Unified pipeline guard")
    parser.add_argument("--hook", action="store_true", help="Read Claude hook payload from stdin")
    parser.add_argument("--check", action="store_true", help="Print pipeline status")
    parser.add_argument("--advance", action="store_true", help="Advance to the next stage after verification")
    parser.add_argument("--force", type=int, help="Force the current stage to N")
    return parser.parse_known_args(argv)


def main(argv: list[str] | None = None) -> int:
    root = repo_root()
    args, extras = parse_args(argv or sys.argv[1:])

    try:
        if args.hook:
            return run_hook_mode(root)
        if args.check:
            print_status(root, load_state(root))
            return 0
        if args.advance:
            return advance_stage(root)
        if args.force is not None:
            return force_stage(root, args.force)
        if extras:
            return run_cli_gate(root, extras)

        print("Usage:")
        print("  python3 scripts/pipeline_guard.py --hook")
        print("  python3 scripts/pipeline_guard.py --check")
        print("  python3 scripts/pipeline_guard.py --advance")
        print("  python3 scripts/pipeline_guard.py --force N")
        print("  python3 scripts/pipeline_guard.py <command ...>")
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
