# Released under the MIT License. See LICENSE for details.
#
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    pass


def _activate_code_paths() -> None:
    """Make internal/open packages importable before plugin startup."""
    user_root = Path(babase.Env().python_directory_user)
    code_root = user_root / 'code'
    internal = code_root / 'internal'
    open_ = code_root / 'open'

    # Keep open code first for editable overrides.
    for path in (internal, open_):
        pstr = str(path)
        if path.exists() and pstr not in sys.path:
            sys.path.insert(0, pstr)


# ba_meta export babase.Plugin
class GoPlugin(babase.Plugin):
    def on_app_running(self) -> None:
        _activate_code_paths()
        from code.internal.routine import strapper

        strapper.on_app_running()

    def on_app_shutdown(self) -> None:
        _activate_code_paths()
        from code.internal.routine import strapper

        strapper.on_app_shutdown()
