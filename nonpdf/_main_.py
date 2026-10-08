from __future__ import annotations

import sys

import click

from nonpdf import __brand__, __version__
from nonpdf.core.generator import Generator
from nonpdf.core.registry import Registry
from nonpdf.tui.app import NonPDFApp
from nonpdf.util.log import configure_logging


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name=__brand__.lower())
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """NonPDF — PDF pentesting framework by Anonymous-beta."""
    configure_logging(verbose)
    if ctx.invoked_subcommand is None:
        NonPDFApp().run()


@cli.command("tui")
def cmd_tui() -> None:
    """Launch the interactive cockpit."""
    NonPDFApp().run()


@cli.command("list")
def cmd_list() -> None:
    """List every registered payload."""
    reg = Registry()
    for entry in reg.all():
        click.echo(f"[{entry.id:>4}] {entry.name:<32} {entry.cve or '-':<16} {entry.platform}")


@cli.command("generate")
@click.argument("callback")
@click.option("--output", "-o", default="output", help="Output directory.")
@click.option("--profile", "-p", default="full", help="Payload profile (full, web, acrobat, server, quick).")
@click.option("--obfuscate", "-O", type=click.IntRange(0, 4), default=0, help="Obfuscation level (0-4).")
@click.option("--only", "-n", multiple=True, help="Only build these payload IDs (repeatable).")
def cmd_generate(callback: str, output: str, profile: str, obfuscate: int, only: tuple[str, ...]) -> None:
    """Generate payloads pointing at CALLBACK."""
    gen = Generator(callback=callback, output_dir=output, profile=profile, obfuscate=obfuscate)
    results = gen.run(only=list(only) or None)
    for r in results:
        click.echo(f"  [+] {r.path.name:<32} {r.description}")


def main() -> None:
    try:
        cli()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
