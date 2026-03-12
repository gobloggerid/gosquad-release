# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from common import helper

if TYPE_CHECKING:
    pass


def balance_teams():
    session = bs.get_foreground_host_session()
    if (
        not isinstance(session, bs.DualTeamSession)
        or len(session.sessionteams) != 2
    ):
        return

    teamASize = 0
    teamBSize = 0

    # Count the players in each team
    try:
        for player in session.sessionplayers:
            if player.sessionteam.id == 0:
                teamASize += 1
            else:
                teamBSize += 1
    except:
        pass

    difference = abs(teamBSize - teamASize)

    # Shift players only if the difference is 2 or more
    if difference >= 2:
        if teamBSize > teamASize:
            # Shift players from Team B to Team A
            move_players(1, 0, difference // 2)  # Move half of the difference
        elif teamASize > teamBSize:
            # Shift players from Team A to Team B
            move_players(0, 1, difference // 2)  # Move half of the difference


def move_players(fromTeam, toTeam, count):
    session = bs.get_foreground_host_session()
    fromTeam = session.sessionteams[fromTeam]
    toTeam = session.sessionteams[toTeam]

    for i in range(count):
        if not fromTeam.players:
            break

        player = fromTeam.players.pop()
        broadcast_shifting(player)
        player.setdata(
            team=toTeam,
            character=player.character,
            color=toTeam.color,
            highlight=player.highlight,
        )
        iconinfo = player.get_icon_info()
        player.set_icon_info(
            iconinfo['texture'],
            iconinfo['tint_texture'],
            toTeam.color,
            player.highlight,
        )
        toTeam.players.append(player)
        player.sessionteam.activityteam.players.append(player.activityplayer)


def broadcast_shifting(player):
    helper.screen(
        f'Shifting {player.getname(full=True)} to balance team.',
        None,
        'random',
    )


def on_player_join(player):
    session = bs.get_foreground_host_session()
    if len(session.sessionplayers) > 1:
        return

    if isinstance(session, bs.DualTeamSession):
        return  # Only handle DualTeamSessions now
