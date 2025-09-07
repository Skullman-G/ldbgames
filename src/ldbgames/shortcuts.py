import os
from pathlib import Path
import vdf
import requests
import zlib
import psutil
import subprocess
import sys

def close_steam():
    """Check if Steam is running, and close it if so."""
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            if "steam" in proc.info["name"].lower():
                print("Steam is running. Attempting to close it...")
                proc.terminate()
                try:
                    proc.wait(timeout=20)
                    print("Steam closed successfully.")
                except psutil.TimeoutExpired:
                    print("Steam did not close gracefully. Forcing kill...")
                    proc.kill()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def generate_shortcut_appid(exe_path: str, shortcut_name: str) -> int:
    """
    Generate the Steam AppID for a non-Steam shortcut.
    
    :param exe_path: The target executable path (string).
    :param shortcut_name: The shortcut name (string).
    :return: The calculated AppID (int).
    """
    # Step 1: Concatenate
    data = exe_path + shortcut_name

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


def create_images(appid: int, hero: str, header: str, grid: str, icon: str, logo: str):
    """Download and save game images to the specified directory."""
    game_dir = get_config_dir() / "grid"
    game_dir.mkdir(parents=True, exist_ok=True)

    images = {
        f"{appid}_hero.jpg": hero,
        f"{appid}.jpg": header,
        f"{appid}p.png": grid,
        f"{appid}_icon.jpg": icon,
        f"{appid}_logo.png": logo
    }

    for filename, url in images.items():
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                with open(game_dir / filename, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {filename}")
            else:
                print(f"Failed to download {filename} from {url}")


def get_steam_shortcuts_file() -> Path:
    """Return path to the Steam shortcuts.vdf file for the first user found."""
    shortcuts_file = get_config_dir() / "shortcuts.vdf"
    if shortcuts_file.exists():
        return shortcuts_file
    raise FileNotFoundError("Could not find Steam shortcuts.vdf")


def add_shortcut(name: str, exe_path: str, args: str = "", start_dir: str = "", img: dict = None):
    steam_was_running = close_steam()

    vdf_path = get_steam_shortcuts_file()

    with open(vdf_path, "rb") as f:
        data = vdf.binary_load(f)

    shortcuts = data.get("shortcuts", {})

    to_remove = [k for k, v in shortcuts.items() if v.get("exe") == exe_path]
    for k in to_remove:
        shortcuts.pop(k)

    appid = generate_shortcut_appid(exe_path, name)

    idx = str(len(shortcuts))
    shortcuts[idx] = {
        "appid": str(appid),
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

    if img:
        create_images(
            appid=appid,
            hero=img.get("hero", None),
            header=img.get("header", None),
            grid=img.get("grid", None),
            icon=img.get("icon", None),
            logo=img.get("logo", None)
        )

    print("Shortcut added to Steam successfully!")

    if steam_was_running:
        print("Restarting Steam...")
        if os.name == "nt":  # Windows
            subprocess.Popen([r"C:\Program Files (x86)\Steam\Steam.exe"])
        elif sys.platform == "darwin":  # macOS
            subprocess.Popen(["open", "-a", "Steam"])
        else:  # Linux
            subprocess.Popen(["steam"])
