# jnegrel's Kodi add-ons

A [Kodi](https://kodi.tv) repository: install it once, and Kodi keeps its add-ons up to date.

| Add-on | |
|---|---|
| [MET Norway (Yr)](https://github.com/jnegrel/kodi-weather-metno) | Weather from MET Norway, the data behind Yr, with warnings and radar rain for the next 2 hours |

## Install

1. In Kodi, allow add-ons from outside the official repository, once:
   *Settings → System → Add-ons → Unknown sources*.
2. *Settings → File manager → Add source*, type `https://jnegrel.github.io/kodi-addons/`
   and name it `jnegrel`.
3. *Settings → Add-ons → Install from zip file → jnegrel →* `repository.jnegrel-1.0.0.zip`.
   (Or download that zip from the address above and install it from a USB stick.)
4. *Install from repository → jnegrel's Kodi add-ons*, then the add-on, e.g.
   *Weather → MET Norway (Yr) → Install*.

Kodi then checks the repository at startup and once a day, and installs new versions by
itself (*Settings → System → Add-ons → Updates*: *Install updates automatically*, the default).

**If the add-on was installed from a zip before:** install it once more from the repository
(step 4). Kodi warns that the "manually installed" copy will be replaced: answer *Yes*, and
*No* when it asks whether to remove the add-on's data, so that your settings are kept. Kodi
only updates an add-on from the repository it was installed from.

## How it works

GitHub Pages serves this project at `https://jnegrel.github.io/kodi-addons/`:
`addons.xml` (the `addon.xml` of the newest version of each add-on), `addons.xml.md5`
(Kodi compares it to see whether anything changed) and `zips/<id>/<id>-<version>.zip`.
The repository add-on itself is in [`repository.jnegrel/`](repository.jnegrel) and is listed
too, so it can update itself.

To publish a new version of an add-on:

```
python3 tools/update_repo.py ../Yr/dist/weather.metno-0.3.1.zip
git add -A && git commit -m "weather.metno 0.3.1" && git push
```

For a test with a local web server (Kodi accepts plain HTTP but warns about it):

```
python3 tools/update_repo.py --base-url http://localhost:8765/ --out /tmp/repo add-on.zip
cd /tmp/repo && python3 -m http.server 8765
```

The scripts are under the [GPL-3.0](LICENSE); each add-on has its own licence.
