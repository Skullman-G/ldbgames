import os
from pathlib import Path

SERVER_URL = "http://ldbgames.com"
LOCAL_DIR = Path(os.path.expanduser("~/.local/share/ldbgames"))
os.makedirs(LOCAL_DIR, exist_ok=True)