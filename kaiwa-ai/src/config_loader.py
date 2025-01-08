## config_loader.py

import toml

def load_config(file_path="/home/nagashimadaichi/dev/kaiwa/src/config.toml"):
    with open(file_path, 'r', encoding='utf-8') as file:
        config = toml.load(file)
    return config

def load_character(file_path="/home/nagashimadaichi/dev/kaiwa/src/character.toml"):
    with open(file_path, 'r', encoding='utf-8') as file:
        characters = toml.load(file)
    return characters

def load_settings(file_path="settings.toml"):
    with open(file_path, 'r', encoding='utf-8') as file:
        settings = toml.load(file)
    return settings