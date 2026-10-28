# FHD_Autopilot — source for Nexus Mods review

**Verified on 28 October 2026: all 31 runtime files rebuild from editable source with exactly the original SHA-256 hashes.** The complete build requires Python 3.10+ and its standard library. No Windows tools, game installation, precompiled script or original DAT/GI binaries are needed.

The supplied module declares **version 2.02**, author **Prolog_D**, installation at `Mods/FHD_MODS/FHD_Autopilot`, and no explicit dependencies or conflicts. Those metadata values and the runtime contents remain unchanged.

## Contents

| Path | Purpose |
| --- | --- |
| `source/CFG/Main.json` | Full Main DAT tree, UI actions, startup hooks and registration |
| `source/CFG/CacheData.json` | All resource aliases and paths |
| `source/CFG/Rus/Lang.json` | Full language data and the main autopilot runtime code |
| `source/script/Mod_FHD_Autopilot_Controller.rson` | Reconstructed SCR controller source and definitions |
| `source/script/Mod_FHD_Autopilot_Controller.layout.json` | Typed field order referring to RSON objects |
| `source/DATA/UI/*.json` | Exact sources for all 26 GI images: pixels, alpha, RLE and geometry |
| `source/ModuleInfo.txt` | UTF-8 metadata, rebuilt in the original CP1251 encoding |
| `scripts/` | DAT, GI and SCR encoders, complete builder and independent SCR inspector |
| `tests/` | Complete source-only build, hash checks and code-edit checks |
| `original-file-sha256.json` | Original runtime hashes |
| `build-verification.json` | Completed verification report and tool versions |
| `.github/workflows/build.yml` | GitHub source-build workflow |

Original runtime binaries, screenshot `АВТОПИЛОТ.bmp`, and duplicate/inconsistent text exports are excluded from this compact review package. No DLL or EXE was present in the input mod.

## Build and verify

```sh
python3 scripts/build.py --strict-original
python3 -m unittest discover -s tests -v
```

Verified with Python 3.12.14 and zlib 1.3.2. Outputs are `dist/FHD_Autopilot_FROM_SOURCE.zip` and `dist/build-report.json`. The ZIP installs at `Mods/FHD_MODS/FHD_Autopilot`.

The first command rebuilds three DAT files, one SCR, 26 GI images and ModuleInfo, checks their hashes and ZIP integrity, and verifies local CacheData resource paths. All 26 CacheData references resolve to rebuilt files. The tests include a separate temporary-directory build containing only source, build scripts and the reference manifest.

For deliberate source changes, omit `--strict-original`; the report lists changed hashes. GitHub hosted execution was not performed during this preparation session.

## Important source provenance

The upload contained `SOURCE/CFG/Main.txt` and `SOURCE/CFG/Rus/Lang.txt`, but their parameter/code contents do **not** match the provided DAT binaries. Differences include the compiled version's pause-request handling and UI button code. They are therefore excluded as duplicate, inconsistent inputs. The authoritative JSON sources in this repository were recovered from the actual supplied DATs and reproduce those DATs byte-for-byte.

All runtime code embedded in the DATs is visible in JSON parameter strings. The larger autopilot implementation is under `Script.FHDAutopilot` in `Lang.json`; the small controller SCR implements the incoming-dialog override. No source-edit operation is delegated to the mod author or reviewer before the provided build can run.

## Recovered controller

The complete original SCR8 is 1,117 bytes. All bytes were parsed: zero global variables, four local records, one star with one planet and ship requirement, one player group, one state, one dialog, and the global/init/turn/dialog event texts. No opaque executable payload remains.

SCR8 stores source strings and typed definitions; the game compiles that language when loading the script. The included Python serializer reads code and data from RSON objects according to the explicit layout. Each layout record is a primitive, field reference, or structural constant. Global/local offsets are recalculated automatically.

The visual coordinates were regenerated. RSON structural validation with SRHD-XenoModKit 0.10.4 completed with **zero issues**. RScript's own opening/recompilation was not executed. The verified source-build path is the included Python serializer; it is specific to this recovered runtime model and is not a general RScript visual-graph compiler. Adding/removing graph objects requires updating the typed layout; edits to mapped existing fields are consumed directly by the build.

## Format sources and limits

The previously supplied engine research, particularly [SpaceRangersHD_decomp](https://github.com/pakompom/SpaceRangersHD_decomp) `aScript.pas`, `EC_Expression.pas` and `EC_Buf.pas`, informed SCR8 layout and string handling. RSON examples and [SRHD-XenoModKit](https://github.com/Xenomorphchyma/SRHD-XenoModKit) 0.10.4 informed structural and GI checking. The independent DAT codec follows format conventions studied in Sergei Osminin's MIT-licensed [rangers-utils](https://github.com/murgesku/rangers-utils). No third-party binary tools are bundled and no new license is assigned to the mod.

Input archive SHA-256: `d00d481cf2fd313485b9b4abd5d6da811779f6cea1ba8254820592096ac8a264`. Although named `FHD_Autopilot.rar`, it is structurally a ZIP archive and passed its CRC checks.

Byte identity establishes preservation of the supplied mod. Game execution, in-game CodeEC compilation, gameplay behavior, antivirus verdicts and Nexus moderation approval were not performed or claimed.
