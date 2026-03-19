from __future__ import annotations

import ctypes
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

import uvicorn

from app.config import APP_DISPLAY_NAME
from app.main import create_app


@dataclass
class ServerHandle:
    server: uvicorn.Server | None = None


def _show_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, message, APP_DISPLAY_NAME, 0x10)
    except Exception:
        print(message, file=sys.stderr)


def _is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _pick_port(preferred_port: int = 8000) -> int:
    for port in range(preferred_port, preferred_port + 20):
        if _is_port_available(port):
            return port
    raise RuntimeError("No available local port was found for the desktop app.")


def _run_server(port: int, handle: ServerHandle) -> None:
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    handle.server = server
    server.run()


def _wait_until_ready(port: int, timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    url = f"http://127.0.0.1:{port}/api/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    raise RuntimeError("The local service did not become ready in time.")


def main() -> int:
    try:
        import webview
    except ImportError:
        _show_error("Desktop dependencies are missing. Please install pywebview before running the desktop app.")
        return 1

    try:
        port = _pick_port()
        handle = ServerHandle()
        server_thread = threading.Thread(target=_run_server, args=(port, handle), daemon=True)
        server_thread.start()
        _wait_until_ready(port)
        webview.create_window(
            APP_DISPLAY_NAME,
            f"http://127.0.0.1:{port}",
            width=1440,
            height=960,
            min_size=(1120, 760),
        )
        webview.start()
    except Exception as exc:  # noqa: BLE001
        _show_error(f"{APP_DISPLAY_NAME} 启动失败：{exc}")
        return 1
    finally:
        if "handle" in locals() and handle.server is not None:
            handle.server.should_exit = True
        if "server_thread" in locals():
            server_thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
