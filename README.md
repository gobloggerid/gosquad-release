# GOSQUAD (BOMBSQUAD MOD)
A modified version of BombSquad game (API 9).


# PREREQUISITES
- Computer with x86 or Arm CPU. Dedicated machine (VPS or bare metal) is recommended.
- 1 core cpu (more is better).
- 1 GB free memory (more is better).
- This program is built against Debian Linux 12 (bookworm).
  - It is recommended to use Debian with the same version or newer.
  - Or use the derivated distro: Ubuntu 24 (noble), MX Linux 23.6 (Libretto)
- Fast internet connection.


# STEPS TO INSTALL
Method 1: Using HTTP
```
tmux new -s gosquad
git clone https://github.com/gobloggerid/gosquad.git
git config --global credential.helper store
```

Method 2: using ssh
```
ssh-keygen -t rsa -b 4096 -C "email@example.com"
ssh-add ~/.ssh/id_rsa
```

Copy the public key to github
```
cat ~/.ssh/id_rsa.pub
```

Then
```
git clone git@github.com:gobloggerid/gosquad.git
```


Once finished, navigate to downloaded gosquad directory, then prepare and install required files/modules.
```
cd gosquad
sudo chmod +x prepare_files.sh install_python.sh install_redis.sh

./prepare_files.sh
./install_python.sh
./install_redis.sh
```


# RUN THE GAME
**Recommended:** Use virtual environment
```
python3.13 -m venv venv
source venv/bin/activate
./gosquad_server
```

or to run in debug mode
```
python3.13 gosquad_server
```


# CONFIGS
Use --config argument to run different config file other than  config.toml or to run multiple config files.
```
./gosquad_server --config ffa.toml
./gosquad_server --config ffa.toml team.toml sport.toml
```

Use --port argument to run on different port
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
sudo chmod +x install_requirements.sh
sudo ./install_requirements.sh

```

Install missing/outdated package individually.
Open install_requirements.sh.
Then install the packages one by one using the commands on install_requirements.sh
