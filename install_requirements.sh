#!/bin/bash

# It is recommended to run this under virtual enviroment. Run these commands:
# python3.13 -m venv venv
# source venv/bin/activate
# Once you're in venv, run this file again or run just the needed package.
# You can exit from this venv by using this command: deactivate
# Or continue running your bombsquad instance inside it.

pip install --upgrade better-profanity --target=dist/ba_data/python-site-packages 
pip install --upgrade unidecode --target=dist/ba_data/python-site-packages 
pip install --upgrade requests --target=dist/ba_data/python-site-packages 
pip install --upgrade redis[hiredis] --target=dist/ba_data/python-site-packages
pip install --upgrade psutil --target=dist/ba_data/python-site-packages
