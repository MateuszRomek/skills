#!/usr/bin/env python3
"""Single-writer state for an orchestrate program: tasks.tsv in the program directory."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

COLUMNS = ["id", "title", "deps", "base", "level", "status", "attempts", "fixes", "max_fixes", "branch", "pr", "head", "verdict", "updated", "note"]
FINAL = {"merged"}
DEFAULTS = {"fixes": "0", "max_fixes": "1"}
LEVELS = {"light", "standard", "behavioral", "security"}
HAS_PR = {"verifying", "merging", "merged"}
TRANSITIONS = {
    "queued": {"building", "parked"},
    "building": {"verifying", "queued", "parked"},
    "verifying": {"merging", "building", "parked"},
    "merging": {"merged", "building", "parked"},
    "parked": {"queued"},
    "merged": set(),
}
EDITABLE = {"branch", "pr", "head", "verdict", "note", "title", "deps", "base", "level", "max_fixes"}


class ProgramError(Exception):
    pass


def tasks_path(program: Path) -> Path:
    return program / "tasks.tsv"


def parse_deps(value: str) -> list[str]:
    return [d.strip() for d in value.split(",") if d.strip()]


def load(program: Path) -> list[dict[str, str]]:
    path = tasks_path(program)
    if not path.exists():
        raise ProgramError(f"{path} does not exist; run init first")
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t") if lines else []
    missing = [c for c in COLUMNS if c not in header]
    if not header or set(missing) - set(DEFAULTS) or set(header) - set(COLUMNS):
        raise ProgramError(f"{path} header must be: {' '.join(COLUMNS)}")
    rows = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) != len(header):
            raise ProgramError(f"{path}:{number} has {len(cells)} cells, expected {len(header)}")
        rows.append({c: DEFAULTS[c] for c in missing} | dict(zip(header, cells)))
    return rows


def save(program: Path, rows: list[dict[str, str]]) -> None:
    validate(rows)
    body = "\t".join(COLUMNS) + "\n" + "".join("\t".join(r[c] for c in COLUMNS) + "\n" for r in rows)
    fd, tmp = tempfile.mkstemp(dir=program, prefix=".tasks-", suffix=".tsv")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(body)
    os.replace(tmp, tasks_path(program))


def validate(rows: list[dict[str, str]]) -> None:
    ids = [r["id"] for r in rows]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ProgramError(f"duplicate task ids: {', '.join(duplicates)}")
    known = set(ids)
    for row in rows:
        if row["status"] not in TRANSITIONS:
            raise ProgramError(f"task {row['id']} has unknown status {row['status']!r}")
        for cell in row.values():
            if "\t" in cell or "\n" in cell:
                raise ProgramError(f"task {row['id']} has a tab or newline in a cell")
        missing = [d for d in parse_deps(row["deps"]) if d not in known]
        if missing:
            raise ProgramError(f"task {row['id']} depends on unknown task(s): {', '.join(missing)}")
        if row["level"] not in LEVELS:
            raise ProgramError(f"task {row['id']} level must be one of {', '.join(sorted(LEVELS))}, got {row['level']!r}")
        if not row["max_fixes"].isdigit():
            raise ProgramError(f"task {row['id']} max_fixes must be a whole number, got {row['max_fixes']!r}")
        if row["base"] != "main" and row["base"] not in parse_deps(row["deps"]):
            raise ProgramError(f"task {row['id']} base must be main or one of its dependencies, got {row['base']!r}")
    graph = {r["id"]: parse_deps(r["deps"]) for r in rows}
    state: dict[str, str] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == "done":
            return
        if state.get(node) == "open":
            cycle = trail[trail.index(node):] + [node]
            raise ProgramError(f"dependency cycle: {' -> '.join(cycle)}")
        state[node] = "open"
        for dep in graph[node]:
            visit(dep, trail + [node])
        state[node] = "done"

    for node in graph:
        visit(node, [])


def by_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {r["id"]: r for r in rows}


def waiting_on(row: dict[str, str], rows: list[dict[str, str]]) -> list[str]:
    tasks = by_id(rows)
    blocked = []
    for dep in parse_deps(row["deps"]):
        status = tasks[dep]["status"]
        if status in FINAL or (dep == row["base"] and status in HAS_PR):
            continue
        blocked.append(dep)
    return blocked


def ready(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in rows if r["status"] == "queued" and not waiting_on(r, rows)]


def stackable(rows: list[dict[str, str]]) -> list[tuple[dict[str, str], str]]:
    tasks = by_id(rows)
    out = []
    for row in rows:
        if row["status"] != "queued" or row["base"] != "main":
            continue
        open_deps = [d for d in parse_deps(row["deps"]) if tasks[d]["status"] not in FINAL]
        if len(open_deps) == 1 and tasks[open_deps[0]]["status"] in HAS_PR:
            out.append((row, open_deps[0]))
    return out


def restack(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    tasks = by_id(rows)
    return [r for r in rows if r["base"] != "main" and r["status"] not in FINAL and tasks[r["base"]]["status"] in FINAL]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_init(program: Path, specs: list[str]) -> str:
    if tasks_path(program).exists():
        rows = load(program)
        validate(rows)
        return f"exists: {len(rows)} tasks in {tasks_path(program)}"
    program.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in specs:
        parts = spec.split("|")
        if len(parts) not in (2, 3):
            raise ProgramError(f"task spec {spec!r} must be id|title or id|title|dep,dep")
        rows.append({c: "" for c in COLUMNS} | {
            "id": parts[0].strip(),
            "title": parts[1].strip(),
            "deps": ",".join(parse_deps(parts[2])) if len(parts) == 3 else "",
            "base": "main",
            "level": "standard",
            "status": "queued",
            "attempts": "0",
            "fixes": "0",
            "max_fixes": "1",
            "updated": now(),
        })
    if not rows:
        raise ProgramError("init needs at least one task spec")
    save(program, rows)
    return f"created: {len(rows)} tasks in {tasks_path(program)}"


def cmd_set(program: Path, task_id: str, status: str | None, fields: list[str]) -> str:
    rows = load(program)
    row = next((r for r in rows if r["id"] == task_id), None)
    if row is None:
        raise ProgramError(f"unknown task {task_id}")
    for field in fields:
        key, sep, value = field.partition("=")
        if not sep or key not in EDITABLE:
            raise ProgramError(f"field {field!r} must be key=value with key in: {', '.join(sorted(EDITABLE))}")
        row[key] = value
    if status and status != row["status"]:
        if status not in TRANSITIONS.get(row["status"], set()):
            allowed = ", ".join(sorted(TRANSITIONS[row["status"]])) or "none"
            raise ProgramError(f"task {task_id}: {row['status']} -> {status} is not allowed (allowed: {allowed})")
        if status == "building":
            blocked = waiting_on(row, rows)
            if blocked:
                raise ProgramError(f"task {task_id} waits on dependencies without a merge or a stack base: {', '.join(blocked)}")
            row["attempts"] = str(int(row["attempts"] or "0") + 1)
            if row["status"] == "verifying":
                if int(row["fixes"]) >= int(row["max_fixes"]):
                    raise ProgramError(
                        f"task {task_id} spent its fix budget ({row['fixes']} of {row['max_fixes']}); "
                        "park it, move the findings to findings.md, or have the user raise max_fixes"
                    )
                row["fixes"] = str(int(row["fixes"]) + 1)
        if status == "merging":
            unmerged = [d for d in parse_deps(row["deps"]) if by_id(rows)[d]["status"] not in FINAL]
            if unmerged:
                raise ProgramError(f"task {task_id} cannot merge before its dependencies merge: {', '.join(unmerged)}")
        row["status"] = status
    row["updated"] = now()
    save(program, rows)
    return f"{task_id}: {row['status']} (attempts {row['attempts']})"


def cmd_ready(program: Path, limit: int | None) -> str:
    rows = load(program)
    validate(rows)
    building = sum(1 for r in rows if r["status"] == "building")
    candidates = ready(rows)
    free = None if limit is None else max(limit - building, 0)
    start = candidates if free is None else candidates[:free]
    lines = [f"building: {building}" + ("" if limit is None else f" of {limit}")]
    lines += [f"start: {r['id']}\t{r['title']}" for r in start]
    lines += [f"waiting-for-slot: {r['id']}\t{r['title']}" for r in candidates[len(start):]]
    lines += [f"can-stack: {r['id']} on {parent}\t{r['title']}" for r, parent in stackable(rows)]
    lines += [f"restack: {r['id']} onto main, {r['base']} merged\t{r['title']}" for r in restack(rows)]
    return "\n".join(lines)


def cmd_show(program: Path) -> str:
    rows = load(program)
    validate(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    lines = [summary]
    for r in rows:
        fixes = f"fixes {r['fixes']}/{r['max_fixes']}"
        extra = " ".join(x for x in (fixes, r["pr"], r["head"][:12], r["verdict"], r["note"]) if x)
        base = "" if r["base"] == "main" else f"\ton[{r['base']}]"
        lines.append(f"{r['id']}\t{r['status']}\t{r['level']}\tdeps[{r['deps']}]{base}\t{extra}")
    done = all(r["status"] in FINAL | {"parked"} for r in rows)
    lines.append("program: settled" if done else "program: open")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="create tasks.tsv; a no-op when it already exists")
    p.add_argument("program", type=Path)
    p.add_argument("tasks", nargs="*", help="id|title or id|title|dep,dep")
    p = sub.add_parser("set", help="move a task and update its fields")
    p.add_argument("program", type=Path)
    p.add_argument("task")
    p.add_argument("--status")
    p.add_argument("fields", nargs="*", help="key=value")
    p = sub.add_parser("ready", help="list queued tasks whose dependencies are merged")
    p.add_argument("program", type=Path)
    p.add_argument("--limit", type=int, help="concurrent worker limit from the profile")
    p = sub.add_parser("show", help="print every task and whether the program is settled")
    p.add_argument("program", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            out = cmd_init(args.program, args.tasks)
        elif args.command == "set":
            out = cmd_set(args.program, args.task, args.status, args.fields)
        elif args.command == "ready":
            out = cmd_ready(args.program, args.limit)
        else:
            out = cmd_show(args.program)
    except ProgramError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
