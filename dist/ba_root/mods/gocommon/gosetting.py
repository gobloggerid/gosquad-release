# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

import json
import shutil
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    pass


@lru_cache
def getsetting() -> dict:
    """
    Load settings from disk or lru cache,
    create the file from default if necessary.
    This is intended to run once during initialization.
    """

    user_dir = Path(babase.Env().python_directory_user)
    usfile = user_dir / 'setting.json'
    defile = user_dir / 'configs' / 'setting.json'

    if not usfile.exists():
        shutil.copy2(defile, usfile)

    with usfile.open('r', encoding='utf-8') as f:
        return json.load(f)


def refresh() -> None:
    getsetting.cache_clear()
    getsetting()
