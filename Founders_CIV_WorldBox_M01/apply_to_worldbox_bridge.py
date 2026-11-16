#!/usr/bin/env python3
"""Safely add the M01 read-only command to user's local worldbox-mcp fork.

Does not clone, install BepInEx, touch the WorldBox installation, or run code.
"""
from pathlib import Path
import argparse,shutil

TARGET='registry.Register(new QueryActorsCommand(worldAccess));'
ADDED='registry.Register(new QueryActorIdentitiesCommand(worldAccess));'
REL='mod/src/WorldBoxBridge/Commands/Read/QueryActorIdentitiesCommand.cs'

def apply(repo_dir,template=None):
    repo=Path(repo_dir).resolve()
    plugin=repo/'mod/src/WorldBoxBridge/Plugin.cs'
    query=repo/'mod/src/WorldBoxBridge/Commands/Read/QueryActorsCommand.cs'
    new_command=repo/REL
    template=Path(template or Path(__file__).parent/'worldbox_patch/QueryActorIdentitiesCommand.cs')
    if not plugin.is_file() or not query.is_file():
        raise FileNotFoundError('Not a compatible worldbox-mcp checkout: expected Plugin.cs and QueryActorsCommand.cs')
    text=plugin.read_text(encoding='utf8');source=template.read_text(encoding='utf8')
    if TARGET not in text:raise ValueError('Expected query command registration not present; upstream changed, review manually')
    # Only known M01 migration: the previous reviewed command was identical
    # except for its missing BridgeRejectionException namespace import.
    # Do NOT overwrite a locally edited/unknown version.
    namespace_line='using WorldBoxBridge.Commands.Action;\\n'
    if source.count(namespace_line)!=1:
        raise ValueError('Reviewed M01 template namespace invariant failed')
    previous=source.replace(namespace_line,'')
    migrated=False
    if new_command.exists():
        existing=new_command.read_text(encoding='utf8')
        if existing!=source:
            if existing!=previous:
                raise ValueError('Existing M01 command differs from both reviewed versions: refusing to overwrite. Inspect local diff.')
            backup=new_command.with_name(new_command.name+'.before-namespace-fix.bak')
            if backup.exists():
                if backup.read_text(encoding='utf8')!=previous:
                    raise ValueError('M01 legacy backup exists with unexpected bytes; refusing migration')
            else:
                shutil.copy2(new_command,backup)
            new_command.write_text(source,encoding='utf8')
            migrated=True
    if ADDED in text:
        if not new_command.exists():raise ValueError('Plugin registers new command but its source is missing')
        return 'migrated reviewed legacy M01 namespace import; previous command backed up' if migrated else 'already applied'
    if text.count(TARGET)!=1:raise ValueError('Found multiple query registrations; refusing to guess')
    backup=plugin.with_name('Plugin.cs.M01_backup')
    if backup.exists():raise FileExistsError('Backup already exists but patch absent; review before retrying')
    shutil.copy2(plugin,backup)
    new_command.write_text(source,encoding='utf8')
    plugin.write_text(text.replace(TARGET,TARGET+'\n        '+ADDED),encoding='utf8')
    return f'patched; original Plugin.cs saved to {backup.name}'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('worldbox_mcp_checkout')
    args=p.parse_args();print(apply(args.worldbox_mcp_checkout))
