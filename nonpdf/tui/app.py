"""NonPDF Textual application shell."""
from __future__ import annotations

from textual.app import App

from nonpdf import __brand__, __creator__, __version__
from nonpdf.net.callback import CallbackServer
from nonpdf.tui.screens import (
    AboutScreen,
    DashboardScreen,
    GenerateScreen,
    ListenerScreen,
    PayloadsScreen,
)
from nonpdf.tui.state import TuiState


APP_CSS = """
Screen {
    background: #0b0d12;
    color: #d5dae3;
}

Header {
    background: #11141b;
    color: #8fe3ff;
}

Footer {
    background: #11141b;
    color: #7c8798;
}

#banner {
    padding: 1 2;
    background: #0e1118;
    border: round #1e88a8;
    margin: 1 2 0 2;
}

.section-title {
    padding: 1 2 0 2;
    color: #8fe3ff;
}

.card {
    border: round #2a3342;
    padding: 1 2;
    margin: 1 1;
    background: #0e1118;
    height: 8;
    content-align: center middle;
}

.card:focus-within {
    border: round #48c9e8;
}

.panel {
    border: round #2a3342;
    padding: 1 2;
    margin: 1 2;
    background: #0e1118;
}

#dash-wrap, #gen-wrap, #pay-wrap, #lis-wrap, #about-wrap {
    height: 1fr;
}

#dash-cards {
    height: auto;
}

#dash-nav {
    margin: 1 2;
    height: auto;
}

.nav-row {
    height: auto;
}

.nav-row Button {
    margin-right: 1;
}

#gen-form {
    height: auto;
    margin: 0 2;
}

.form-col {
    width: 1fr;
    padding: 0 1;
}

.field-label {
    padding: 1 0 0 0;
    color: #8fe3ff;
}

.filter-label {
    padding: 1 1 0 1;
    color: #8fe3ff;
}

#gen-log {
    border: round #2a3342;
    margin: 1 2;
    background: #0a0c11;
    height: 1fr;
}

#lis-log {
    border: round #2a3342;
    margin: 1 2;
    background: #0a0c11;
    height: 1fr;
}

#lis-form {
    height: auto;
    margin: 0 2;
}

#pay-filter {
    height: auto;
    margin: 0 2;
}

#pay-filter Input {
    width: 40;
}

#payload-table {
    border: round #2a3342;
    margin: 1 2;
    height: 1fr;
    background: #0a0c11;
}

#pay-detail {
    height: auto;
}

#about-body, #about-counts {
    height: auto;
}

#about-actions {
    height: auto;
    margin: 1 2;
}

Button {
    min-width: 12;
}

Input {
    background: #0e1118;
    border: tall #2a3342;
}

Input:focus {
    border: tall #48c9e8;
}

Select {
    background: #0e1118;
}

Select > SelectCurrent {
    background: #0e1118;
}
"""


class NonPDFApp(App):
    """The cockpit."""

    CSS = APP_CSS
    TITLE = __brand__
    SUB_TITLE = f"v{__version__} · {__creator__}"

    SCREENS = {
        "dashboard": DashboardScreen,
        "generate": GenerateScreen,
        "payloads": PayloadsScreen,
        "listener": ListenerScreen,
        "about": AboutScreen,
    }

    BINDINGS = [
        ("d", "switch('dashboard')", "Dashboard"),
        ("g", "switch('generate')", "Generate"),
        ("p", "switch('payloads')", "Payloads"),
        ("l", "switch('listener')", "Listener"),
        ("a", "switch('about')", "About"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = TuiState()
        self.callback_server: CallbackServer | None = None

    def on_mount(self) -> None:
        self.switch_screen("dashboard")

    def action_switch(self, name: str) -> None:
        self.switch_screen(name)

    def on_unmount(self) -> None:
        if self.callback_server and self.callback_server.running:
            self.callback_server.stop()