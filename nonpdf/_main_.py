from __future__ import annotations

import sys

import click

# Ensure payload modules are imported so the registry is populated.
from nonpdf import __brand__, __version__  # noqa: F401
from nonpdf.core.generator import Generator
from nonpdf.core.registry import registry
from nonpdf.tui.app import NonPDFApp
from nonpdf.util.log import configure_logging


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name=__brand__.lower())
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """NonPDF — PDF pentesting framework by Anonymous-beta (chinedu)."""
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
    for entry in registry.all():
        click.echo(
            f"[{entry.id:>4}] {entry.name:<32} "
            f"{(entry.cve or '-'):<16} {entry.platform}"
        )


@cli.command("generate")
@click.argument("callback")
@click.option("--output", "-o", default="output", help="Output directory.")
@click.option("--profile", "-p", default="full",
              help="Payload profile (full, quick, web, pdfjs, acrobat, server, unc, xxe, js).")
@click.option("--obfuscate", "-O", type=click.IntRange(0, 4), default=0,
              help="Obfuscation level (0-4).")
@click.option("--only", "-n", multiple=True,
              help="Only build these payload IDs (repeatable).")
def cmd_generate(callback: str, output: str, profile: str,
                 obfuscate: int, only: tuple[str, ...]) -> None:
    """Generate payloads pointing at CALLBACK."""
    gen = Generator(callback=callback, output_dir=output,
                    profile=profile, obfuscate=obfuscate)
    results = gen.run(only=list(only) or None)
    for r in results:
        click.echo(f"  [+] {r.path.name:<32} {r.description}")


@cli.command("listen")
@click.option("--port", "-P", default=8080, type=int, help="Bind port.")
def cmd_listen(port: int) -> None:
    """Run a headless HTTP callback listener."""
    import time

    from nonpdf.net.callback import CallbackServer

    def on_hit(hit) -> None:
        click.echo(
            f"{hit.timestamp}  {hit.method:<4}  {hit.client_ip:<15}  "
            f"{hit.path}  ({hit.payload_id()})"
        )

    srv = CallbackServer(port=port, on_hit=on_hit)
    srv.start()
    click.echo(f"[+] NonPDF listener up on 0.0.0.0:{port}  (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\n[!] stopping…")
    finally:
        srv.stop()


def main() -> None:
    try:
        cli()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()