{
  description = "Texlive expressions for documents";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system}; in
      rec {
        packages.tex2nix = pkgs.callPackage ./default.nix {
          pkgsSrc = self;
        };
        defaultPackage = packages.tex2nix;
      });
}
