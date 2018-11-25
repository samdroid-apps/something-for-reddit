# Something For Reddit

[![Build Status](https://travis-ci.org/samdroid-apps/something-for-reddit.svg?branch=master)](https://travis-ci.org/samdroid-apps/something-for-reddit)[![Maintainability](https://api.codeclimate.com/v1/badges/99d7155d2d7ad46df42e/maintainability)](https://codeclimate.com/github/samdroid-apps/something-for-reddit/maintainability)[![Test Coverage](https://api.codeclimate.com/v1/badges/99d7155d2d7ad46df42e/test_coverage)](https://codeclimate.com/github/samdroid-apps/something-for-reddit/test_coverage)

A simple Reddit client for GNOME, built for touch, mouse and VIM keyboards.

![Screenshot of AskReddit](https://raw.githubusercontent.com/samdroid-apps/something-for-reddit/master/screenshots/0.2.1-askreddit.png)

![Screenshot of the content view](https://raw.githubusercontent.com/samdroid-apps/something-for-reddit/master/screenshots/0.2.1-dankmemes.png)

![Screenshot of the dark view](https://raw.githubusercontent.com/samdroid-apps/something-for-reddit/master/screenshots/0.2.1-dark.png)

# Features

* Touchscreen tested interface
* VIM style keybindings
* View subreddits, comments and user pages
* Vote on comments and links, write replies
* Integrated WebKit2 browser for viewing links
* Multi-account support

# Packages

Up to date:

| Distro | Command | Info |
|--------|---------|------|
| Flatpak | `flatpak install https://flatpak.dl.sam.today/today.sam.reddit-is-gtk.flatpakref` | |
| NixOS | Run `nix-shell --command reddit-is-gtk` inside the git repo | see `app.nix` for package |
| openSUSE | | https://software.opensuse.org/package/something-for-reddit |

Being updated (feel free to contribute):

| Distro | Command | Info |
|--------|---------|------|
| Fedora | `dnf copr enable samtoday/something-for-reddit; dnf install something-for-reddit` | https://copr.fedorainfracloud.org/coprs/samtoday/something-for-reddit/ |
| Archlinux | `yaourt -S something-for-reddit-git` | https://aur.archlinux.org/packages/something-for-reddit-git/ |

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
flatpak-builder build-dir today.sam.reddit-is-gtk.json --force-clean --install
```

To build the from the local copy of your source, use change the sources option
in the flatpak to as follows:

```json
      "sources": [
        {
          "type": "dir",
          "path": ".",
          "skip": [
            "__build_prefix",
            ".flatpak-builder",
            "flatpak-repo"
          ]
        }
      ]
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
