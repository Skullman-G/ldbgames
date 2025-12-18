{ config, lib, pkgs, ... }:
let
  cfg = programs.ldbgames.emulators.duckstation;
in
{
  options.programs.ldbgames.emulators.duckstation = {
    enable = lib.mkEnableOption "Enable Duckstation Ps1 emulator";
  };

  config = lib.mkIf cfg.enable {
    home.packages = with pkgs; {
      duckstation
    }
  };
}