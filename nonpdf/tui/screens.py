"""Every NonPDF screen.

Screens:
  DashboardScreen  — banner + quick stats + nav
  GenerateScreen   — callback, profile, obfuscation, run, live log, correlator
  PayloadsScreen   — full registry browser with filters
  ListenerScreen   — HTTP + DNS listeners, live hit feed, click-through
  AboutScreen      — Anonymous-beta (chinedu) branding
"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Footer, Header, Input, Label,
    RichLog, Select, Slider, Static,
)

from nonpdf import __brand__, __creator__, __version__
from nonpdf.core.generator import PROFILES
from nonpdf.core.registry import registry
from nonpdf.net.session import Session, SessionHit
from nonpdf.tui.widgets import Banner, StatusBar


# ──────────────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────────────

class DashboardScreen(Screen):
    BINDINGS = [
        Binding("g", "goto('generate')", "Generate"),
        Binding("p", "goto('payloads')", "Payloads"),
        Binding("l", "goto('listener')", "Listener"),
        Binding("a", "goto('about')", "About"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="dash-wrap"):
            yield Banner(id="banner")
            with Horizontal(id="dash-cards"):
                yield Static(self._stat_payloads(), id="card-payloads", classes="card")
                yield Static(self._stat_profiles(), id="card-profiles", classes="card")
                yield Static(self._stat_builds(), id="card-builds", classes="card")
                yield Static(self._stat_hits(), id="card-hits", classes="card")
            with Vertical(id="dash-nav"):
                yield Label("Navigation", classes="section-title")
                with Horizontal(classes="nav-row"):
                    yield Button("Generate  [g]", id="nav-generate", variant="primary")
                    yield Button("Payloads  [p]", id="nav-payloads", variant="default")
                    yield Button("Listener  [l]", id="nav-listener", variant="success")
                    yield Button("About     [a]", id="nav-about", variant="default")
            yield Static(id="dash-recent", classes="panel")
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        s = self.app.state
        self.query_one("#card-payloads", Static).update(self._stat_payloads())
        self.query_one("#card-profiles", Static).update(self._stat_profiles())
        self.query_one("#card-builds", Static).update(self._stat_builds())
        self.query_one("#card-hits", Static).update(self._stat_hits())
        self.query_one("#dash-recent", Static).update(self._recent_block())
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

    def _stat_payloads(self) -> str:
        total = len(registry.all())
        return f"[b cyan]PAYLOADS[/]\n\n[bold white]{total}[/]  registered"

    def _stat_profiles(self) -> str:
        return f"[b cyan]PROFILES[/]\n\n[bold white]{len(PROFILES)}[/]  available"

    def _stat_builds(self) -> str:
        n = len(self.app.state.recent_builds)
        return f"[b cyan]BUILDS[/]\n\n[bold white]{n}[/]  this session"

    def _stat_hits(self) -> str:
        n = len(self.app.state.hits)
        return f"[b cyan]HITS[/]\n\n[bold white]{n}[/]  callbacks"

    def _recent_block(self) -> str:
        s = self.app.state
        lines = ["[b cyan]Recent activity[/]"]
        if s.recent_builds:
            lines.append("[b]last builds[/]")
            for path, desc, pid, _cid in s.recent_builds[:6]:
                lines.append(f"  [green]·[/] [b]{pid}[/] {Path(path).name}  [dim]{desc}[/]")
        if s.hits:
            lines.append("")
            lines.append("[b]last callbacks[/]")
            for ts, source, method, ip, path, _cid in s.hits[:6]:
                tag = "[magenta]dns [/]" if source == "dns" else "[cyan]http[/]"
                lines.append(f"  {tag}  {ts}  {method:<4}  {ip:<15}  {path}")
        if len(lines) == 1:
            lines.append("[dim]no activity yet — run a generation or start the listener[/]")
        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "nav-generate":
            self.app.switch_screen("generate")
        elif bid == "nav-payloads":
            self.app.switch_screen("payloads")
        elif bid == "nav-listener":
            self.app.switch_screen("listener")
        elif bid == "nav-about":
            self.app.switch_screen("about")

    def action_goto(self, name: str) -> None:
        self.app.switch_screen(name)


# ──────────────────────────────────────────────────────────────────────
# Generate
# ──────────────────────────────────────────────────────────────────────

class GenerateScreen(Screen):
    BINDINGS = [
        Binding("escape", "goto('dashboard')", "Back"),
        Binding("ctrl+r", "run_generation", "Run"),
    ]

    def compose(self) -> ComposeResult:
        s = self.app.state
        yield Header(show_clock=True)
        with Container(id="gen-wrap"):
            yield Label("[b cyan]GENERATE PAYLOADS[/]", classes="section-title")
            with Horizontal(id="gen-form"):
                with Vertical(classes="form-col"):
                    yield Label("Callback URL / domain", classes="field-label")
                    yield Input(
                        value=s.callback,
                        placeholder="collab.example.com  or  https://collab.example.com",
                        id="inp-callback",
                    )
                    yield Label("Output directory", classes="field-label")
                    yield Input(value=s.output_dir, id="inp-output")
                    yield Label("Profile", classes="field-label")
                    yield Select(
                        [(k, k) for k in PROFILES.keys()],
                        value=s.profile,
                        id="sel-profile",
                        allow_blank=False,
                    )
                with Vertical(classes="form-col"):
                    yield Label("Obfuscation level", classes="field-label")
                    yield Static(id="lbl-obf")
                    yield Slider(min=0, max=4, step=1, value=s.obfuscate,
                                 id="sld-obf")
                    yield Label("Only build IDs (comma-separated, blank = profile)",
                                classes="field-label")
                    yield Input(placeholder="A01,J04,U01", id="inp-only")
                    with Horizontal(id="gen-actions"):
                        yield Button("Run", id="btn-run", variant="success")
                        yield Button("Back", id="btn-back", variant="default")
            yield RichLog(id="gen-log", highlight=True, markup=True)
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._sync_label()
        self._refresh_status()
        self.query_one("#gen-log", RichLog).write(
            "[dim]ready. set a callback and hit Run (or Ctrl+R).[/]"
        )

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

    def _refresh_status(self) -> None:
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def _sync_label(self) -> None:
        v = int(self.query_one("#sld-obf", Slider).value)
        names = {
            0: "0 · none",
            1: "1 · name/string encoding",
            2: "2 · + JS / URI obfuscation",
            3: "3 · + FlateDecode streams",
            4: "4 · + JS staging (base64 / charcode)",
        }
        self.query_one("#lbl-obf", Static).update(
            f"[bold white]{names.get(v, str(v))}[/]"
        )

    def on_slider_changed(self, event: Slider.Changed) -> None:
        self.app.state.obfuscate = int(event.value)
        self._sync_label()
        self._refresh_status()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "sel-profile":
            self.app.state.profile = str(event.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        s = self.app.state
        if event.input.id == "inp-callback":
            s.callback = event.value
        elif event.input.id == "inp-output":
            s.output_dir = event.value or "output"
        self._refresh_status()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            self.action_run_generation()
        elif event.button.id == "btn-back":
            self.app.switch_screen("dashboard")

    def action_goto(self, name: str) -> None:
        self.app.switch_screen(name)

    def action_run_generation(self) -> None:
        callback = self.query_one("#inp-callback", Input).value.strip()
        output = self.query_one("#inp-output", Input).value.strip() or "output"
        profile = self.query_one("#sel-profile", Select).value
        obf = int(self.query_one("#sld-obf", Slider).value)
        only_raw = self.query_one("#inp-only", Input).value.strip()
        only = [x.strip() for x in only_raw.split(",") if x.strip()] or None

        log = self.query_one("#gen-log", RichLog)
        if not callback:
            log.write("[bold red]error:[/] callback URL/domain is required.")
            return

        s = self.app.state
        s.callback = callback
        s.output_dir = output
        s.profile = str(profile)
        s.obfuscate = obf

        log.write(f"[cyan]▸[/] profile=[b]{profile}[/]  obfuscate=L{obf}"
                  f"  output=[b]{output}[/]")
        log.write(f"[cyan]▸[/] callback=[b]{callback}[/]")
        self.run_worker(
            self._do_generation(callback, output, str(profile), obf, only),
            thread=True, exclusive=True, name="generate",
        )

    def _do_generation(self, callback: str, output: str,
                       profile: str, obf: int, only: list[str] | None):
        app = self.app

        def emit(msg: str) -> None:
            app.call_from_thread(self.query_one("#gen-log", RichLog).write, msg)

        def refresh() -> None:
            app.call_from_thread(self._refresh_status)

        try:
            session = app.session
            entries = (
                registry.filter(ids=only) if only
                else _select_for_profile(profile)
            )
            emit(f"[dim]selected {len(entries)} payloads[/]")
            built = 0
            for entry in entries:
                try:
                    corr = session.mint_for(entry.id, entry.name)
                    data = entry.builder(host=corr.callback_url)
                    data = _brand_artifact(data)
                    path = Path(output) / f"{entry.id}_{entry.name}_{corr.corr_id}.pdf"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                    if obf:
                        from nonpdf.core.obfuscator import obfuscate_pdf
                        obfuscate_pdf(path, obf)

                    session.record_build(
                        payload_id=entry.id, payload_name=entry.name,
                        corr_id=corr.corr_id, callback_url=corr.callback_url,
                        domain=corr.domain, path=str(path),
                        description=entry.description, obfuscate=obf,
                    )
                    app.state.add_build(str(path), entry.description,
                                        entry.id, corr.corr_id)
                    emit(
                        f"[green]✔[/] {path.name}\n"
                        f"    [dim]corr[/] {corr.corr_id}  "
                        f"[dim]url[/] {corr.callback_url}"
                    )
                    built += 1
                except Exception as exc:  # noqa: BLE001
                    emit(f"[red]✘[/] {entry.id} {entry.name}: {exc}")
            emit(f"[bold green]done.[/] {built} file(s) → {output}/")
        except Exception as exc:  # noqa: BLE001
            emit(f"[bold red]generation failed:[/] {exc}")
        finally:
            refresh()


def _select_for_profile(profile: str):
    from nonpdf.core.generator import PROFILES as P
    spec = P.get(profile, P["full"])
    if spec.get("ids") == ["*"]:
        return registry.all()
    return registry.filter(
        platform=spec.get("platform"),
        tags=spec.get("tags"),
    )


def _brand_artifact(data: bytes) -> bytes:
    """Apply Anonymous-beta (chinedu) metadata signature."""
    from nonpdf.core.branding import INFO_DICT, PDF_HEADER_COMMENT
    from nonpdf.core.generator import Generator
    nl = data.find(b'\n')
    if nl != -1 and data.startswith(b'%PDF'):
        data = data[:nl + 1] + PDF_HEADER_COMMENT + data[nl + 1:]
    tidx = data.rfind(b'trailer')
    if tidx != -1:
        section = data[tidx:]
        if b'/Info' not in section:
            last = section.rfind(b'>>')
            if last != -1:
                pos = tidx + last
                data = data[:pos] + INFO_DICT + b'\n' + data[pos:]
    return Generator._append_footer(data)


# ──────────────────────────────────────────────────────────────────────
# Payloads
# ──────────────────────────────────────────────────────────────────────

class PayloadsScreen(Screen):
    BINDINGS = [
        Binding("escape", "goto('dashboard')", "Back"),
        Binding("ctrl+r", "reload", "Reload"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="pay-wrap"):
            yield Label("[b cyan]PAYLOAD REGISTRY[/]", classes="section-title")
            with Horizontal(id="pay-filter"):
                yield Label("Platform:", classes="filter-label")
                yield Select(
                    [("all", "all"), ("acrobat", "acrobat"),
                     ("pdfium", "pdfium"), ("pdfjs", "pdfjs"),
                     ("server", "server")],
                    value="all", id="sel-platform", allow_blank=False,
                )
                yield Label("Tag:", classes="filter-label")
                yield Input(placeholder="quick / unc / xxe / javascript / xfa / browser …",
                            id="inp-tag")
                yield Button("Apply", id="btn-apply", variant="primary")
            yield DataTable(id="payload-table", zebra_stripes=True,
                            cursor_type="row", fixed_columns=1)
            yield Static(id="pay-detail", classes="panel")
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._reload()
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

    def _reload(self) -> None:
        platform = self.query_one("#sel-platform", Select).value
        tag = self.query_one("#inp-tag", Input).value.strip() or None
        plat = None if platform == "all" else str(platform)
        tbl = self.query_one("#payload-table", DataTable)
        tbl.clear(columns=True)
        tbl.add_columns("ID", "Name", "Platform", "CVE", "Tags", "Description")
        entries = registry.filter(platform=plat, tags={tag} if tag else None)
        for entry in entries:
            tbl.add_row(
                entry.id, entry.name, entry.platform,
                entry.cve or "—", ",".join(entry.tags) or "—",
                entry.description, key=entry.id,
            )
        self.query_one("#pay-detail", Static).update(
            f"[dim]{len(entries)} payload(s) shown[/]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply":
            self._reload()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        pid = event.row_key.value if event.row_key else None
        if not pid:
            return
        try:
            entry = registry.get(str(pid))
        except KeyError:
            return
        self.query_one("#pay-detail", Static).update(
            f"[b cyan]{entry.id}[/] [b]{entry.name}[/]\n"
            f"[dim]platform:[/] {entry.platform}    "
            f"[dim]cve:[/] {entry.cve or '—'}    "
            f"[dim]tags:[/] {','.join(entry.tags) or '—'}\n"
            f"{entry.description}"
        )

    def action_goto(self, name: str) -> None:
        self.app.switch_screen(name)

    def action_reload(self) -> None:
        self._reload()


# ──────────────────────────────────────────────────────────────────────
# Listener
# ──────────────────────────────────────────────────────────────────────

class ListenerScreen(Screen):
    BINDINGS = [
        Binding("escape", "goto('dashboard')", "Back"),
        Binding("ctrl+s", "toggle_http", "HTTP start/stop"),
        Binding("ctrl+d", "toggle_dns", "DNS start/stop"),
        Binding("ctrl+l", "clear_log", "Clear log"),
        Binding("ctrl+e", "export", "Export"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="lis-wrap"):
            yield Label("[b cyan]CALLBACK LISTENERS[/]", classes="section-title")
            with Horizontal(id="lis-form"):
                yield Label("HTTP:", classes="filter-label")
                yield Input(value="8080", id="inp-http-port")
                yield Button("HTTP ▶", id="btn-http-start", variant="success")
                yield Button("HTTP ■", id="btn-http-stop", variant="error")
                yield Label("DNS:", classes="filter-label")
                yield Input(value="53", id="inp-dns-port")
                yield Input(value="127.0.0.1", id="inp-dns-answer")
                yield Button("DNS ▶", id="btn-dns-start", variant="success")
                yield Button("DNS ■", id="btn-dns-stop", variant="error")
            with Horizontal(id="lis-status-row"):
                yield Static("[dim]HTTP idle[/]", id="lis-http-status")
                yield Static("[dim]DNS idle[/]", id="lis-dns-status")
                yield Static("[dim]engagement: —[/]", id="lis-eng-status")
                yield Button("Export bundle", id="btn-export", variant="primary")
            yield RichLog(id="lis-log", highlight=True, markup=True)
            yield Static(id="lis-hit-detail", classes="panel")
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._log_line("[dim]listeners idle. Ctrl+S → HTTP, Ctrl+D → DNS.[/]")
        self._refresh_status()
        self._refresh_eng_status()

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

    def _refresh_status(self) -> None:
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def _refresh_eng_status(self) -> None:
        sess = self.app.session
        self.query_one("#lis-eng-status", Static).update(
            f"[dim]engagement:[/] [b]{sess.name}[/]  "
            f"[dim]callback:[/] [b]{sess.callback or '—'}[/]"
        )

    def _log_line(self, line: str) -> None:
        self.query_one("#lis-log", RichLog).write(line)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-http-start":
            self._start_http()
        elif bid == "btn-http-stop":
            self._stop_http()
        elif bid == "btn-dns-start":
            self._start_dns()
        elif bid == "btn-dns-stop":
            self._stop_dns()
        elif bid == "btn-export":
            self.action_export()

    def action_toggle_http(self) -> None:
        if self.app.session.http and self.app.session.http.running:
            self._stop_http()
        else:
            self._start_http()

    def action_toggle_dns(self) -> None:
        if self.app.session.dns and self.app.session.dns.running:
            self._stop_dns()
        else:
            self._start_dns()

    def action_clear_log(self) -> None:
        self.query_one("#lis-log", RichLog).clear()

    def action_export(self) -> None:
        from nonpdf.net.store import export_engagement
        out = Path(self.app.state.output_dir) / "bundle" / f"{self.app.session.name}.json"
        try:
            export_engagement(self.app.session.store, out)
            self._log_line(f"[bold green]▸ exported[/] {out}")
        except Exception as exc:  # noqa: BLE001
            self._log_line(f"[red]export failed:[/] {exc}")

    def _start_http(self) -> None:
        try:
            port = int(self.query_one("#inp-http-port", Input).value.strip() or "8080")
        except ValueError:
            self._log_line("[red]invalid HTTP port.[/]")
            return
        try:
            used = self.app.session.start_http(port=port)
            self.query_one("#lis-http-status", Static).update(
                f"[green]HTTP listening on 0.0.0.0:{used}[/]"
            )
            self._log_line(f"[bold green]▸ HTTP[/] 0.0.0.0:{used}")
        except Exception as exc:  # noqa: BLE001
            self._log_line(f"[bold red]HTTP bind failed:[/] {exc}")

    def _stop_http(self) -> None:
        if self.app.session.http and self.app.session.http.running:
            self.app.session.stop_http()
            self.query_one("#lis-http-status", Static).update("[dim]HTTP idle[/]")
            self._log_line("[yellow]■ HTTP stopped.[/]")
        else:
            self._log_line("[yellow]HTTP not running.[/]")

    def _start_dns(self) -> None:
        try:
            port = int(self.query_one("#inp-dns-port", Input).value.strip() or "53")
        except ValueError:
            self._log_line("[red]invalid DNS port.[/]")
            return
        answer_ip = self.query_one("#inp-dns-answer", Input).value.strip() or "127.0.0.1"
        try:
            used = self.app.session.start_dns(port=port, answer_ip=answer_ip)
            self.query_one("#lis-dns-status", Static).update(
                f"[green]DNS listening on 0.0.0.0:{used} → {answer_ip}[/]"
            )
            self._log_line(
                f"[bold green]▸ DNS[/] 0.0.0.0:{used}  (answer A → {answer_ip})"
            )
            self._log_line(
                "[dim]note: port 53 usually requires root. use a higher port + "
                "iptables redirect, or run with sudo.[/]"
            )
        except PermissionError:
            self._log_line(
                "[bold red]DNS bind failed:[/] permission denied on port 53. "
                "try sudo, or use a high port with a redirect."
            )
        except Exception as exc:  # noqa: BLE001
            self._log_line(f"[bold red]DNS bind failed:[/] {exc}")

    def _stop_dns(self) -> None:
        if self.app.session.dns and self.app.session.dns.running:
            self.app.session.stop_dns()
            self.query_one("#lis-dns-status", Static).update("[dim]DNS idle[/]")
            self._log_line("[yellow]■ DNS stopped.[/]")
        else:
            self._log_line("[yellow]DNS not running.[/]")

    # called from Session via app-level callback
    def render_hit(self, hit: SessionHit) -> None:
        tag = "[magenta]dns [/]" if hit.source == "dns" else "[cyan]http[/]"
        corr_tag = (
            f"  [b green]{hit.payload_id}[/]:[dim]{hit.payload_name}[/]"
            if hit.payload_id else "  [dim](unmatched)[/]"
        )
        self._log_line(
            f"{tag}  [b]{hit.ts}[/]  {hit.method:<4}  "
            f"[b]{hit.client:<15}[/]  {hit.path}{corr_tag}"
        )
        self.query_one("#lis-hit-detail", Static).update(
            f"[b cyan]{hit.source.upper()}[/]  {hit.method}  {hit.client}\n"
            f"[dim]path:[/]  {hit.path}\n"
            f"[dim]corr:[/]  {hit.corr_id or '—'}\n"
            f"[dim]payload:[/]  [b]{hit.payload_id or '—'}[/] "
            f"{hit.payload_name}\n"
            f"[dim]desc:[/]  {hit.description or '—'}"
        )
        self._refresh_status()

    def action_goto(self, name: str) -> None:
        self.app.switch_screen(name)


# ──────────────────────────────────────────────────────────────────────
# About
# ──────────────────────────────────────────────────────────────────────

class AboutScreen(Screen):
    BINDINGS = [Binding("escape", "goto('dashboard')", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="about-wrap"):
            yield Banner()
            yield Static(self._body(), id="about-body", classes="panel")
            yield Static(id="about-counts", classes="panel")
            with Horizontal(id="about-actions"):
                yield Button("Back", id="btn-back", variant="primary")
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        total = len(registry.all())
        by_plat: dict[str, int] = {}
        for e in registry.all():
            by_plat[e.platform] = by_plat.get(e.platform, 0) + 1
        lines = [f"[b cyan]registry[/]  {total} payloads total"]
        for k in sorted(by_plat):
            lines.append(f"  [dim]·[/] {k:<10} {by_plat[k]}")
        lines.append("")
        lines.append(f"[b cyan]engagement[/]  {self.app.session.name}")
        lines.append(f"  [dim]·[/] callback  {self.app.session.callback or '—'}")
        self.query_one("#about-counts", Static).update("\n".join(lines))
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

    def _body(self) -> str:
        return (
            f"[b white]{__brand__}[/]  v{__version__}\n\n"
            f"[b cyan]Creator:[/]  {__creator__}\n"
            f"[b cyan]Maintainer:[/]  Anonymous-beta\n\n"
            "NonPDF is a callback-driven PDF payload generation and "
            "listening framework. Each build mints a unique correlation "
            "ID, so every HTTP or DNS callback maps back to the exact "
            "payload that fired it.\n\n"
            f"[dim]Engagements persist to ~/.nonpdf/engagements/[/]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.switch_screen("dashboard")

    def action_goto(self, name: str) -> None:
        self.app.switch_screen(name)