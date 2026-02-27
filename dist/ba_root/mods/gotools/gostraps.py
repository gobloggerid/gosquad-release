# Released under the MIT License. See LICENSE for details.
#
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

# pylint: disable=import-error
# pylint: disable=import-outside-toplevel
# pylint: disable=protected-access

from __future__ import annotations

import importlib
from pathlib import Path
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import requests
from gobase import godata, svdata
from gocommon import helper, logger
from gocommon.gosetting import getsetting
from gostorage import redisclient

if TYPE_CHECKING:
    pass


# ba_meta export babase.Plugin
class GoPlugin(babase.Plugin):
    def on_app_running(self):
        import bauiv1 as bui
        from goextra import characterchooser, customcharacter

        from gotools.account import AccountLogin

        # apply_overlay_modules()
        # apply_additional_actor_aliases()  # In case old imports still lingering

        plus = bui.app.plus
        goset = getsetting()
        if goset.get('useV2Account', False):
            if (
                plus.get_v1_account_state() == 'signed_in'
                and plus.accounts.have_primary_credentials()
                # and plus.get_v1_account_type() == "V2"
            ):
                pass
            else:
                print('V2 account setting enabled. Please follow instructons.')
                babase.apptimer(1, AccountLogin)
        else:
            plus.accounts.set_primary_credentials(None)
            plus.sign_in_v1('Local')

        apply_additional_maps()
        apply_mods_modules()

        if goset.get('characterChooser', True):
            characterchooser.enable()
        if goset.get('customCharacter', True):
            customcharacter.enable()

    def on_app_shutdown(self):
        logger.dump_logs()
        redisclient.shutredis()


def apply_additional_maps():
    """Imports the custom games from the games directory."""
    base_dir = Path(babase.Env().python_directory_user)
    maps_dir = base_dir / 'maps'
    maps_dir.mkdir(parents=True, exist_ok=True)
    for module in maps_dir.glob('*'):
        if module.suffix in {'.py', '.so'}:
            importlib.import_module(f'maps.{module.stem}')

    # games_dir = base_dir / "games"
    # games_dir.mkdir(parents=True, exist_ok=True)
    # sys.path.append(str(games_dir))
    # for game in games_dir.glob("*.so"):
    #     importlib.import_module(f"games.{game.stem}")


def apply_mods_modules():
    apply_on_player_request()
    apply_hit_message()
    apply_activity_on_begin()
    apply_score_screen_on_begin()
    apply_map_init()
    reload_chat_message_hook()
    fetch_server_info()
    load_server_data()
    maintain_player_stats()
    apply_other_settings()


def reload_chat_message_hook() -> str | None:
    """Intercept/filter chat messages."""
    from bascenev1 import _hooks
    from goservice.chat import handler

    _hooks.filter_chat_message = handler.handle_chat
    bs.reload_hooks()


def load_server_data():
    svdata.Command.load()
    svdata.Alias.load()
    svdata.Rank.load()
    svdata.Role.load()
    svdata.Achievement.load()
    svdata.Hide.load()
    svdata.Item.load()
    svdata.Language.load()
    svdata.Whitelist.load()
    # svdata.dump_redis()  #  We set this on redis.conf


def fetch_server_info():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        svdata.Setting.server_info = {
            'ip': data.get('ip'),
            'city': data.get('city'),
            'region': data.get('region'),
            'country': data.get('country'),
            'loc': data.get('loc'),  # Latitude and Longitude
        }
    except Exception as e:
        print(f'Error: {e}')
        return


def apply_other_settings():
    babase.apptimer(7, svdata.Setting.load_server_ban_settings)
    allow: bool = getsetting()['kickIdlePlayer']
    babase.apptimer(10, bs.CallStrict(bs.set_allow_kick_idle_players, allow))


def maintain_player_stats():
    svdata.Stat.cleanup()
    svdata.Topper.set()


def apply_hit_message():
    from gobeautify import hitmessage

    if getsetting()['hitMessage']:
        bs.HitMessage = hitmessage.HitMessage


def on_player_request(func) -> bool:
    from goservice.gocheck import player_check

    def wrapper(*args, **kwargs):
        if args[1].inputdevice.client_id not in svdata.Player.get('live'):
            player_check.check_player(
                args[1].get_v1_account_id(),
                args[1].inputdevice.client_id,
                args[1].inputdevice.get_v1_account_name(full=True),
            )
            return False

        status = godata.Status.get(args[1].get_v1_account_id())
        if status.get('banned_global', False):
            helper.screen(
                "You're banned from all servers. Try /unban global status.",
                args[1].inputdevice.client_id,
                'red',
            )
            bs.getsound('error').play()
            return False

        if status.get('banned_team', False) and helper.is_team_server():
            helper.screen(
                "Your're banned from team server. Try /unban team status.",
                args[1].inputdevice.client_id,
                'red',
            )
            bs.getsound('error').play()
            return False

        elif status.get('banned_ffa', False) and not helper.is_team_server():
            helper.screen(
                "You're banned from ffa server. Try /unban ffa status.",
                args[1].inputdevice.client_id,
                'red',
            )
            bs.getsound('error').play()
            return False

        limit = getsetting()['limitPlayerPerDevice']
        if limit.get('enable', False):
            max_players = (
                limit.get('maxPlayer', 2)
                if len(args[0].sessionplayers)
                < limit.get('whenPlayerLessThan', 10)
                else 1
            )
            p_count = 0

            for p in args[0].sessionplayers:
                if p.get_v1_account_id() == args[1].get_v1_account_id():
                    p_count += 1

            if p_count >= max_players:
                helper.screen(
                    'Reached maximum players per device.',
                    args[1].inputdevice.client_id,
                    'red',
                )
                bs.getsound('error').play()
                return False

        # Call the original function
        return func(*args, **kwargs)

    return wrapper


def apply_on_player_request():
    from bascenev1._session import Session

    Session.on_player_request = on_player_request(Session.on_player_request)


def apply_activity_on_begin():
    from gobeautify import caller
    from goextra.quiz import quiz_system
    from goextra.votingmachine import vote_system

    orig_on_begin = bs._activity.Activity.on_begin

    def activity_on_begin(self):
        """Runs when game is began."""
        orig_on_begin(self)
        caller.decorate_map()
        mod_game_activity()
        quiz_system.start()
        vote_system.on_begin()
        godata.Ban.remove_betrayer()

    bs._activity.Activity.on_begin = activity_on_begin


def mod_game_activity() -> None:
    activity = bs.get_foreground_host_activity()
    if not isinstance(activity, bs.GameActivity):
        return

    if getsetting()['printPlayerCount']:
        print(
            f'Total Players: {len(activity.players)} '
            f'Game: {activity.getname()} '
            f'Map: {activity.map.getname()}'
        )
    activity.customdata['default_slow_motion'] = (
        activity.globalsnode.slow_motion
    )


def on_map_init(func):
    from gobeautify import maptext, textonmap

    def _init_map_text() -> None:
        try:
            activity = bs.getactivity()
        except Exception:
            return
        with activity.context:
            maptext.MapText()
            if getsetting().get("textOnMap", False):
                textonmap.TextOnMap()

    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        babase.pushcall(_init_map_text)

    return wrapper


def apply_map_init():
    from bascenev1._map import Map

    Map.__init__ = on_map_init(Map.__init__)


def score_screen_on_begin(func) -> None:
    from gobeautify import maptext
    from goextra import teambalancer
    from goextra.quiz import quiz_system

    """Runs when score screen is displayed."""

    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)  # execute the original method
        svdata.Player.update_count(len(self.players))
        if getsetting()['endRoundMessage']:
            maptext.end_round_message()
        if getsetting()['autoBalanceTeam']:
            teambalancer.balance_teams()
        if getsetting()['statistics']:
            svdata.Record.update(self._stats)
        if getsetting()['quizCoin']:
            quiz_system.generate_questions()
        return result

    return wrapper


def apply_score_screen_on_begin():
    from bascenev1._activitytypes import ScoreScreenActivity

    ScoreScreenActivity.on_begin = score_screen_on_begin(
        ScoreScreenActivity.on_begin
    )


def apply_overlay_modules() -> None:
    # IMPORTANT: import/apply in dependency order.
    # Importing all overlays up-front can bind old class bases
    # (for example playerspaz -> old Spaz) before overlay apply runs.

    # bascenev1
    from goscene import _session as _session_overlay

    _session_overlay.apply()
    from goscene import _multiteamsession as _multiteamsession_overlay

    _multiteamsession_overlay.apply()
    from goscene import _freeforallsession as _freeforallsession_overlay

    _freeforallsession_overlay.apply()
    from goscene import _actor as _actor_overlay

    _actor_overlay.apply()
    from goscene import _activity as _activity_overlay

    _activity_overlay.apply()
    from goscene import _gameactivity as _gameactivity_overlay

    _gameactivity_overlay.apply()
    from goscene import _map as _map_overlay

    _map_overlay.apply()
    from goscene import _messages as _messages_overlay

    _messages_overlay.apply()
    from goscene import _powerup as _powerup_overlay

    _powerup_overlay.apply()
    from goscene import _gameutils as _gameutils_overlay

    _gameutils_overlay.apply()
    from goscene import _lobby as _lobby_overlay

    _lobby_overlay.apply()
    from goscene import _stats as _stats_overlay

    _stats_overlay.apply()

    # baclassic
    from goscene import _servermode as _servermode_overlay

    _servermode_overlay.apply()

    # bascenev1lib
    from goscene import gameutils as gameutils_overlay

    gameutils_overlay.apply()

    # bascenev1lib.activity
    from goscene import multiteamscore as multiteamscore_overlay

    multiteamscore_overlay.apply()
    from goscene import dualteamscore as dualteamscore_overlay

    dualteamscore_overlay.apply()
    from goscene import multiteamvictory as multiteamvictory_overlay

    multiteamvictory_overlay.apply()
    from goscene import freeforallvictory as freeforallvictory_overlay

    freeforallvictory_overlay.apply()

    # bascenev1lib.actor
    from goscene import bomb as bomb_overlay

    bomb_overlay.apply()
    from goscene import powerupbox as powerupbox_overlay

    powerupbox_overlay.apply()
    from goscene import flag as flag_overlay

    flag_overlay.apply()
    from goscene import scoreboard as scoreboard_overlay

    scoreboard_overlay.apply()
    from goscene import background as background_overlay

    background_overlay.apply()
    from goscene import spazfactory as spazfactory_overlay

    spazfactory_overlay.apply()
    from goscene import spaz as spaz_overlay

    spaz_overlay.apply()
    from goscene import playerspaz as playerspaz_overlay

    playerspaz_overlay.apply()
    from goscene import spazbot as spazbot_overlay

    spazbot_overlay.apply()


def apply_additional_actor_aliases() -> None:
    import importlib
    import sys

    sys.modules['bascenev1lib.actor.cannon'] = importlib.import_module(
        'goscene.cannon'
    )
    sys.modules['bascenev1lib.actor.drone'] = importlib.import_module(
        'goscene.drone'
    )
    sys.modules['bascenev1lib.actor.extrabomb'] = importlib.import_module(
        'goscene.extrabomb'
    )
    sys.modules['bascenev1lib.actor.extraspaz'] = importlib.import_module(
        'goscene.extraspaz'
    )
    sys.modules['bascenev1lib.actor.skyland'] = importlib.import_module(
        'goscene.skyland'
    )
