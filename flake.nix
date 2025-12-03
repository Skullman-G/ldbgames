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

    ldbgames-package = pythonPackages.buildPythonPackage {
      pname = "ldbgames";
      version = "0.1.0";
      src = ./.;

      buildInputs = [
        python
        pythonPackages.setuptools
        pkgs.aria2
        pkgs.makeWrapper
      ];

      propagatedBuildInputs = with pythonPackages; [
        typer
        requests
        tqdm
        vdf
        psutil
      ];

      pyproject = true;

      postInstall = ''
        wrapProgram $out/bin/ldbgames \
          --prefix PATH : ${pkgs.aria2}/bin
      '';
    };
  in {
    devShell.${system} = pkgs.mkShell {
      buildInputs = [
        ldbgames-package
      ];
    };

    nixosModules.ldbgames = { config, lib, pkgs, ...}: import ./ldbgames.nix { inherit config lib pkgs ldbgames-package; };
  };
}
