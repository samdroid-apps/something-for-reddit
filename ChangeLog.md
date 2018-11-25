# 0.2.2 - “The Bugfix Release ⓇⒺⒹⓊⓍ”

26/Nov/2018

- Fixes sign in issues on newer versions of webkit (#61, #58)

# 0.2.1 - “The Bugfix Release”

25/Nov/2018

It has been great to come back and revitalize this app after 2 years of
neglect.  I'm excited about how far this app can be improved, and think this
release makes a good stepping stone towards future features and improvements.

## Added

- The frontpage is now visible.  You can see it by going to `/` in the url bar.
  (#56)
- The app now supports Flatpak & NixOS installation
- Performance improvements in the comments view
- The codebase is now tested!  I'm pretty sure this is one of the only GTK+
  apps which has proper UI tests - so this should stop more regressions in the
  future!

## Changed

- Replaced the markdown engine, should now support more features (#66)
- The alignment in subreddit listings should now be more uniform. (#64)
- Many size related bugs have been fixed (#6, #47, #72)
- The url bar is now less lenient on formatting.  Previously, going to `/linux`
  would take you to `/r/linux`.  Due to the frontpage changes, this no longer
  happens
- [PACKAGING] Moved icons from pixmaps to the hicolor directory
- [PACKAGING] Change SCSS compiler from ruby sass to sassc
