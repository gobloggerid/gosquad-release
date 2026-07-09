# GoSquad (BombSquad Mod, API 9)
Simple guide to install and run the GoSquad server.

**What you need**
- Computer with x86_64 or AARCH64 CPU (dedicated is recommended)
- 1 CPU core (more is better)
- 1 GB free RAM (more is better)
- Ubuntu 24.04 or newer (binary built for 24.04)
- Internet connection

**Read before you start**
- Use at your own risk
- What you see is what you get
- Please read LICENSE file

## Instruction
Run the following commands one by one.
- Copy each command (CTRL + C).
- Paste to your console (CTRL + SHIFT + V).
- Press ENTER.
- Or just rewrite the commands then run as usual.

## Setup
Update system:
```bash
sudo apt update && sudo apt upgrade -y
```

Install tools (if missing):
```bash
sudo apt install --upgrade git tmux -y
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
git clone -b main --single-branch --depth 1 https://github.com/n00bility/gosquad.git
```
- If `aarch64`:
```bash
git clone -b aarch --single-branch --depth 1 https://github.com/n00bility/gosquad.git
```

Go to the project folder:
```bash
cd gosquad
```

Make setup files executable:
```bash
sudo chmod +x prepare_files.sh install_python.sh install_requirements.sh install_database.sh
```

Prepare program files:
```bash
bash prepare_files.sh
```

Install python3.13:
```bash
bash install_python.sh
```

Install required packages:
```bash
bash install_requirements.sh
```

Install database (System will reboot to take effect):
```bash
bash install_database.sh
```

In a non-standard system, there's a chance the database fail to run using its default configuration.
In that case, you need to disable unix socket and fall back to using TCP.
Open and disable the unix socket in *dist/ba_root/mods/data/configs/setting.json*
Find and set *Settings -> unixSocket -> false*

## Run the game
If you just rebooted, start a new session:
```bash
tmux new -s gosquad
```

Else:
```bash
tmux attach-session -t gosquad
```

Activate virtual environment:
```bash
source venv/bin/activate
```

Start the server:
```bash
./gosquad_server
```

## Extra - Playlists and ports (You can skip this)
Default:
- Config file: `config.toml`
- UDP port: `43210`

Run a different playlist:
```bash
./gosquad_server --config ffa.toml
```

Run on another port (No need to edit port in the file):
```bash
./gosquad_server --config ffa.toml --port 43211
```

Run multiple playlists on one port (rotates on restart):
```bash
./gosquad_server --config ffa.toml team.toml smash.toml --port 43211
```

Playlist files:
- Defaults: `./dist/ba_root/mods/data/defaults/playlists/`
- Live edits: `./dist/ba_root/mods/data/live/playlists/` | These are the ones to edit.

## Make yourself owner
Do this only once.
- Put your `account_id` in the `admins` list inside your config file (`config.toml` or another active toml file).
- If `protocol_version > 35`, your id starts with `a-`.
- If `protocol_version <= 35` (default), your id starts with `pb-`.
- You can add both to be safe.
- You are owner for permanently.

After you join the server, run this command in the chat:
```bash
/role import
```

## Commands
Two ways to browse commands:
- Read help files: `./dist/ba_root/mods/defaults/languages/`
- In game:
```bash
/command help
```
```bash
/role help
```
```bash
/ban requirement
```
```bash
/effect info
```

## Notes
- Commands need levels/roles/coins depending on the type.
- Admin commands always need reason to run, otherwise they will use coins.
- E.g.: /restart aNy ReASon yoU wAnt -> to restart server.
- This to avoid being abused by server admins.
- Admin commands will be logged, coins commands will not.
- Fun and Cheat commands always need coins regardless the executor.
- All the files under `./dist/ba_root/mods/data/live/` are safe to edit.
- If you break them, delete them to restore the defaults.
- `settings.json` controls server settings.
- GoSquad comes with plenty of server coins.
- As owner, you won't need it for most of the time.
- Except for assigning roles to players.
- Or sending coins to them (as giveaways).
- Contact author on discord to top up.

## Notes 2
- Discord module may not ready. We have not tested it. You have to test it yourself and edit it if needed to make it work.
- This module is taken from HeyFang bombsquad repository.
- You may want to explore the server features for a while privately before you make the server public.
- It is recommended to use V2 Account. With it, you can use ballistica cloud console to manage your server without joining.
  - Do this by logging in with your V2 account when the server starts.
- GoSquad is multi-instances ready. Meaning, you can run as many server as you want at the same time on the same machine. All of them will share the same/unified database.
  - Learn about tmux pane/window to manage instance efficiently.

**Cloud Command**
On your ballistica cloud console
```
from bascenev1.cloudcmd import cc
cc.command()
```
This will print all the available cloud commands.

Examples of available commands:

Find players whose their names cointains 'n00b' word.
```
from bascenev1.cloudcmd import cc
cc.find('n00b')
```

Ban a player using his local id (locid):
```
from bascenev1.cloudcmd import cc
cc.ban(targets='gs-001', scope='global', reason='breaking rules', duration=1, incremental=False)
```

Or you can leave the default arguments:
```
from bascenev1.cloudcmd import cc
cc.ban(targets='gs-001')
```

Or :
```
from bascenev1.cloudcmd import cc
cc.ban('gs-001')
```
