import os
from pathlib import Path
import vdf
import requests
import zlib
import psutil
import subprocess
import sys
import typer
from ldbgames.settings import SERVER_URL, GAMES_DIR
import json

def close_steam():
    """Check if Steam is running, and close it if so."""
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            if "steam" in proc.info["name"].lower():
                typer.echo("Steam is running. Attempting to close it...")
                proc.terminate()
                try:
                    proc.wait(timeout=20)
                    typer.echo("Steam closed successfully.")
                except psutil.TimeoutExpired:
                    typer.echo("Steam did not close gracefully. Forcing kill...")
                    proc.kill()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def generate_shortcut_appid(exe_path: Path, shortcut_name: str) -> int:
    """
    Generate the Steam AppID for a non-Steam shortcut.
    
    :param exe_path: The target executable path.
    :param shortcut_name: The shortcut name.
    :return: The calculated AppID.
    """
    # Step 1: Concatenate
    data = f"{exe_path}{shortcut_name}"

    # Step 2: CRC32 hash
    crc = zlib.crc32(data.encode('utf-8')) & 0xFFFFFFFF

    # Step 3: Set highest bit
    appid = crc | 0x80000000

    return appid

def get_config_dir() -> Path:
    """Return path to the Steam config directory for the first user found."""
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
                    config_dir = folder / "config"
                    if config_dir.exists():
                        return config_dir
    raise FileNotFoundError("Could not find Steam config directory")


def create_images(appid: int, game_id: str):
    """Download and save game images to the specified directory."""
    game_dir = get_config_dir() / "grid"
    game_dir.mkdir(parents=True, exist_ok=True)

    images = {
        f"{appid}_hero.jpg": "hero",
        f"{appid}.jpg": "header",
        f"{appid}p.png": "grid",
        f"{appid}_icon.jpg": "icon",
        f"{appid}_logo.png": "logo"
    }

    for filename, id in images.items():
        url = f"{SERVER_URL.value}/api/games/{game_id}/img/{id}"
        with requests.get(url) as response:
            if response.status_code == 200:
                with open(game_dir / filename, "wb") as f:
                    f.write(response.content)
                typer.echo(f"Downloaded {filename}")
            else:
                typer.echo(f"Failed to download {filename} from {url}")


def get_data_from_info_file(game_id: str) -> dict:
    info_file = GAMES_DIR.value / (f"{game_id}.json")
    if not info_file.exists():
        with open(info_file, "w") as f:
            json.dump({"appid": ""}, f)

    with open(info_file, "r") as f:
            data = json.load(f)
            return data
    

def save_data_to_info_file(game_id: str, data: dict):
    info_file = GAMES_DIR.value / (f"{game_id}.json")
    with open(info_file, "w") as f:
        json.dump(data, f)


def add_shortcut(game_id: str, name: str, exe_path: Path, args: str = "", start_dir: str = ""):
    steam_was_running = close_steam()

    vdf_path = get_config_dir() / "shortcuts.vdf"

    if not vdf_path.exists():
        typer.echo("Steam shortcuts.vdf file not found. Creating new one.")
        data = {"shortcuts": {}}
    else:
        with open(vdf_path, "rb") as f:
            data = vdf.binary_load(f)

    shortcuts = data.get("shortcuts", {})

    info_data = get_data_from_info_file(game_id)
    appid = info_data.get("appid")
    if appid == "":
        appid = str(generate_shortcut_appid(exe_path, name))

    print(shortcuts)

    idx = str(len(shortcuts))

    for id, shortcut in shortcuts.items():
        if shortcut.get("appid") == appid or shortcut.get("AppName") == name:
            idx = id

    shortcuts[idx] = {
        "appid": appid,
        "AppName": name,
        "Exe": str(exe_path),
        "StartDir": start_dir or os.path.dirname(exe_path),
        "Icon": str(get_config_dir() / (f"grid/{appid}_icon.jpg")),
        "LaunchOptions": args,
        "ShortcutPath": "",
        "IsHidden": "0",
        "AllowDesktopConfig": "1",
        "OpenVR": "0",
        "Devkit": "0",
        "DevkitGameID": "",
        "tags": {}
    }

    print(shortcuts)

    data["shortcuts"] = shortcuts

    with open(vdf_path, "wb") as f:
        vdf.binary_dump(data, f)

    save_data_to_info_file(game_id, {"appid": appid})

    create_images(appid, game_id)

    typer.echo("Shortcut added to Steam successfully!")

    if steam_was_running:
        typer.echo("Restarting Steam...")
        if os.name == "nt":  # Windows
            subprocess.Popen([r"C:\Program Files (x86)\Steam\Steam.exe"])
        elif sys.platform == "darwin":  # macOS
            subprocess.Popen(["open", "-a", "Steam"])
        else:  # Linux
            os.system("xdg-open steam://")
