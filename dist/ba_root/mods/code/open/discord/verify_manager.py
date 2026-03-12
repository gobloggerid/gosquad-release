# Released under the MIT License. See LICENSE for details.
"""In-game verification state for external Discord auth bridge."""

from __future__ import annotations

import bascenev1 as bs


class DiscordVerifyManager:
    """Stores and validates temporary admin verifications."""

    verified_admins: dict[int, str] = {}

    @classmethod
    def mark_admin_verified(cls, client_id: int, shortname: str) -> bool:
        """Verify by matching current client id + shortname in session."""
        try:
            session = bs.get_foreground_host_session()
            if session is None:
                return False

            player = next(
                (
                    p
                    for p in session.sessionplayers
                    if p.inputdevice.client_id == client_id
                ),
                None,
            )
            if player is None:
                return False

            current_shortname = player.getname(full=False, icon=False)
            if current_shortname != shortname:
                return False

            cls.verified_admins[client_id] = shortname
            bs.broadcastmessage(
                'Admin verification successful.',
                clients=[client_id],
                transient=True,
                color=(0, 1, 0),
            )
            return True
        except Exception as exc:
            print(
                f'Discord verification error for {client_id}/{shortname}: {exc}'
            )
            return False

    @classmethod
    def is_admin_verified(cls, client_id: int, current_shortname: str) -> bool:
        """Return whether client/name pair still matches verified state."""
        return cls.verified_admins.get(client_id) == current_shortname

    @classmethod
    def remove_verified_admin(cls, client_id: int) -> None:
        """Remove verification for disconnected/renamed admin."""
        cls.verified_admins.pop(client_id, None)
