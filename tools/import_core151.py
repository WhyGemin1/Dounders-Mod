"""Deterministic import of the ONE verified Core151/Cycle152 engine.

Requires authorized ZIP bytes locally. Does not download, overwrite, or
install unrelated historical engines, proprietary game binaries or saves.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SOURCE_SHA256 = "29c6bc0a650a6b3c48d3f7cdc2ab49e94592f6243cdfc36a168416b514a54cd8"
ROOT = "Founders_CIV_CoreCompletion151/source/world023024/"
SOURCES = ("founders_civ/", "knowledge_architecture.py", "run_world_tree_pilot.py")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def plan(archive):
    data = Path(archive).read_bytes()
    actual = digest(data)
    if actual != SOURCE_SHA256:
        raise ValueError("Source archive fingerprint mismatch: " + actual)
    entries = {}
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.startswith(ROOT) or not name.endswith(".py"):
                continue
            relative = name[len(ROOT):]
            if not (relative.startswith(SOURCES[0]) or relative in SOURCES[1:]):
                continue
            if ".." in Path(relative).parts or relative.startswith("/"):
                raise ValueError("unsafe path: " + relative)
            entries[relative] = z.read(name)
    required = ("founders_civ/core/ledger.py",
                "founders_civ/core/engine.py",
                "founders_civ/experimental/world_integration.py",
                "knowledge_architecture.py", "run_world_tree_pilot.py")
    missing = set(required) - set(entries)
    if missing:
        raise ValueError("missing engine dependencies: " + repr(sorted(missing)))
    return entries


def install(archive, destination, dry_run=False):
    entries = plan(archive)
    target = Path(destination)
    conflicts = [str(target / name) for name, raw in entries.items()
                 if (target / name).exists() and (target / name).read_bytes() != raw]
    if conflicts:
        raise FileExistsError("Refusing to overwrite modified source: " + repr(conflicts))
    manifest = {"archive_sha256": SOURCE_SHA256, "source_prefix": ROOT,
                "authority": "founders_civ.experimental.world_integration.IntegratedWorld",
                "book": "IntegratedWorld.book", "clock": "IntegratedWorld.tick",
                "files": {name: digest(raw) for name, raw in sorted(entries.items())}}
    if not dry_run:
        manifest_path = target / "CORE151_SOURCE_MANIFEST.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
            raise FileExistsError("existing manifest differs")
        for name, raw in sorted(entries.items()):
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(raw)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("destination")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = install(args.archive, args.destination, args.dry_run)
    print(json.dumps({"files": len(result["files"]), "archive_sha256": SOURCE_SHA256,
                      "dry_run": args.dry_run}))


if __name__ == "__main__":
    main()
