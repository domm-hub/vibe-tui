import os
import json
import subprocess
import platform
import shutil
from pathlib import Path

def check():
    # Get the directory of this file (vibe_tui/)
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config.json"
    
    if config_path.exists():
        with open(config_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = { "fps": 60, "fps_counter": True }
    else:
        data = {            
            "fps": 60,
            "fps_counter": True,
        }
        with open(config_path, "w") as f:
            json.dump(data, f, indent=4)
    return data

def compile_lib():
    # 1. Anchor to vibe_tui/ regardless of where Python is running from
    vibe_tui_dir = Path(__file__).resolve().parent.parent
    managers_dir = vibe_tui_dir / "managers"
    
    # 2. Handle OS differences
    ext = ".dll" if platform.system() == "Windows" else ".so"
    sopath = managers_dir / f"opt{ext}"
    cpppath = managers_dir / "opt.cpp"

    if not sopath.exists():
        # 3. Check for compiler
        if not (shutil.which("g++") or shutil.which("clang++")):
            print("Note: 'g++' not found. Performance may be reduced (using pure Python mode).")
            return None

        if not cpppath.exists():
            return None

        print(f"Compiling C++ extension: {cpppath}")
        
        # 4. Run compilation
        try:
            subprocess.run([
                "g++", "-shared", "-O3", "-fPIC", 
                "-o", str(sopath), str(cpppath)
            ], check=True, capture_output=True)
            print("Compilation successful.")
        except (subprocess.CalledProcessError, Exception) as e:
            print(f"Warning: Compilation failed ({e}). Falling back to pure Python.")
            return None
            
    return str(sopath)

def initialize():
    config = check()
    lib_path = compile_lib()
    return {
        "config": config,
        "lib_path": lib_path
    }
