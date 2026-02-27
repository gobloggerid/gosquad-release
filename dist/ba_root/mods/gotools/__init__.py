# Released under the MIT License. See LICENSE for details.
"""Our lovely collection of gosquad modules."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    pass


# ba_meta export babase.Plugin
class Init(babase.Plugin):  # pylint: disable=too-few-public-methods
    """Initializes all of the plugins in the directory."""
