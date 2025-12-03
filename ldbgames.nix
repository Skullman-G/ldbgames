{ config, lib, pkgs, ldbgames-package, ... }:
let
  cfg = config.programs.ldbgames;
in
{
  options.programs.ldbgames = {
    client = {
      enable = lib.mkEnableOption "Enable client";
      serverIp = lib.mkOption {
        type = lib.types.str;
        default = "0.0.0.0";
        description = "The Ip adress of the server";
      };
    };
    server = {
      enable = lib.mkEnableOption "Enable server";
    };
  };

  config = {
    services.nginx = lib.mkIf cfg.server.enable {
      enable = true;
      virtualHosts."ldbgames.com" = {
        root = "/var/cache/ldbgames";
        enableACME = false;
        extraConfig = ''
          gzip off;
        '';
      };
    };

    networking.firewall.allowedTCPPorts = lib.mkIf cfg.server.enable [ 80 ];

    environment.systemPackages = lib.mkIf cfg.client.enable [
      ldbgames-package
    ];

    networking.extraHosts = lib.mkIf cfg.client.enable ''
      ${cfg.client.serverIp} ldbgames.com
    '';
  };
}