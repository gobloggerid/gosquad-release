# GOSQUAD (BOMBSQUAD MOD)
A modified version of BombSquad game (API 9) - private repository.


# PREREQUISITES
- Computer with x86 or Arm CPU. Dedicated is recommended.
- 1 core cpu (more is better).
- 1 GB free memory (more is better).
- This build is built against: 
  - Debian Linux 12 (bookworm) (x86).
  - Ubuntu 24.04 (noble) (arm).
  - Use Debian/Ubuntu or their derived distros with the same or higher version.
- Fast internet connection (unless for local use).


# HOW TO SETUP

## Method 1: Using HTTP
Create tmux session and clone the repository
```
tmux new -s gosquad
git config --global credential.helper store
git clone https://github.com/n00bility/gosquad.git
```

## Method 2: Using SSH
Create the key (if not done yet)
```
ssh-keygen -t rsa -b 4096 -C "email@example.com"
ssh-add ~/.ssh/id_rsa
```

Copy the public key, then save the key to github
```
cat ~/.ssh/id_rsa.pub
```

Clone the repository
```
git clone git@github.com:n00bility/gosquad.git
```


Once finished, navigate to downloaded gosquad directory, 
then prepare and install the required files/modules.
```
cd gosquad
sudo chmod +x preparation.sh install_python.sh install_database.sh

./preparation.sh
./install_python.sh
./install_database.sh
```


# RUN THE GAME
**Recommended:** Use virtual environment

Create the virtual environment
```
python3.13 -m venv venv
source venv/bin/activate
```

Run the game
```
./gosquad_server
```


# CONFIGS
Above command is to run the game with config.toml/config.json as the config file
and 43210 as the port (default)

To run another config file (if exist in ./dist/ba_root/mods/data/defaults/playlists)
```
./gosquad_server --config ffa.toml
```

or
```
./gosquad_server --config team.toml
```

To run multiple config files (change automatically after game restart)
```
./gosquad_server --config ffa.toml team.toml sport.toml
```

To run on different port
```
./gosquad_server --config ffa.toml --port 43211
```


**Quit virtual environment**
If using one
```
deactivate
```


# COMMON PROBLEMS
## Missing packages
Install missing/outdated packages in batch
```
sudo chmod +x requirements.sh
sudo ./requirements.sh

```

Install missing/outdated package individually.
Open requirements.sh.
Then install the packages one by one using the commands on requirements.sh
