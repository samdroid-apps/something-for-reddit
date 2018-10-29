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
, sass }:

let
  py = python3;
in
stdenv.mkDerivation rec {
  name = "something-for-reddit-0.2";

  src = ./.;

  propagatedUserEnvPkgs = [ gnome3.gnome_themes_standard ];
  nativeBuildInputs = [
    pkgconfig
    autoconf
    gnome3.gnome-common
    intltool
    itstool
    sass
  ];

  buildInputs = [
    gtk3
    glib
    py 
    hicolor_icon_theme
    gnome3.gsettings_desktop_schemas
    makeWrapper
    gnome3.webkitgtk
  ] ++ (with py.pkgs; [
    pygobject3
    markdown
    arrow
  ]);

  preConfigure = ''
    ./autogen.sh
  '';

  preFixup = let
    libPath = stdenv.lib.makeLibraryPath [ glib gtk3 gnome3.webkitgtk ];
  in
  ''
    wrapProgram "$out/bin/reddit-is-gtk" \
      --prefix XDG_DATA_DIRS : "${gnome3.gnome_themes_standard}/share:$XDG_ICON_DIRS:$GSETTINGS_SCHEMAS_PATH" \
      --prefix GI_TYPELIB_PATH : "${gnome3.webkitgtk}/lib/girepository-1.0/:$GI_TYPELIB_PATH" \
      --prefix LD_LIBRARY_PATH : "${libPath}" \
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

