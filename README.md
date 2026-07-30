# GoSquad (BombSquad Mod, API 9)
Simple guide to install and run the GoSquad server.

**What you need**
- Computer with x86_64 or AARCH64 CPU
- 1 CPU core or more
- 1 GB free RAM or more
- Ubuntu 24.04 or newer (binary built for 24.04)
- Internet connection
- Opened UDP port (To make the game accessible by public. The standard is 43210)

**Read before you start**
- Use at your own risk
- What you see is what you get
- Please read the LICENSE file


## Instruction
Run the following commands one by one.
- Copy each command or (CTRL + c).
- Paste to your console/terminal or (CTRL + SHIFT + v).
- Run it (press ENTER).
- Or just write the commands then run as usual.


## Preparation
1. Update system:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Install tools (if missing):
```bash
sudo apt install --upgrade git tmux -y
```

3. Create a tmux session:
```bash
tmux new -s gosquad
```

4. Download the files:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/gobloggerid/gosquad-release/main/download-gosquad.sh)
```


## Setup
6. Go to the downloaded folder:
```bash
cd gosquad
```

7. Make setup files executable:
```bash
sudo chmod +x prepare-files.sh install-python.sh install-requirements.sh install-database.sh
```

8. Prepare program files:
```bash
bash prepare-files.sh
```

9. Install python3.13:
```bash
bash install-python.sh
```

10. Install required packages:
```bash
bash install-requirements.sh
```

11. Install database (system will reboot to take effect):
```bash
bash install-database.sh
```


## Run the game
12. If you just rebooted, recreate the session:
```bash
tmux new -s gosquad
```

13. If not:
```bash
tmux attach-session -t gosquad
```

14. Start the server:
```bash
./gosquad_server
```


## Make yourself owner
15. Open `config.toml` (or another active toml file).
- You only need to do this once.
```bash
nano ./dist/ba_root/mods/data/live/playlists/config.toml
```
- Put your `account_id` in the `admins` list inside the file.
- If you use protocol_version > 35, your id starts with `a-`.
- If protocol_version <= 35 (default), your id starts with `pb-`.
- You can add both to be safe.

16. Save the configuration.
- Press CTRL + s
- Press y then ENTER
- Press CTRL + x to close the file.

- Stop the game or restart.

- Join the game, then run this command in the chat box:
```bash
/role import
```
- You are owner for permanently.


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
- Game commands need levels/roles/coins depending on the type.
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
- Avoid rookie mistake by creating tmux session again and again everytime you log in into your instance/server.
- Do this `tmux a` to log in to the last active session.
- GoSquad is multi-instances ready. Meaning, you can run as many server as you want at the same time on the same machine. All of them will share the same/unified database.
  - Learn about tmux pane/window to manage instance efficiently.
- Discord module may not ready. We have not tested it. You have to test it yourself and edit it if needed to make it work.
- This module is taken from HeyFang bombsquad repository.
- You may want to explore the server features for a while privately before you make the server public.
- It is recommended to use V2 Account. With it, you can use ballistica cloud console to manage your server without joining.
  - Do this by logging in with your V2 account when the server starts.


## Log in using V2 account
When the server starts, system will give you an url/link in the console. Copy `(CTRL + SHIFT + c)` and paste `(CTRL + v)` it onto your browser and allow the log in process.


## Using GoSquad cloud command
In any browser, log in into your account in `ballistica.net`. Go to `device` menu and open a running server in the active server list.

On the cloud console, type this then ENTER:
```
from cloudcmd import cmd
cmd.command()
```
This will print all the available cloud commands.

**Examples of available commands:**
- Find players whose their names cointains 'goblo' word:
```
from cloudcmd import cmd
cmd.find('goblo')
```

- Open ban command list:
```
from cloudcmd import cmd
cmd.ban()
```

- Open role command list:
```
from cloudcmd import cmd
cmd.role()
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
- Defaults: `./dist/ba_root/mods/data/defaults/playlists/` | It is not recommended to edit these. Instead:
- Live edits: `./dist/ba_root/mods/data/live/playlists/` | These are the ones to edit.
