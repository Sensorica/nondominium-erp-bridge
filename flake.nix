{
  description = "Nondominium ERP Bridge - Python bridge to Holochain via hc-http-gw";

  inputs = {
    holonix.url = "github:holochain/holonix?ref=main-0.6";
    nixpkgs.follows = "holonix/nixpkgs";
    flake-parts.follows = "holonix/flake-parts";
  };

  outputs = inputs@{ flake-parts, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    systems = builtins.attrNames inputs.holonix.devShells;
    perSystem = { inputs', pkgs, ... }: {
      formatter = pkgs.nixpkgs-fmt;

      devShells.default = pkgs.mkShell {
        inputsFrom = [ inputs'.holonix.devShells.default ];

        packages = with pkgs; [
          python312
          uv
        ];

        shellHook = ''
          export PS1='\[\033[1;35m\][erp-bridge:\w]\$\[\033[0m\] '
        '';
      };
    };
  };
}
