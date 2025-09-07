import subprocess
from pathlib import Path
from tqdm import tqdm
import re
import hashlib
import os
import typer

def calc_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def aria2_download(game_id: str, url: str, output_path: str, sha256: str, connections: int = 16):
    """
    Download a file using aria2c with tqdm progress bar.

    Args:
        url: The URL to download.
        output_path: Full path including filename where the file will be saved.
        connections: Number of parallel connections to use.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if os.path.exists(output_path):
        typer.echo("Archive found. Continuing download...")

    command = [
        "aria2c",
        url,
        "-x", str(connections),
        "-s", str(connections),
        "-c",
        "-o", output_path.name,
        "-d", str(output_path.parent),
        "--enable-color=false",  # avoid ANSI codes in output
        "--console-log-level=warn",  # suppress unnecessary info
        "--summary-interval=1"  # print progress every second
    ]

    # Regex to extract progress percentage
    progress_re = re.compile(r"(\d+)%")

    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    ) as proc:
        pbar = tqdm(total=100, desc=f"Downloading {game_id}", unit="%")
        for line in proc.stdout:
            match = progress_re.search(line)
            if match:
                percent = int(match.group(1))
                pbar.n = percent
                pbar.refresh()
        pbar.close()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"aria2c failed with exit code {proc.returncode}")

    if os.path.exists(output_path):
        filehash = calc_sha256(output_path)
        if sha256 and filehash != sha256:
            typer.echo("Archive checksum mismatch. Redownloading...")
            os.remove(output_path)
            aria2_download(game_id, url, output_path, sha256, connections)
