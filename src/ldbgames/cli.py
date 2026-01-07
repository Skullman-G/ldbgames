import typer
import requests
import os
import tarfile
from tqdm import tqdm
from ldbgames.shortcuts import add_shortcut
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
from ldbgames.settings import load_settings, GAMES_DIR, SERVER_URL
import ldbgames.requests as req
import ldbgames.installed as inst

app = typer.Typer()

pbar_lock = threading.Lock()

load_settings()


@app.command()
def list():
    """List available games on the server."""
    games = req.get_game_infos()
    if not games:
        typer.echo("No games available from server.")
    else:
        for g in games:
            typer.echo(f"{g['id']}: {g['name']} (v{g['version']})")


@app.command()
def installed():
    """List installed games."""
    installed = inst.get_installed_games()

    if not installed:
        typer.echo("No games installed.")
        return

    for g in installed:
        id = g.get("id", "unknown")
        name = g.get("name", "unknown")
        version = g.get("version", -1)
        typer.echo(f"{id}: {name} (v{version})")


@app.command()
def steamlink(game_id: str):
    """Add a game to the steam library"""
    game = req.get_game_info(game_id)
    if not game:
        typer.echo(f"Game {game_id} not found.")
        raise typer.Exit(code=1)
    
    add_shortcut(
        game_id=game_id,
        name=game["name"],
        exe_path=GAMES_DIR.value / game_id / game["binary"]
    )


def download_chunk(url: str, start: int, end: int, part_path: Path, pbar: tqdm, chunk_size=8*1024*1024):
    headers = {"Range": f"bytes={start}-{end}"}
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(part_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    with pbar_lock:
                        pbar.update(len(chunk))


def parallel_download(url: str, dest: str, game_id: str, num_threads: int = 8):
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        dest_path.unlink()

    r = requests.get(url, stream=True)
    r.raise_for_status()
    total_size = int(r.headers.get("content-length", 0))
    if total_size == 0:
        raise ValueError("Could not determine file size from server.")

    chunk_size = total_size // num_threads
    ranges = []
    for i in range(num_threads):
        start = i * chunk_size
        end = (start + chunk_size - 1) if i < num_threads - 1 else total_size - 1
        ranges.append((start, end))

    temp_files = [dest_path.with_suffix(f".part{i}") for i in range(num_threads)]

    for part_file in temp_files:
        if part_file.exists():
            part_file.unlink()

    with tqdm(total=total_size, unit="B", unit_scale=True,
          desc=f"Downloading {game_id}", bar_format="{l_bar}\033[92m{bar}\033[0m{r_bar}") as pbar:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(download_chunk, url, start, end, part_file, pbar)
                for (start, end), part_file in zip(ranges, temp_files)
            ]
            for future in futures:
                future.result()
    
    with open(dest_path, "wb") as outfile:
        for part_file in temp_files:
            with open(part_file, "rb") as f:
                outfile.write(f.read())
            part_file.unlink()


@app.command()
def install(game_id: str):
    """Download a game using its JSON config"""
    game = req.get_game_info(game_id)
    if not game:
        typer.echo(f"Game {game_id} not found.")
        raise typer.Exit(code=1)

    url = f"{SERVER_URL.value}/api/games/{game_id}/download"
    archive_path = GAMES_DIR.value / f"{game_id}.tar.gz"

    # --- Download with progress bar ---
    parallel_download(url, archive_path, game_id)

    # --- Extract with progress bar ---
    extract_path = GAMES_DIR.value / game_id
    with tarfile.open(archive_path) as tar:
        members = tar.getmembers()
        with tqdm(
            total=len(members),
            desc=f"Extracting {game_id}",
            bar_format="{l_bar}\033[93m{bar}\033[0m{r_bar}"
        ) as progress:
            for member in members:
                tar.extract(member, path=extract_path)
                progress.update(1)

    os.remove(archive_path)

    typer.echo(f"{game_id} installed successfully!")

    add_shortcut(
        game_id=game_id,
        name=game["name"],
        exe_path=GAMES_DIR.value / game_id / game["binary"]
    )


@app.command()
def run(game_id: str):
    """Run a downloaded game based on JSON config."""
    game = req.get_game_info(game_id)
    if not game:
        typer.echo(f"Game {game_id} not found.")
        raise typer.Exit(code=1)

    game_path = GAMES_DIR.value / game_id
    binary_path = game_path / game["binary"]
    if not binary_path.exists():
        typer.echo(f"No executable found for {game_id}. Run `ldbgames install {game_id}` first.")
        raise typer.Exit(code=1)

    os.execv(binary_path, [binary_path])


@app.command()
def cleanup():
    """Fixup or add game info files based on installed games"""
    inst.cleanup()
