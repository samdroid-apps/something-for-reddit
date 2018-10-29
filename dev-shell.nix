with import <nixpkgs> {};

let
  py = pkgs.python3;
  app = callPackage ./app.nix {};

  helpMessage = ''
To setup the build environment, you will need to run autogen:

  ./autogen.sh --prefix=$PREFIX

To build, you can use the following commands:

  make; and make install; and reddit-is-gtk

The environment is configured so that the builds will be installed
into the `__build_prefix` directory.  Root is not required.
  '';
in
stdenv.mkDerivation rec {
  name = "env";

  buildInputs = app.nativeBuildInputs ++ app.buildInputs;

  shellHook = ''
    export FISH_P1="(sfr-dev) "
    export FISH_P1_COLOR="magenta"

    export PREFIX=$(pwd)/__build_prefix

    export XDG_DATA_DIRS=$PREFIX/share:${gnome3.gnome_themes_standard}/share:$XDG_DATA_DIRS:$XDG_ICON_DIRS:$GSETTINGS_SCHEMAS_PATH
    export GI_TYPELIB_PATH=${app.extraTypelibPath}:$GI_TYPELIB_PATH
    export LD_LIBRARY_PATH=${app.extraLibPath}:$LD_LIBRARY_PATH
    export PYTHONPATH=.:$PREFIX/lib/python3.6/site-packages:$PYTHONPATH
    export PATH=$PREFIX/bin:$PATH

    echo '${helpMessage}'
  '';
}
