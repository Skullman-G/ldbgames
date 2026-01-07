from ldbgames.settings import GAMES_DIR
import json
import ldbgames.requests as req

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


def get_installed_games():
    """Return a list of installed game IDs"""
    installed = []
    if not GAMES_DIR.value.exists():
        return installed

    for entry in GAMES_DIR.value.glob("*.json"):
        game_info = get_data_from_info_file(entry.stem)
        installed.append(game_info)

    return installed


def cleanup():
    """Fixup or add game info files based on installed games"""
    if not GAMES_DIR.value.exists():
        return

    for entry in GAMES_DIR.value.glob("*.json"):
        game_info = get_data_from_info_file(entry.stem)
        
        if "id" not in game_info:
            game_info["id"] = entry.stem

        server_game_info = req.get_game_info(entry.stem)
        merged_info = game_info | server_game_info if server_game_info else game_info
        
        save_data_to_info_file(entry.stem, merged_info)