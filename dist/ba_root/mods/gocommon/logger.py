# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

import datetime
import fcntl
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs

if TYPE_CHECKING:
    pass


@dataclass
class RecentLogs:
    """Saves the recent logs."""

    chat: list[str] = field(default_factory=list)
    join: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    admin: list[str] = field(default_factory=list)
    system: list[str] = field(default_factory=list)
    host: list[str] = field(default_factory=list)
    error: list[str] = field(default_factory=list)
    transaction: list[str] = field(default_factory=list)


recent_logs = RecentLogs()


class DumpLogs:
    """Dumps the logs in the server data."""

    def __init__(self, msg: list[str], mtype: str = 'system'):
        self.msg = msg.copy()
        self.type = mtype

    def run(self):
        if len(self.msg) > 1:
            self._dump_logs()

    def _dump_logs(self):
        game_port = bs.get_game_port()
        server_logs = (
            Path(babase.Env().python_directory_user) / f'{game_port}-logs'
        )
        server_logs.mkdir(parents=True, exist_ok=True)

        log_filename = {
            'chat': 'chat.log',
            'join': 'join.log',
            'command': 'command.log',
            'admin': 'admin.log',
            'host': 'host.log',
            'error': 'error.log',
            'transaction': 'transaction.log',
        }.get(self.type, 'system.log')

        log_path = server_logs / log_filename

        if log_path.exists() and log_path.stat().st_size > 1_000_000:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            backup_path = log_path.with_name(log_path.name + timestamp)
            self.copy_file(str(log_path), str(backup_path))

        self.write_file(log_path)

    def write_file(self, file_path):
        with open(file_path, 'a+', encoding='utf-8') as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)
            try:
                for msg in self.msg:
                    file.write(msg + '\n')
                file.write('\n')
            finally:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)
                self.msg.clear()

    def copy_file(self, file_path, dest_path):
        src = Path(file_path)
        dst = Path(dest_path)

        with src.open('r') as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                shutil.copy(src, dst)
            except Exception as e:
                print(f'Error occurred while copying file: {e}')
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

        src.unlink(missing_ok=True)


def get_time() -> str:
    now = datetime.datetime.now().strftime('%A, %d-%b-%Y %H:%M:%S')
    return f'###### {now} ######'


def log(message: str, msg_type: str = 'system') -> None:
    """Cache and dumps the log."""
    log_list = None

    if msg_type == 'chat':
        if not recent_logs.chat:
            recent_logs.chat.append(get_time())
        recent_logs.chat.append(message)
        if len(recent_logs.chat) > 25:
            log_list = recent_logs.chat

    elif msg_type == 'join':
        if not recent_logs.join:
            recent_logs.join.append(get_time())
        recent_logs.join.append(message)
        if len(recent_logs.join) > 25:
            log_list = recent_logs.join

    elif msg_type == 'command':
        if not recent_logs.command:
            recent_logs.command.append(get_time())
        recent_logs.command.append(message)
        if len(recent_logs.command) > 25:
            log_list = recent_logs.command

    elif msg_type == 'admin':
        if not recent_logs.admin:
            recent_logs.admin.append(get_time())
        recent_logs.admin.append(message)
        if len(recent_logs.admin) > 25:
            log_list = recent_logs.admin

    elif msg_type == 'host':
        if not recent_logs.host:
            recent_logs.host.append(get_time())
        recent_logs.host.append(message)
        if len(recent_logs.host) > 25:
            log_list = recent_logs.host

    elif msg_type == 'error':
        if not recent_logs.error:
            recent_logs.error.append(get_time())
        recent_logs.error.append(message)
        if len(recent_logs.error) > 25:
            log_list = recent_logs.error

    elif msg_type == 'transaction':
        if not recent_logs.transaction:
            recent_logs.transaction.append(get_time())
        recent_logs.transaction.append(message)
        if len(recent_logs.transaction) > 25:
            log_list = recent_logs.transaction

    else:
        if not recent_logs.system:
            recent_logs.system.append(get_time())
        recent_logs.system.append(message)
        if len(recent_logs.system) > 25:
            log_list = recent_logs.system

    if log_list is not None:
        babase.app.threadpool.submit(DumpLogs(log_list, msg_type).run)
        log_list.clear()


def dump_logs() -> None:
    """
    Batch dump logs to log files.
    Ideally to be executed on program shutdown/restart.
    """
    DumpLogs(recent_logs.chat, 'chat').run()
    DumpLogs(recent_logs.admin, 'admin').run()
    DumpLogs(recent_logs.command, 'command').run()
    DumpLogs(recent_logs.system, 'system').run()
    DumpLogs(recent_logs.host, 'host').run()
    DumpLogs(recent_logs.error, 'error').run()
    DumpLogs(recent_logs.join, 'join').run()
    DumpLogs(recent_logs.transaction, 'transaction').run()
