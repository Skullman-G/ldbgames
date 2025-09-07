import typer
import requests
import os
import tarfile
from tqdm import tqdm
from ldbgames.shortcuts import add_shortcut
from ldbgames.aria2cpython import aria2_download

app = typer.Typer()

SERVER_URL = "http://ldbgames.com"
LOCAL_DIR = os.path.expanduser("~/.local/share/ldbgames")
os.makedirs(LOCAL_DIR, exist_ok=True)


def fetch_games():
    """Fetch the list of games from the server as JSON."""
    r = requests.get(f"{SERVER_URL}/games.json")
    if r.status_code != 200:
        typer.echo("Failed to fetch game list.")
        raise typer.Exit(code=1)
    return r.json()


@app.command()
def list():
    """List available games on the server."""
    games = fetch_games()
    for g in games:
        typer.echo(f"{g['id']}: {g['name']} (v{g['version']})")


@app.command()
def steamlink(game_id: str):
    """Add a game to the steam library"""
    games = fetch_games()
    game = next((g for g in games if g["id"] == game_id), None)
    if not game:
        typer.echo(f"Game {game_id} not found.")
        raise typer.Exit(code=1)
    
    add_shortcut(
        name=game["name"],
        exe_path=os.path.join(LOCAL_DIR, game_id, game["binary"]),
        img=game.get("img", None)
    )


@app.command()
def install(game_id: str):
    """Download a game using its JSON config"""
    games = fetch_games()
    game = next((g for g in games if g["id"] == game_id), None)
    if not game:
        typer.echo(f"Game {game_id} not found.")
        raise typer.Exit(code=1)

    url = game["url"]
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        typer.echo(f"Failed to download {game_id}.")
        raise typer.Exit(code=1)

    archive_path = os.path.join(LOCAL_DIR, f"{game_id}.tar.gz")

    # --- Download with progress bar ---
    aria2_download(game_id, game["url"], archive_path, game["sha256"])

    # --- Extract with progress bar ---
    extract_path = os.path.join(LOCAL_DIR, game_id)
    with tarfile.open(archive_path) as tar:
        members = tar.getmembers()
        with tqdm(total=len(members), desc=f"Extracting {game_id}") as progress:
            for member in members:
                tar.extract(member, path=extract_path)
                progress.update(1)

    os.remove(archive_path)

    typer.echo(f"{game_id} installed successfully!")

    add_shortcut(
        name=game["name"],
        exe_path=os.path.join(LOCAL_DIR, game_id, game["binary"]),
        img=game.get("img", None)
    )


@app.command()
def run(game_id: str):
    """Run a downloaded game based on JSON config."""
    games = fetch_games()
    game = next((g for g in games if g["id"] == game_id), None)
    if not game:
        typer.echo(f"Game {game_id} not found.")
        raise typer.Exit(code=1)

    game_path = os.path.join(LOCAL_DIR, game_id)
    binary_path = os.path.join(game_path, game["binary"])
    if not os.path.exists(binary_path):
        typer.echo(f"No executable found for {game_id}. Run `install {game_id}` first.")
        raise typer.Exit(code=1)

    os.execv(binary_path, [binary_path])
