Run this command to build the app (remembering to change the subject):

```sh
flatpak-builder build-dir \
  today.sam.reddit-is-gtk.json \
  --force-clean \
  --gpg-sign=34E268B2FA2F8B13 \
  --repo=/home/sam/sam.today-flatpak-repo \
  --default-branch=stable \
  --subject="Testing build of Something for Reddit"
```

Then inside the repo directory, run this:

```sh
flatpak build-update-repo \
  --prune \
  --prune-depth=20 \
  --gpg-sign=34E268B2FA2F8B13 \
  .
rsync -rapPhz --delete . root@nix1.sam.today:/srv/flatpak.dl.sam.today/
```


