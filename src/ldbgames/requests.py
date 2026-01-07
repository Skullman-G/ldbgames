import requests
from ldbgames.settings import SERVER_URL

def get(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching {url}:\n {e}")
        return None

def get_game_info(game_id: str) -> dict:
    return get(f"{SERVER_URL.value}/api/games/{game_id}")
    

def get_game_infos() -> list:
    return get(f"{SERVER_URL.value}/api/games")