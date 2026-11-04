"""Adds add-on zips to the Kodi repository and rebuilds its index.

    python3 tools/update_repo.py ../Yr/dist/weather.metno-0.3.0.zip

Kodi reads, under the base URL (GitHub Pages of this project):
- addons.xml: the addon.xml of the newest version of every add-on,
- addons.xml.md5: its checksum, which Kodi checks to see whether anything changed,
- zips/<id>/<id>-<version>.zip, and the add-on's icon next to it.
The repository add-on itself (repository.jnegrel/) is one of these add-ons, so that it can
update itself; a copy of its zip and index.html at the top let people install it, also
from Kodi's file manager (Kodi reads the links of index.html as a folder listing).

--base-url and --out make a copy for testing with a local web server:
    python3 tools/update_repo.py --base-url http://localhost:8000/ --out /tmp/repo add-on.zip
"""

import argparse
import hashlib
import html
import io
import os
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
REPOSITORY = 'repository.jnegrel'
BASE_URL = 'https://jnegrel.github.io/kodi-addons/'


def version_key(version):
    return tuple(int(part) if part.isdigit() else part for part in re.split(r'[.~+-]', version))


def addon_xml(archive):
    """(id, version, addon.xml text) of an add-on zip, which holds one folder named after the id."""
    names = [n for n in archive.namelist() if n.count('/') == 1 and n.endswith('/addon.xml')]
    if len(names) != 1:
        raise SystemExit('{}: no <id>/addon.xml'.format(archive.filename))
    text = archive.read(names[0]).decode('utf-8')
    root = ET.fromstring(text)
    if root.get('id') + '/addon.xml' != names[0]:
        raise SystemExit('{}: the folder is not named after the add-on id'.format(archive.filename))
    return root.get('id'), root.get('version'), text


def repository_zip(base_url):
    """The repository add-on as a zip, pointing to base_url."""
    folder = os.path.join(ROOT, REPOSITORY)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(os.listdir(folder)):
            data = open(os.path.join(folder, name), 'rb').read()
            if name == 'addon.xml':
                data = data.replace(BASE_URL.encode(), base_url.encode())
            # a fixed date: the same files give the same zip, without changes for git
            info = zipfile.ZipInfo('{}/{}'.format(REPOSITORY, name), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return buffer.getvalue()


def add(out, data):
    """Copies an add-on zip (bytes) into out/zips/<id>/ with its icon; returns (id, version)."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        addon_id, version, text = addon_xml(archive)
        folder = os.path.join(out, 'zips', addon_id)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, '{}-{}.zip'.format(addon_id, version)), 'wb') as f:
            f.write(data)
        icon = ET.fromstring(text).find('.//assets/icon')
        if icon is not None and icon.text:
            target = os.path.join(folder, icon.text)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as f:
                f.write(archive.read('{}/{}'.format(addon_id, icon.text)))
    return addon_id, version


def write_index(out):
    """addons.xml and its md5 from the newest zip of every add-on in out/zips."""
    entries, newest = [], {}
    zips = os.path.join(out, 'zips')
    for addon_id in sorted(os.listdir(zips)):
        versions = [n[len(addon_id) + 1:-4] for n in os.listdir(os.path.join(zips, addon_id))
                    if n.startswith(addon_id + '-') and n.endswith('.zip')]
        if not versions:
            continue
        version = max(versions, key=version_key)
        newest[addon_id] = version
        with zipfile.ZipFile(os.path.join(zips, addon_id, '{}-{}.zip'.format(addon_id, version))) as archive:
            text = addon_xml(archive)[2]
        entries.append(re.sub(r'^<\?xml[^>]*\?>\s*', '', text.strip()))
    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n{}\n</addons>\n'.format('\n'.join(entries))
    with open(os.path.join(out, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(content)
    with open(os.path.join(out, 'addons.xml.md5'), 'w', encoding='utf-8') as f:
        f.write(hashlib.md5(content.encode('utf-8')).hexdigest())
    return newest


def write_start(out, repository_version):
    """The repository zip at the top, and index.html linking to it."""
    for name in os.listdir(out):
        if name.startswith(REPOSITORY + '-') and name.endswith('.zip'):
            os.remove(os.path.join(out, name))
    name = '{}-{}.zip'.format(REPOSITORY, repository_version)
    shutil.copy(os.path.join(out, 'zips', REPOSITORY, name), os.path.join(out, name))
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>jnegrel\'s Kodi add-ons</title></head>\n'
                '<body>\n<h1>jnegrel\'s Kodi add-ons</h1>\n'
                '<p>Install <a href="{0}">{0}</a> in Kodi (Add-ons &gt; Install from zip file), '
                'then the add-ons from it (Install from repository). '
                'See <a href="https://github.com/jnegrel/kodi-addons">github.com/jnegrel/kodi-addons</a>.</p>\n'
                '</body></html>\n'.format(html.escape(name)))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('zips', nargs='*', help='add-on zips to add')
    parser.add_argument('--base-url', default=BASE_URL)
    parser.add_argument('--out', default=ROOT)
    args = parser.parse_args()
    base_url = args.base_url if args.base_url.endswith('/') else args.base_url + '/'

    for path in args.zips:
        with open(path, 'rb') as f:
            print('added {} {}'.format(*add(args.out, f.read())))
    add(args.out, repository_zip(base_url))
    newest = write_index(args.out)
    write_start(args.out, newest[REPOSITORY])
    open(os.path.join(args.out, '.nojekyll'), 'w').close()  # GitHub Pages: serve the files as they are
    for addon_id, version in sorted(newest.items()):
        print('{} {}'.format(addon_id, version))


if __name__ == '__main__':
    main()
