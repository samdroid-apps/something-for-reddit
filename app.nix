{ stdenv
, intltool
, gdk_pixbuf
, python3
, pkgconfig
, gtk3
, glib
, hicolor_icon_theme
, makeWrapper
, itstool
, gnome3
, autoconf
, pango
, atk
, sassc }:

let
  py = python3;
  # VERSION:
  version = "0.2.2";
in
stdenv.mkDerivation rec {
  name = "something-for-reddit-${version}";

  src = ./.;

  propagatedUserEnvPkgs = [ gnome3.gnome_themes_standard ];
  nativeBuildInputs = [
    pkgconfig
    autoconf
    gnome3.gnome-common
    intltool
    itstool
    sassc
    py.pkgs.pytest
    py.pkgs.pytestcov
  ];

  buildInputs = [
    gtk3
    glib
    gdk_pixbuf
    pango
    py 
    hicolor_icon_theme
    gnome3.gsettings_desktop_schemas
    makeWrapper
    gnome3.webkitgtk
    gnome3.libsoup
  ] ++ (with py.pkgs; [
    pygobject3
    markdown
    arrow
  ]);

  preConfigure = ''
    ./autogen.sh
  '';

  extraLibs = [
    gnome3.webkitgtk
    gnome3.libsoup
    gtk3
    glib
    pango
    # full output for the gi typelib files:
    pango.out
    atk
    gdk_pixbuf
  ];
  extraTypelibPath = let
    paths = map (lib: "${lib}/lib/girepository-1.0/") extraLibs;
  in
    builtins.concatStringsSep ":" paths;
  extraLibPath = stdenv.lib.makeLibraryPath extraLibs;

  preFixup = ''
    wrapProgram "$out/bin/reddit-is-gtk" \
      --prefix XDG_DATA_DIRS : "$out/share:${gnome3.gnome_themes_standard}/share:$XDG_ICON_DIRS:$GSETTINGS_SCHEMAS_PATH" \
      --prefix GI_TYPELIB_PATH : "${extraTypelibPath}:$GI_TYPELIB_PATH" \
      --prefix LD_LIBRARY_PATH : "${extraLibPath}" \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';

  meta = with stdenv.lib; {
    homepage = https://github.com/samdroid-apps/something-for-reddit;
    description = "A Reddit Client For GNOME (with Gtk+ and Python)";
    maintainers = with maintainers; [ samdroid-apps ];
    license = licenses.gpl3;
    platforms = platforms.linux;
  };
}
