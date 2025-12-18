{ pkgs }:
let
  python = pkgs.python3;
  pythonPackages = pkgs.python3Packages;
in
pythonPackages.buildPythonPackage {
  pname = "ldbgames";
  version = "0.1.0";
  src = ../.;

  buildInputs = [
    python
    pythonPackages.setuptools
  ];

  propagatedBuildInputs = with pythonPackages; [
    typer
    requests
    tqdm
    vdf
    psutil
  ];

  pyproject = true;
}