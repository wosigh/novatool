import json, copy

def get_default_config():
    return {'device_aliases':{}}

def load_config(config_file):
    config = get_default_config()
    try:
        with open(config_file, 'r') as f:
            config.update(json.load(f))
    except IOError:
        pass
    return config

def save_config(config_file, config_data):
    ret = True
    try:
        with open(config_file, 'w+') as f:
            json.dump(config_data, f, separators=(',',': '), indent=4, sort_keys=True)
            f.write('\n')
    except IOError:
        ret = False
    return ret

def gen_config(config_file):
    return save_config(config_file, get_default_config())