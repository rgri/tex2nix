{ pkgs ?  import <nixpkgs> {}
, pkgsSrc ? ./.
}:


with pkgs;

let
  nixFlakes = nixVersions.stable;
in
python3.pkgs.buildPythonApplication rec {
  name = "tex2nix";

  src = pkgsSrc;

  buildInputs = [ makeWrapper ];
  checkInputs = [
    python3.pkgs.black
    python3.pkgs.flake8
    glibcLocales
    mypy
    # technically not a test input, but we need it for development in PATH
    nixFlakes
  ];
  checkPhase = ''
    echo -e "\x1b[32m## run black\x1b[0m"
    LC_ALL=en_US.utf-8 black --check .
    echo -e "\x1b[32m## run flake8\x1b[0m"
    flake8 tex2nix
    echo -e "\x1b[32m## run mypy\x1b[0m"
    mypy --strict tex2nix
  '';
  makeWrapperArgs = [
    "--prefix PATH" ":" (lib.makeBinPath [ nixFlakes ])
  ];
}
