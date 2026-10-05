#!/usr/bin/env python3
"""Download the CC0 assets build_house.py uses into blender/assets/.

  python3 /Users/rejoesudarsan/Dev/networker-space/blender/fetch_assets.py [--no-tree]

Sources: Poly Haven (api.polyhaven.com / dl.polyhaven.org) and ambientCG
(ambientcg.com). Both publish everything under CC0 1.0. Writes
assets/manifest.json (what build_house.py reads) and assets/LICENSES.md.
Already-downloaded files with the right size are skipped. Standard library only.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
UA = {"User-Agent": "space-house-blender-build/1.0"}

HDRI = "bryanston_park_sunrise"          # "soft pink sunrise ... calm dawn"
TREE = "jacaranda_tree"                  # spreading flowering-tree canopy (stands in for gulmohar)
# local name -> (source, asset id, real-world tile size in metres or None to read from the API)
TEXTURES = {
    "plaster":    ("polyhaven", "white_stucco", None),
    "teak":       ("polyhaven", "teak_veneer", None),
    "cladding":   ("polyhaven", "concrete_tile_facade", None),
    "sandstone":  ("polyhaven", "seaworn_stone_tiles", None),
    "terracotta": ("polyhaven", "terracotta_floor_tiles", None),
    "asphalt":    ("polyhaven", "asphalt_02", None),
    "steel":      ("ambientcg", "Metal027", 1.0),
}
PH_MAPS = {"color": "Diffuse", "roughness": "Rough", "normal": "nor_gl"}
ACG_MAPS = {"color": "_Color.jpg", "roughness": "_Roughness.jpg", "normal": "_NormalGL.jpg",
            "metalness": "_Metalness.jpg"}


def retry(fn, tries=4):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # flaky reads through proxies
            if i == tries - 1:
                raise
            print("  retry (%s)" % e)
            time.sleep(2 * (i + 1))


CURL = shutil.which("curl")


def fetch_bytes(url, timeout=60):
    if CURL:  # curl copes better with flaky proxies than urllib
        return subprocess.run([CURL, "-sSfL", "--retry", "3", "-m", str(timeout), "-A", UA["User-Agent"], url],
                              check=True, capture_output=True).stdout
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def get_json(url):
    return retry(lambda: json.loads(fetch_bytes(url)))


def download(url, path, size=None):
    if os.path.isfile(path) and (size is None or os.path.getsize(path) == size):
        print("  have", os.path.relpath(path, HERE))
        return os.path.getsize(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print("  get ", url)
    tmp = path + ".part"

    def go():
        if CURL:
            subprocess.run([CURL, "-sSfL", "--retry", "3", "-C", "-", "-m", "1800", "-A", UA["User-Agent"],
                            "-o", tmp, url], check=True)
        else:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        if size is not None and os.path.getsize(tmp) != size:
            raise IOError("short download %d / %d" % (os.path.getsize(tmp), size))
    retry(go)
    os.replace(tmp, path)
    return os.path.getsize(path)


def main():
    no_tree = "--no-tree" in sys.argv
    manifest = {"hdri": None, "textures": {}, "tree": None}
    licences = []

    # HDRI
    files = get_json("https://api.polyhaven.com/files/%s" % HDRI)["hdri"]["2k"]["hdr"]
    p = os.path.join(ASSETS, "hdri", "%s_2k.hdr" % HDRI)
    n = download(files["url"], p, files["size"])
    manifest["hdri"] = os.path.relpath(p, HERE)
    licences.append((HDRI + " (HDRI, 2K .hdr)", "https://polyhaven.com/a/" + HDRI, n))

    # Textures
    for name, (src, aid, size_m) in TEXTURES.items():
        d = os.path.join(ASSETS, "textures", name)
        entry = {"source": src, "id": aid, "maps": {}}
        total = 0
        if src == "polyhaven":
            info = get_json("https://api.polyhaven.com/info/%s" % aid)
            dims = info.get("dimensions") or [1000, 1000]
            entry["size_m"] = size_m or round(dims[0] / 1000.0, 3)
            files = get_json("https://api.polyhaven.com/files/%s" % aid)
            for key, ph in PH_MAPS.items():
                f = files[ph]["2k"]["jpg"]
                p = os.path.join(d, key + ".jpg")
                total += download(f["url"], p, f["size"])
                entry["maps"][key] = os.path.relpath(p, HERE)
            url = "https://polyhaven.com/a/" + aid
        else:
            entry["size_m"] = size_m
            z = os.path.join(d, "%s_2K-JPG.zip" % aid)
            total += download("https://ambientcg.com/get?file=%s_2K-JPG.zip" % aid, z)
            with zipfile.ZipFile(z) as zf:
                for key, suffix in ACG_MAPS.items():
                    member = next((m for m in zf.namelist() if m.endswith(suffix)), None)
                    if member is None:
                        continue
                    p = os.path.join(d, key + ".jpg")
                    with zf.open(member) as s, open(p, "wb") as t:
                        shutil.copyfileobj(s, t)
                    entry["maps"][key] = os.path.relpath(p, HERE)
            os.remove(z)
            url = "https://ambientcg.com/view?id=" + aid
        manifest["textures"][name] = entry
        licences.append(("%s -> textures/%s (2K: %s)" % (aid, name, ", ".join(entry["maps"])), url, total))

    # Tree model (glTF 1k: ~210 MB, mostly the .bin)
    if not no_tree:
        g = get_json("https://api.polyhaven.com/files/%s" % TREE)["gltf"]["1k"]["gltf"]
        d = os.path.join(ASSETS, "models", TREE)
        total = download(g["url"], os.path.join(d, "%s_1k.gltf" % TREE), g["size"])
        base = g["url"].rsplit("/", 1)[0]
        for rel, f in g.get("include", {}).items():
            total += download(f.get("url") or base + "/" + rel, os.path.join(d, rel), f["size"])
        manifest["tree"] = os.path.relpath(os.path.join(d, "%s_1k.gltf" % TREE), HERE)
        licences.append((TREE + " (model, glTF 1k)", "https://polyhaven.com/a/" + TREE, total))

    with open(os.path.join(ASSETS, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(ASSETS, "LICENSES.md"), "w") as f:
        f.write("# Third-party assets\n\n"
                "Downloaded by `blender/fetch_assets.py`. Every asset is **CC0 1.0 Universal** "
                "(public domain dedication): https://creativecommons.org/publicdomain/zero/1.0/\n\n"
                "- Poly Haven licence: https://polyhaven.com/license\n"
                "- ambientCG licence: https://docs.ambientcg.com/license/\n\n"
                "| asset | source | size on disk | licence |\n|---|---|---|---|\n")
        for what, url, n in licences:
            f.write("| %s | %s | %.1f MB | CC0 1.0 |\n" % (what, url, n / 1e6))
    print("wrote", os.path.join(ASSETS, "manifest.json"))


if __name__ == "__main__":
    main()
