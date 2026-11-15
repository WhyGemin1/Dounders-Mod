"""Deterministic import of the ONE verified Core151/Cycle152 engine.

Requires authorized ZIP bytes locally. Does not download, overwrite, or
install unrelated historical engines, proprietary game binaries or saves.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

SOURCE_SHA256 = "29c6bc0a650a6b3c48d3f7cdc2ab49e94592f6243cdfc36a168416b514a54cd8"
ROOT = "Founders_CIV_CoreCompletion151/source/world023024/"
SOURCES = ("founders_civ/", "knowledge_architecture.py", "run_world_tree_pilot.py")
MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 15_000_000
MAX_FILES = 128


def digest(data):
    return hashlib.sha256(data).hexdigest()


def plan(archive):
    data = Path(archive).read_bytes()
    actual = digest(data)
    if actual != SOURCE_SHA256:
        raise ValueError("Source archive fingerprint mismatch: " + actual)
    entries = {}
    total = 0
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name = info.filename
            if not name.startswith(ROOT) or not name.endswith(".py"):
                continue
            relative = name[len(ROOT):]
            if not (relative.startswith(SOURCES[0]) or relative in SOURCES[1:]):
                continue
            if (relative.startswith("/") or "\\" in relative or
                    any(not part or part in (".", "..") for part in relative.split("/"))):
                raise ValueError("unsafe archive path: " + relative)
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError("symlink source forbidden: " + relative)
            if relative in entries:
                raise ValueError("duplicate source member: " + relative)
            if len(entries) >= MAX_FILES or info.file_size > MAX_FILE_BYTES:
                raise ValueError("source member exceeds import limit")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("source tree exceeds import limit")
            raw = z.read(info)
            if len(raw) != info.file_size:
                raise ValueError("source size mismatch: " + relative)
            entries[relative] = raw
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
    if target.is_symlink():
        raise ValueError("destination root is a symlink")
    for name in entries:
        cursor = target
        for part in PurePosixPath(name).parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise ValueError("destination contains symlink: " + str(cursor))
    conflicts = [str(target / name) for name, raw in entries.items()
                 if (target / name).exists() and (target / name).read_bytes() != raw]
    if conflicts:
        raise FileExistsError("Refusing to overwrite modified source: " + repr(conflicts))
    manifest = {"archive_sha256": SOURCE_SHA256, "source_prefix": ROOT,
                "authority": "founders_civ.experimental.world_integration.IntegratedWorld",
                "book": "IntegratedWorld.book", "clock": "IntegratedWorld.tick",
                "files": {name: digest(raw) for name, raw in sorted(entries.items())}}
    manifest_path = target / "CORE151_SOURCE_MANIFEST.json"
    if manifest_path.is_symlink():
        raise ValueError("manifest destination is a symlink")
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise FileExistsError("existing manifest differs")
    if not dry_run:
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
