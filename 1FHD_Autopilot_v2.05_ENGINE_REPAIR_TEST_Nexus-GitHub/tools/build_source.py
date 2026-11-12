#!/usr/bin/env python3
"""Export original FHD_Autopilot v2.05 game resources into editable sources.
Rebuilds a ZIP without touching the game or adding hooks/DLLs.
"""
from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

import dat_codec

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "install" / "FHD_Autopilot_v2.05_ENGINE_REPAIR_TEST.zip"
PREFIX = "Mods/FHD_MODS/FHD_Autopilot/"
SHA256 = "4207a89eee9690403e135bffd18647654a035d28f681d3db213b0cb376ad7753"
DAT = ["CFG/CacheData.dat", "CFG/Main.dat", "CFG/Rus/Lang.dat"]
TXT = ["SOURCE/CacheData.txt", "SOURCE/Main.txt", "SOURCE/Lang.txt"]
SCR = "DATA/Script/Mod_FHD_Autopilot_Controller.scr"
MODINFO = "ModuleInfo.txt"
UI = "DATA/UI/"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def kit(*arguments):
    subprocess.run([sys.executable, "-m", "srhd_modkit", *map(str, arguments)],
                   check=True, stdout=subprocess.DEVNULL)

def check_archive():
    assert ARCHIVE.is_file(), str(ARCHIVE)
    assert digest(ARCHIVE.read_bytes()) == SHA256, "Original ZIP SHA256 mismatch"
    with ZipFile(ARCHIVE) as z:
        assert z.testzip() is None, "Damaged ZIP"
        names = z.namelist()
        assert len(names) == 37 and len(names) == len(set(names)), "Unexpected ZIP entries"
        assert all(n.startswith(PREFIX) and ".." not in Path(n).parts for n in names)
        gi = sorted(n for n in names if n.endswith(".gi"))
        assert len(gi) == 29, "Expected 29 GI"
        expected = {PREFIX + n for n in [*DAT, *TXT, MODINFO, SCR]}
        assert set(names) == expected | set(gi), "Unexpected or missing game files"
        return gi

def export():
    gi_names = check_archive()
    if (ROOT / "SOURCE_HASHES.json").exists():
        print("Source already exists; preserving any user edits")
        return
    original = {}
    editable = {}
    with ZipFile(ARCHIVE) as z, tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        gis = []
        for name in z.namelist():
            raw = z.read(name)
            original[name] = {"bytes": len(raw), "sha256": digest(raw)}
            rel = name[len(PREFIX):]
            if rel in DAT:
                fmt = "cachedata" if rel == "CFG/CacheData.dat" else "blockpar"
                obj = dat_codec.decode(raw, fmt)
                assert dat_codec.encode(obj) == raw, "DAT roundtrip mismatch: " + rel
                export_rel = "SOURCE/DAT_JSON/" + rel + ".json"
                value = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            elif rel in TXT:
                export_rel = "SOURCE/ORIGINAL_TEXT/" + Path(rel).name
                value = raw
                assert value.decode("utf-8").encode("utf-8") == raw
            elif rel == MODINFO:
                export_rel = "SOURCE/ModuleInfo.utf8.txt"
                value = raw.decode("cp1251").encode("utf-8")
                assert value.decode("utf-8").encode("cp1251") == raw
            elif rel == SCR:
                export_rel = "SOURCE/ORIGINAL_SCRIPT/" + Path(rel).name
                value = raw
            elif rel.startswith(UI) and rel.endswith(".gi"):
                export_rel = "SOURCE/ORIGINAL_GI/" + Path(rel).name
                value = raw
                gi_path = tmp / Path(rel).name
                gi_path.write_bytes(raw)
                gis.append(gi_path)
            else:
                raise RuntimeError("Unrecognized game resource: " + rel)
            target = ROOT / export_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
            editable[export_rel] = digest(value)
        assert len(gis) == len(gi_names) == 29
        png_dir = ROOT / "SOURCE/PNG"
        png_dir.mkdir(parents=True, exist_ok=True)
        kit("convert", "gi-png", *gis, "--output", png_dir)
        for gi in gis:
            png = png_dir / (gi.stem + ".png")
            assert png.is_file(), "GI conversion did not produce " + str(png)
            assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            editable["SOURCE/PNG/" + png.name] = digest(png.read_bytes())
        assert len(editable) == 66, "Unexpected source file count: " + str(len(editable))
    (ROOT / "ORIGINAL_FILE_SHA256.json").write_text(
        json.dumps(original, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "SOURCE_HASHES.json").write_text(
        json.dumps(editable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Exported", len(editable), "source/editable files from 37 game resources")

def build(verify=False):
    check_archive()
    source_hashes = json.loads((ROOT / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    updates = {}
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        edited_gi = set()
        edited_png = set()
        for rel, original_hash in source_hashes.items():
            data = (ROOT / rel).read_bytes()
            if digest(data) == original_hash:
                continue
            if rel.startswith("SOURCE/DAT_JSON/") and rel.endswith(".dat.json"):
                game = rel.removeprefix("SOURCE/DAT_JSON/").removesuffix(".json")
                assert game in DAT
                obj = json.loads(data.decode("utf-8"))
                assert obj["format"] == ("cachedata" if game == "CFG/CacheData.dat" else "blockpar")
                updates[PREFIX + game] = dat_codec.encode(obj)
            elif rel.startswith("SOURCE/ORIGINAL_TEXT/"):
                game = "SOURCE/" + Path(rel).name
                assert game in TXT
                updates[PREFIX + game] = data
            elif rel == "SOURCE/ModuleInfo.utf8.txt":
                updates[PREFIX + MODINFO] = data.decode("utf-8").encode("cp1251")
            elif rel.startswith("SOURCE/ORIGINAL_SCRIPT/"):
                assert Path(rel).name == Path(SCR).name
                updates[PREFIX + SCR] = data
            elif rel.startswith("SOURCE/ORIGINAL_GI/"):
                name = Path(rel).name
                edited_gi.add(name)
                updates[PREFIX + UI + name] = data
            elif rel.startswith("SOURCE/PNG/"):
                name = Path(rel).with_suffix(".gi").name
                edited_png.add(name)
                converted = tmp / Path(name).stem
                converted.mkdir()
                kit("convert", "png-gi", ROOT / rel, "--mode", "2", "--output", converted)
                updates[PREFIX + UI + name] = (converted / name).read_bytes()
            else:
                raise ValueError("Unknown source path: " + rel)
        if edited_gi & edited_png:
            raise RuntimeError("Same GI and PNG edited together: " + str(edited_gi & edited_png))
        dist = ROOT / "DIST"
        dist.mkdir(exist_ok=True)
        result = dist / ARCHIVE.name
        if not updates:
            shutil.copyfile(ARCHIVE, result)
        else:
            with ZipFile(ARCHIVE) as original, ZipFile(result, "w") as output:
                for info in original.infolist():
                    output.writestr(info, updates.get(info.filename, original.read(info.filename)))
        with ZipFile(ARCHIVE) as original, ZipFile(result) as rebuilt:
            assert rebuilt.testzip() is None
            assert original.namelist() == rebuilt.namelist()
            for name in original.namelist():
                if name not in updates:
                    assert rebuilt.read(name) == original.read(name), "Unexpected change: " + name
        if verify and not updates:
            assert digest(result.read_bytes()) == SHA256, "Clean ZIP rebuild differs"
        print("Rebuilt:", result, "changed runtime files:", len(updates), "SHA256:", digest(result.read_bytes()))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.export:
        export()
    else:
        build(verify=args.verify)
