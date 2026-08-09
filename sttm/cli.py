"""Command-line entry point for deterministic STTM compilation and codegen."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from sttm import __version__
from sttm.application.services import STTMGenerationService
from sttm.config import get_settings
from sttm.domain.ir import LogicalMappingIR
from sttm.infrastructure.codegen import DeterministicCodeGeneratorAgent
from sttm.infrastructure.compiler import STTMCompiler


def _read_ir(path: Path) -> LogicalMappingIR:
    """Load and validate a Logical Mapping IR JSON document."""
    return LogicalMappingIR.model_validate_json(path.read_text(encoding="utf-8"))


def _write(path: Path, content: str) -> None:
    """Write a requested artifact without creating directories implicitly."""
    if not path.parent.exists():
        raise ValueError(f"Output directory does not exist: {path.parent}")
    path.write_text(content, encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="STTM AI Platform")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="Validate local application configuration")
    check.set_defaults(handler=_run_check)

    compile_command = commands.add_parser("compile", help="Compile approved IR JSON to STTM JSON")
    compile_command.add_argument("ir", type=Path, help="Approved LogicalMappingIR JSON file")
    compile_command.add_argument("--output", required=True, type=Path, help="STTM JSON output path")
    compile_command.set_defaults(handler=_run_compile)

    generate = commands.add_parser("generate", help="Compile approved IR and generate SQL or dbt")
    generate.add_argument("ir", type=Path, help="Approved LogicalMappingIR JSON file")
    generate.add_argument(
        "--language",
        default="ansi_sql",
        choices=("ansi_sql", "sql", "spark_sql", "dbt"),
    )
    generate.add_argument("--output", required=True, type=Path, help="Generated code output path")
    generate.set_defaults(handler=_run_generate)
    return parser


def _run_check(_: argparse.Namespace) -> int:
    settings = get_settings()
    print(
        f"Configuration valid: env={settings.app_env}, "
        f"sttm_columns={settings.sttm_column_count}",
    )
    return 0


def _run_compile(args: argparse.Namespace) -> int:
    result = STTMGenerationService(compiler=STTMCompiler()).compile(_read_ir(args.ir))
    _write(args.output, result.sttm.model_dump_json(indent=2))
    print(f"Wrote {len(result.sttm.rows)} STTM row(s) to {args.output}")
    return 0


def _run_generate(args: argparse.Namespace) -> int:
    result = STTMGenerationService(
        compiler=STTMCompiler(),
        code_generator=DeterministicCodeGeneratorAgent(),
    ).generate_code(_read_ir(args.ir), args.language)
    assert result.generated_code is not None
    _write(args.output, result.generated_code.content)
    print(f"Wrote {result.generated_code.language} to {args.output}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the STTM command-line application."""
    args = _build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError) as error:
        print(f"Error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
