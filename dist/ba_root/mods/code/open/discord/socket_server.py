# Released under the MIT License. See LICENSE for details.
"""Unix socket bridge to accept Discord /verify requests."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import threading

import babase
import bascenev1 as bs

from common.setting import getsetting
from code.open.discord.verify_manager import DiscordVerifyManager

_SOCKET_THREAD_STARTED = False
_DEFAULT_SOCKET_PATH = '/tmp/bombsquad_verify.sock'
_STOP_EVENT = threading.Event()
_SERVER_THREAD: threading.Thread | None = None
_SERVER_SOCK: socket.socket | None = None


def _socket_path() -> str:
    setting_path = getsetting().get('socketPath')
    if isinstance(setting_path, str) and setting_path.strip():
        return setting_path
    return _DEFAULT_SOCKET_PATH


def _handle_verify_request(client_id: int, shortname: str) -> bool:
    result: dict[str, bool] = {'ok': False}
    done = threading.Event()

    def _run_in_game_thread() -> None:
        result['ok'] = DiscordVerifyManager.mark_admin_verified(
            client_id, shortname
        )
        done.set()

    babase.pushcall(_run_in_game_thread, from_other_thread=True)
    done.wait(timeout=3.0)
    return bool(result['ok'])


def _send_response(client_sock: socket.socket, response: str) -> None:
    try:
        client_sock.sendall(response.encode('utf-8'))
    except Exception:
        pass


def _handle_client(client_sock: socket.socket) -> None:
    data_buffer = b''
    try:
        while True:
            chunk = client_sock.recv(1024)
            if not chunk:
                break
            data_buffer += chunk
            if data_buffer.endswith(b'}'):
                break

        if not data_buffer:
            _send_response(client_sock, 'ERROR: Empty payload')
            return

        payload = json.loads(data_buffer.decode('utf-8'))
        action = payload.get('action')
        client_id = payload.get('client_id')
        shortname = payload.get('shortname')

        if (
            action == 'verify_admin'
            and isinstance(client_id, int)
            and isinstance(shortname, str)
        ):
            ok = _handle_verify_request(client_id, shortname)
            _send_response(client_sock, 'OK' if ok else 'ERROR: Verification failed')
        else:
            _send_response(client_sock, 'ERROR: Invalid action or data format')

    except json.JSONDecodeError:
        _send_response(client_sock, 'ERROR: Invalid JSON')
    except Exception as exc:
        print(f'Discord socket client error: {exc}')
        _send_response(client_sock, 'ERROR: Server exception')
    finally:
        client_sock.close()


def _run_server() -> None:
    global _SERVER_SOCK

    socket_path = _socket_path()
    if os.path.exists(socket_path):
        try:
            os.unlink(socket_path)
        except OSError as exc:
            print(f'Discord socket cleanup failed: {exc}')
            return

    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    _SERVER_SOCK = server_sock
    try:
        server_sock.bind(socket_path)
        server_sock.listen(5)
        server_sock.settimeout(0.5)
        print(f'Discord verify socket listening on {socket_path}')

        while not _STOP_EVENT.is_set():
            try:
                client_sock, _ = server_sock.accept()
            except socket.timeout:
                continue
            threading.Thread(
                target=_handle_client,
                args=(client_sock,),
                daemon=True,
            ).start()
    except Exception as exc:
        print(f'Discord socket server stopped: {exc}')
    finally:
        _SERVER_SOCK = None
        server_sock.close()
        if os.path.exists(socket_path):
            try:
                os.unlink(socket_path)
            except OSError:
                pass


async def _shutdown_socket_server() -> None:
    """Gracefully stop socket server thread during app shutdown."""
    global _SERVER_THREAD

    _STOP_EVENT.set()

    # Closing the listening socket unblocks accept() immediately.
    server_sock = _SERVER_SOCK
    if server_sock is not None:
        try:
            server_sock.close()
        except Exception:
            pass

    thread = _SERVER_THREAD
    if thread is not None and thread.is_alive():
        await asyncio.to_thread(thread.join, 2.0)

    _SERVER_THREAD = None


def stop_discord_socket_server() -> None:
    """Stop background socket server if running."""
    global _SOCKET_THREAD_STARTED

    if not _SOCKET_THREAD_STARTED:
        return
    
    _shutdown_socket_server()


def maybe_start_discord_socket_server() -> None:
    """Start background socket server if enabled in settings."""
    global _SOCKET_THREAD_STARTED
    global _SERVER_THREAD

    if _SOCKET_THREAD_STARTED:
        return

    # Only run on main instance
    if bs.get_game_port() != 43210:
        return

    if not bool(
        getsetting().get('discordIntegration', {}).get('enable', False)):
        return

    _STOP_EVENT.clear()
    babase.app.add_shutdown_task(_shutdown_socket_server())
    _SERVER_THREAD = threading.Thread(target=_run_server, daemon=True)
    _SERVER_THREAD.start()
    _SOCKET_THREAD_STARTED = True
