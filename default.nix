with import <nixpkgs> {};

let
  py = pkgs.python3;
  app = callPackage ./app.nix {};
in
stdenv.mkDerivation rec {
  name = "env";

  buildInputs = [
    app
  ];

  shellHook = ''
    export FISH_P1="(sfr) "
    export FISH_P1_COLOR="green"
  '';
}
