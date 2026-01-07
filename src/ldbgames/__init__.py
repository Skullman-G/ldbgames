import os
from pathlib import Path

LOCAL_DIR = Path(os.path.expanduser("~/.local/share/ldbgames"))
os.makedirs(LOCAL_DIR, exist_ok=True)
