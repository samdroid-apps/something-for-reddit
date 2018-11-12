# Something For Reddit

[![Build Status](https://travis-ci.org/samdroid-apps/something-for-reddit.svg?branch=master)](https://travis-ci.org/samdroid-apps/something-for-reddit)[![Maintainability](https://api.codeclimate.com/v1/badges/99d7155d2d7ad46df42e/maintainability)](https://codeclimate.com/github/samdroid-apps/something-for-reddit/maintainability)[![Test Coverage](https://api.codeclimate.com/v1/badges/99d7155d2d7ad46df42e/test_coverage)](https://codeclimate.com/github/samdroid-apps/something-for-reddit/test_coverage)

A simple Reddit client for GNOME, built for touch, mouse and VIM keyboards.

![Screenshot 1](http://people.sugarlabs.org/sam/reddit-screenshots/SS1.png)

![Screenshot 2](http://people.sugarlabs.org/sam/reddit-screenshots/SS2.png)

# Features

* Touchscreen tested interface
* VIM style keybindings
* View subreddits, comments and user pages
* Vote on comments and links, write replies
* Integrated WebKit2 browser for viewing links
* Multi-account support

# Packages

| Distro | Command | Info |
|--------|---------|------|
| Fedora | `dnf copr enable samtoday/something-for-reddit; dnf install something-for-reddit` | https://copr.fedorainfracloud.org/coprs/samtoday/something-for-reddit/ |
| Archlinux | `yaourt -S something-for-reddit-git` | https://aur.archlinux.org/packages/something-for-reddit-git/ |
| openSUSE | | https://software.opensuse.org/package/something-for-reddit |
| NixOS | `nix-shell --command reddit-is-gtk` | see `app.nix` for package |

# Installing

I did this ages ago, so I don't really remember.

1.  Install `gnome-common` (and autotools, etc.)
2.  Install the `python3-arrow`  and `python3-markdown`
3.  Install the `sassc` (from your package manager)

Then you can just install it like any usual program.

1.  Download the source code (eg. `git clone https://github.com/samdroid-apps/something-for-reddit; cd something-for-reddit`)
2.  `./autogen.sh`
3.  `make`
4.  `sudo make install`

There is a .desktop file, but it is also `reddit-is-gtk` command

Please report the bugs or deficiencies that you find via Github Issues.

# Development

A development shell using Nix is provided in `dev-shell.nix`.  You can run it
with the following command:

```sh
nix-shell dev-shell.nix
```

This will include instructions to run the app.

# Flatpak

You can build the flatpak with the following commands:

```sh
# Build
flatpak-builder build-dir today.sam.reddit-is-gtk.json --force-clean --repo=flatpak-repo --subject="Development build of Something for Reddit"
flatpak build-update-repo --prune --prune-depth=20 flatpak-repo
```

Note that flatpak builds it from the git repo, not your local source.  So you
need to push to a branch and change the flatpak config if you are testing
changes to the source inside of flatpak.

You can install it from your local repository:

```sh
# Initial setup (run only once):
flatpak --user remote-add --no-gpg-verify sfr-local ./flatpak-repo
flatpak --user install sfr-local today.sam.reddit-is-gtk

# To update:
flatpak update --user today.sam.reddit-is-gtk
```

# Outdated Roadmap

Feel free to contribute and do whatever you want.

Please try and use Flake8!

* **Any app icon suggestions/designs are appreciated**
    - The current one isn't great at all
* Replace the media previews, integrate them with the comments view
* Use gettext
    - **If you are interested in translateing this app, please email me!**
* Search all the subreddits on reddit
* Manage subreddits dialog
* Better handle private messages
* Multireddits in the urlbar list
* Mutlireddit add/remove subreddits

Long Term

* Optimise the comments view performance
* Separate the reddit json parsing from the view components
* Support other sites (eg. hackernews)
