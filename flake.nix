{
  description = "LDB Games CLI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      overlays = [ self.overlays.default ];
    };
  in {
    devShell.${system} = pkgs.mkShell {
      buildInputs = with pkgs; [
        ldbgames
      ];
    };

    overlays = rec {
      default = ldbgames;
      ldbgames = import ./overlay.nix;
    };

    nixosModules = rec {
      default = ldbgames;
      ldbgames = import ./modules;
    };
  };
}
