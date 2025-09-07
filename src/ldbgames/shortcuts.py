import os
from pathlib import Path
import vdf

def get_steam_shortcuts_file() -> Path:
    """Return path to the Steam shortcuts.vdf file for the first user found."""
    if os.name == "posix":  # Linux / macOS
        steam_dirs = [
            Path.home() / ".local/share/Steam/userdata",
            Path.home() / ".steam/steam/userdata"
        ]
    elif os.name == "nt":  # Windows
        steam_dirs = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam/userdata"
        ]
    else:
        raise RuntimeError("Unsupported OS")

    for userdata_dir in steam_dirs:
        if userdata_dir.exists():
            for folder in userdata_dir.iterdir():
                if folder.is_dir() and folder.name.isdigit():
                    shortcuts_file = folder / "config/shortcuts.vdf"
                    if shortcuts_file.exists():
                        return shortcuts_file
    raise FileNotFoundError("Could not find Steam shortcuts.vdf")


def add_shortcut(name: str, exe_path: str, args: str = "", start_dir: str = ""):
    vdf_path = get_steam_shortcuts_file()

    with open(vdf_path, "rb") as f:
        data = vdf.binary_load(f)

    shortcuts = data.get("shortcuts", {})

    to_remove = [k for k, v in shortcuts.items() if v.get("exe") == exe_path]
    for k in to_remove:
        shortcuts.pop(k)

    idx = str(len(shortcuts))
    shortcuts[idx] = {
        "appname": name,
        "exe": exe_path,
        "StartDir": start_dir or os.path.dirname(exe_path),
        "LaunchOptions": args,
        "ShortcutPath": "",
        "IsHidden": "0",
        "AllowDesktopConfig": "1",
        "OpenVR": "0",
        "Devkit": "0",
        "DevkitGameID": "",
        "tags": {}
    }

    data["shortcuts"] = shortcuts

    with open(vdf_path, "wb") as f:
        vdf.binary_dump(data, f)

    print("Shortcut added to Steam successfully!")
