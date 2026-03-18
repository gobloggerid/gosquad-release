# File: service/discord/bot.py
"""Discord slash-command bridge for GoSquad admin verification."""

from __future__ import annotations

import json
import os
import socket

import discord
from discord import app_commands
from discord.ext import commands

def _load_settings() -> dict:
    try:
        from gocommon.setting import getsetting
    except Exception:
        return {}
    try:
        return getsetting()
    except Exception:
        return {}


def _get_str_setting(
    settings: dict, key: str, env_name: str, default: str = ''
) -> str:
    value = settings.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    env_value = os.getenv(env_name, '').strip()
    if env_value:
        return env_value
    return default


def _get_int_setting(
    settings: dict, key: str, env_name: str, default: int = 0
) -> int:
    value = settings.get(key)
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = int(value.strip())
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    env_value = os.getenv(env_name, '').strip()
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            pass
    return default


_SETTINGS = _load_settings()
_DISCORD_SETTINGS = (
    _SETTINGS.get('discordIntegration', {})
    if isinstance(_SETTINGS.get('discordIntegration', {}), dict)
    else {}
)

BOT_TOKEN = _get_str_setting(
    _DISCORD_SETTINGS, 'botToken', 'GOSQUAD_DISCORD_BOT_TOKEN'
)
GUILD_ID = _get_int_setting(
    _DISCORD_SETTINGS, 'guildId', 'GOSQUAD_DISCORD_GUILD_ID'
)
STAFF_ROLE_ID = _get_int_setting(
    _DISCORD_SETTINGS, 'staffRoleId', 'GOSQUAD_DISCORD_STAFF_ROLE_ID'
)
SOCKET_PATH = _get_str_setting(
    _DISCORD_SETTINGS,
    'socketPath',
    'GOSQUAD_DISCORD_SOCKET_PATH',
    default=os.getenv('GOSQUAD_VERIFY_SOCKET', '/tmp/gosquad_discord.sock'),
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='.', intents=intents)


@bot.event
async def on_ready() -> None:
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    try:
        if GUILD_ID <= 0:
            print(
                'Set discordIntegration.guildId in setting.json '
                'or GOSQUAD_DISCORD_GUILD_ID to enable slash command sync.'
            )
            return
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f'Synced {len(synced)} slash command(s) to guild {GUILD_ID}')
    except Exception as exc:
        print(f'Error syncing slash commands: {exc}')


@bot.tree.command(
    name='verify',
    description='Verify admin status for the current GoSquad session.',
)
@app_commands.describe(
    shortname='Current in-game shortname (case-sensitive)',
    client_id='Current in-game client id from server output',
)
async def verify(
    interaction: discord.Interaction, shortname: str, client_id: int
) -> None:
    if STAFF_ROLE_ID > 0 and all(role.id != STAFF_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            '❌ You do not have the required Staff role.',
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    client_sock: socket.socket | None = None
    try:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(SOCKET_PATH)

        payload = json.dumps(
            {
                'action': 'verify_admin',
                'client_id': client_id,
                'shortname': shortname,
            }
        )
        client_sock.sendall(payload.encode('utf-8'))

        response = client_sock.recv(1024).decode('utf-8').strip() or 'OK'
        if response == 'OK':
            await interaction.followup.send(
                f'Verification request sent for `{shortname}` (Client ID `{client_id}`).',
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f'❌ Verification failed: {response}',
                ephemeral=True,
            )
    except FileNotFoundError:
        await interaction.followup.send(
            '❌ Socket not found. Is GoSquad Discord integration enabled?',
            ephemeral=True,
        )
    except ConnectionRefusedError:
        await interaction.followup.send(
            '❌ Connection refused by GoSquad socket server.',
            ephemeral=True,
        )
    except Exception as exc:
        await interaction.followup.send(
            f'❌ Unexpected error: {exc}',
            ephemeral=True,
        )
    finally:
        if client_sock is not None:
            client_sock.close()


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    print(f'Unhandled slash command error: {error}')
    if not interaction.response.is_done():
        await interaction.response.send_message(
            '❌ An unexpected error occurred.',
            ephemeral=True,
        )
    else:
        await interaction.followup.send(
            '❌ An unexpected error occurred.',
            ephemeral=True,
        )


if __name__ == '__main__':
    if not BOT_TOKEN:
        print(
            'Set discordIntegration.botToken in setting.json '
            'or GOSQUAD_DISCORD_BOT_TOKEN before running this bot.'
        )
    else:
        bot.run(BOT_TOKEN)
