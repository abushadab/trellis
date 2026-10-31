"""The ``trellis`` command line."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .paths import AGENT_NAMES


def _project(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trellis", description="Trellis: the Sunny, Iris and Ben agent workflow."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the stdio MCP server for one agent")
    serve.add_argument("--agent", required=True, choices=AGENT_NAMES)
    serve.add_argument("--project", required=True, type=_project, help="project directory (holds .trellis/)")

    render = sub.add_parser("render", help="render the templates into <project>/.trellis/agents/")
    render.add_argument("--project", type=_project, default=Path.cwd())
    render.add_argument("--check", action="store_true", help="report stale files without writing")
    render.add_argument(
        "--agent", action="append", choices=AGENT_NAMES, help="render only this agent (repeatable)"
    )
    render.add_argument("--templates", help="templates directory (default: <plugin root>/templates)")
    render.add_argument("--plugin-root", help="plugin root holding server/ and templates/")

    hook = sub.add_parser("hook", help="hook entry points")
    hook_sub = hook.add_subparsers(dest="hook_name", required=True)
    register = hook_sub.add_parser("register-subagent", help="PostToolUse hook on the Agent tool")
    register.add_argument("--agent", required=True, choices=AGENT_NAMES)
    register.add_argument("--project", required=True, type=_project)

    doctor = sub.add_parser("doctor", help="check tools, config and rendered files")
    doctor.add_argument("--project", type=_project, default=Path.cwd())
    doctor.add_argument("--templates")
    doctor.add_argument("--plugin-root")
    return parser


def _serve(args: argparse.Namespace) -> int:
    from .config import ConfigError
    from .server import serve
    from .settings import Settings

    try:
        settings = Settings.for_project(args.project)
    except ConfigError as exc:
        print(f"trellis serve: {exc}", file=sys.stderr)
        return 1
    serve(args.agent, settings)
    return 0


def _render(args: argparse.Namespace) -> int:
    from .render import RenderError, render_project

    try:
        report = render_project(
            args.project,
            plugin_root=args.plugin_root,
            templates_root=args.templates,
            agents=args.agent,
            check=args.check,
        )
    except RenderError as exc:
        print(f"trellis render: {exc}", file=sys.stderr)
        return 2
    for line in report.summaries:
        print(line)
    if args.check:
        for path in report.stale:
            print(f"STALE {path}")
        if report.stale:
            print("Run `trellis render` to regenerate.")
            return 1
        print(f"OK {len(report.unchanged)} file(s) up to date")
        return 0
    for path in report.written:
        print(f"Wrote {path}")
    for path in report.removed:
        print(f"Removed {path}")
    print(f"{len(report.written)} written, {len(report.unchanged)} unchanged, {len(report.removed)} removed")
    return 0


def _hook(args: argparse.Namespace) -> int:
    from .hook import run

    return run(args.agent, args.project)


def _doctor(args: argparse.Namespace) -> int:
    from .doctor import FAIL, run_doctor

    checks = run_doctor(args.project, plugin_root=args.plugin_root, templates=args.templates)
    for check in checks:
        print(check.line())
    failed = [c for c in checks if c.status == FAIL]
    print(f"{len(failed)} problem(s)" if failed else "All required checks passed")
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"serve": _serve, "render": _render, "hook": _hook, "doctor": _doctor}
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
