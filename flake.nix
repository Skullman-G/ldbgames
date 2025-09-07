{
  description = "LDB Games CLI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    python = pkgs.python3;
    pythonPackages = pkgs.python3Packages;
  in {
    packages.${system}.default = pythonPackages.buildPythonPackage {
      pname = "ldbgames";
      version = "0.1.0";
      src = ./.;

      buildInputs = [ python pythonPackages.setuptools ];

      propagatedBuildInputs = with pythonPackages; [
        typer
        requests
        tqdm
        vdf
        psutil
      ];

      pyproject = true;
    };

    apps.${system}.default = {
      type = "app";
      program = "${self.packages.${system}.default}/bin/ldbgames";
    };
  };
}
