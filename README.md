# GoSquad (BombSquad Mod, API 9)
Simple guide to install and run the GoSquad server.

**What you need**
- Computer with x86_64 or ARM CPU (dedicated is better)
- 1 CPU core (more is better)
- 1 GB free RAM (more is better)
- Ubuntu 24.04 or newer (binary built for 24.04)
- Internet connection

**Read before you start**
- Use at your own risk

## Setup
Install tools (if missing):
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install --upgrade git tmux
```

Create a tmux session:
```bash
tmux new -s gosquad
```

Check your CPU type:
```bash
uname -m
```

Download the server:
- If `x86_64`:
```bash
git clone -b main --single-branch https://github.com/n00bility/gosquad.git
```
- If `aarch64`:
Not available yet.

Go to the project folder:
```bash
cd gosquad
```

Run setup:
```bash
sudo chmod +x .setup.sh
bash .setup.sh
```

## Run the game
If you just rebooted:
```bash
tmux attach-session gosquad
```

Or start a new session:
```bash
tmux new -s gosquad
```

Start the server:
```bash
./gosquad_server
```

## Playlists and ports
Default:
- Config file: `config.toml`
- UDP port: `43210`

Run a different playlist:
```bash
./gosquad_server --config ffa.toml
```

Run on another port:
```bash
./gosquad_server --config ffa.toml --port 43211
```

Run multiple playlists on one port (rotates on restart):
```bash
./gosquad_server --config ffa.toml team.toml smash.toml --port 43211
```

Playlist files:
- Defaults: `./dist/ba_root/mods/data/defaults/playlists/`
- Live edits: `./dist/ba_root/mods/data/live/playlists/`

## Make yourself owner
Do this once.
- Put your `account_id` in the `admins` list inside your config file (`ffa.toml`, `team.toml`, etc.).
- If `protocol_version > 35`, your id starts with `a-`.
- If `protocol_version <= 35` (default), your id starts with `pb-`.
- You can add both to be safe.
- You are owner for permanently.

After you join the server, run in chat:
```bash
/role import
```

## Commands
Two ways:
- Read help files: `./dist/ba_root/mods/defaults/languages/`
- In game:
```bash
/command help
```
```bash
/ban help
```
```bash
/ban requirement
```

## Notes
- Commands need levels/roles/coins depending on type.
- Files in `./dist/ba_root/mods/data/live/` are safe to edit.
- If you break them, delete them to restore defaults.
- `settings.json` controls server settings.
- GoSquad comes with plenty of server coins.
- As owner, you won't need it for most of the time.
- Except for assigning roles to players.
- Or sending coins to them (giveaways).
- Contact author on discord to top up.

## Notes 2
- Discord module is not ready. You have to edit it to make it works.
- This module is take from HeyFang bombsquad repository.
- You may want to explore the server features for a while privately before you make the server public.