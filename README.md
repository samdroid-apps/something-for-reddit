# Something For Reddit

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

# Installing

I did this ages ago, so I don't really remember.

1.  Install `gnome-common`
2.  Install the `python3-arrow`  and `python3-markdown`
3.  Install a SCSS compiler (eg. `rubygem-sass` on Fedora).  This is very
    important because otherwise it will fail to build.

Then you can just install it like any usual program.

1.  Download the source code (eg. `git clone https://github.com/samdroid-apps/something-for-reddit; cd something-for-reddit`)
2.  `./autogen.sh`
3.  `make`
4.  `sudo make install`

There is a .desktop file, but it is also `reddit-is-gtk` command

Please report the bugs or deficiencies that you find via Github Issues.

# Roadmap

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
