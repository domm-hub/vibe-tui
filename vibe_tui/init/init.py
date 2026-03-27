import os
import json

def check():
    # Get the directory where vibe_tui is located
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    
    if os.path.isfile(config_path):
        with open(config_path, "r") as f:
            data = json.load(f)
    else:
        data = {            
            "fps": 60,
            "fps_counter": True,
        }
        with open(config_path, "w") as f:
            json.dump(data, f, indent=4)
    return data

def initialize():
    config = check()
    return {"config": config}

    