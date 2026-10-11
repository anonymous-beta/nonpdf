"""Every NonPDF screen.

Screens:
  DashboardScreen  — banner + quick stats + nav
  GenerateScreen   — callback, profile, obfuscation, run, live log
  PayloadsScreen   — full registry browser with filters
  ListenerScreen   — start/stop HTTP callback server + live hit feed
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
from nonpdf.core.generator import PROFILES, Generator
from nonpdf.core.registry import registry
from nonpdf.net.callback import CallbackServer, Hit
from nonpdf.tui.widgets import Banner, StatusBar, build_payload_table


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
            for path, desc in s.recent_builds[:6]:
                lines.append(f"  [green]·[/] {Path(path).name}  [dim]{desc}[/]")
        if s.hits:
            lines.append("")
            lines.append("[b]last callbacks[/]")
            for ts, method, ip, path in s.hits[:6]:
                lines.append(f"  [magenta]·[/] {ts}  {method:<4}  {ip:<15}  {path}")
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
                    yield Label("Callback URL / IP", classes="field-label")
                    yield Input(
                        value=s.callback,
                        placeholder="https://collab.example.com  or  10.0.0.5",
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
        self._status().update_status(
            callback=self.app.state.callback,
            profile=self.app.state.profile,
            obfuscate=self.app.state.obfuscate,
            hits=len(self.app.state.hits),
            builds=len(self.app.state.recent_builds),
        )
        self.query_one("#gen-log", RichLog).write(
            "[dim]ready. set a callback and hit Run (or Ctrl+R).[/]"
        )

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

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
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "sel-profile":
            self.app.state.profile = str(event.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        s = self.app.state
        if event.input.id == "inp-callback":
            s.callback = event.value
        elif event.input.id == "inp-output":
            s.output_dir = event.value or "output"
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

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
            log.write("[bold red]error:[/] callback URL is required.")
            return

        # persist to state
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
        def emit(msg: str) -> None:
            self.app.call_from_thread(self.query_one("#gen-log", RichLog).write, msg)

        def finish(results) -> None:
            self._refresh_status_only()

        try:
            gen = Generator(
                callback=callback, output_dir=output,
                profile=profile, obfuscate=obf,
            )
            entries = gen._select(only)
            emit(f"[dim]selected {len(entries)} payloads[/]")
            results = []
            for entry in entries:
                try:
                    data = entry.builder(host=callback)
                    data = gen._brand(data)
                    path = Path(output) / f"{entry.id}_{entry.name}.pdf"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                    if obf:
                        from nonpdf.core.obfuscator import obfuscate_pdf
                        obfuscate_pdf(path, obf)
                    self.app.state.add_build(str(path), entry.description)
                    emit(f"[green]✔[/] {path.name}  [dim]{entry.description}[/]")
                    results.append(path)
                except Exception as exc:  # noqa: BLE001
                    emit(f"[red]✘[/] {entry.id} {entry.name}: {exc}")
            emit(f"[bold green]done.[/] {len(results)} file(s) → {output}/")
        except Exception as exc:  # noqa: BLE001
            emit(f"[bold red]generation failed:[/] {exc}")
        finally:
            self.app.call_from_thread(self._refresh_status_only)

    def _refresh_status_only(self) -> None:
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )


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
        for entry in registry.filter(platform=plat, tags={tag} if tag else None):
            tbl.add_row(
                entry.id, entry.name, entry.platform,
                entry.cve or "—", ",".join(entry.tags) or "—",
                entry.description, key=entry.id,
            )
        self.query_one("#pay-detail", Static).update(
            f"[dim]{len(registry.filter(platform=plat, tags={tag} if tag else None))}"
            f" payload(s) shown[/]"
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
        Binding("ctrl+s", "toggle_listener", "Start/Stop"),
        Binding("ctrl+l", "clear_log", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="lis-wrap"):
            yield Label("[b cyan]CALLBACK LISTENER[/]", classes="section-title")
            with Horizontal(id="lis-form"):
                yield Label("Bind port:", classes="filter-label")
                yield Input(value="8080", id="inp-port")
                yield Button("Start", id="btn-listen-start", variant="success")
                yield Button("Stop", id="btn-listen-stop", variant="error")
                yield Static("[dim]idle[/]", id="lis-status")
            yield RichLog(id="lis-log", highlight=True, markup=True)
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._log_line("[dim]listener idle. press Start (Ctrl+S) to bind.[/]")
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

    def _status(self) -> StatusBar:
        return self.query_one("#status", StatusBar)

    def _log_line(self, line: str) -> None:
        self.query_one("#lis-log", RichLog).write(line)

    def _set_listener_status(self, text: str) -> None:
        self.query_one("#lis-status", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-listen-start":
            self._start_listener()
        elif bid == "btn-listen-stop":
            self._stop_listener()

    def action_toggle_listener(self) -> None:
        if self.app.callback_server and self.app.callback_server.running:
            self._stop_listener()
        else:
            self._start_listener()

    def action_clear_log(self) -> None:
        log = self.query_one("#lis-log", RichLog)
        log.clear()

    def _start_listener(self) -> None:
        if self.app.callback_server and self.app.callback_server.running:
            self._log_line("[yellow]already running.[/]")
            return
        try:
            port = int(self.query_one("#inp-port", Input).value.strip() or "8080")
        except ValueError:
            self._log_line("[red]invalid port.[/]")
            return

        def on_hit(hit: Hit) -> None:
            self.app.state.add_hit(hit.timestamp, hit.method,
                                   hit.client_ip, hit.path)
            self.app.call_from_thread(self._render_hit, hit)

        try:
            srv = CallbackServer(port=port, on_hit=on_hit)
            srv.start()
            self.app.callback_server = srv
            self._set_listener_status(f"[green]listening on 0.0.0.0:{port}[/]")
            self._log_line(f"[bold green]▸ listening[/] on 0.0.0.0:{port}")
        except Exception as exc:  # noqa: BLE001
            self._log_line(f"[bold red]bind failed:[/] {exc}")
            self.app.callback_server = None

    def _stop_listener(self) -> None:
        if not self.app.callback_server or not self.app.callback_server.running:
            self._log_line("[yellow]not running.[/]")
            return
        self.app.callback_server.stop()
        self.app.callback_server = None
        self._set_listener_status("[dim]idle[/]")
        self._log_line("[yellow]■ listener stopped.[/]")

    def _render_hit(self, hit: Hit) -> None:
        self._log_line(
            f"[magenta]{hit.timestamp}[/]  [cyan]{hit.method:<4}[/]  "
            f"[b]{hit.client_ip:<15}[/]  {hit.path}  "
            f"[dim]({hit.payload_id()})[/]"
        )
        s = self.app.state
        self._status().update_status(
            callback=s.callback, profile=s.profile,
            obfuscate=s.obfuscate, hits=len(s.hits),
            builds=len(s.recent_builds),
        )

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
            "listening framework. Every artifact produced carries the "
            "Anonymous-beta (chinedu) metadata signature: header comment, "
            "/Info dictionary, and a visible footer credit.\n\n"
            "[dim]Use only against systems you are authorized to test.[/]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.switch_screen("dashboard")

    def action_goto(self, name: str) -> None:
        self.app.switch_screen(name)