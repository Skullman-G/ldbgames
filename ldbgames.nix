{ config, lib, pkgs, ldbgames-package, ... }:
let
  cfg = config.programs.ldbgames;
in
{
  options.programs.ldbgames = {
    enable = lib.mkEnableOption "Enable client";
    serverIp = lib.mkOption {
      type = lib.types.str;
      default = "0.0.0.0";
      description = "The Ip adress of the server";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      ldbgames-package
    ];

    networking.extraHosts = ''
      ${cfg.serverIp} ldbgames.com
    '';
  };
}