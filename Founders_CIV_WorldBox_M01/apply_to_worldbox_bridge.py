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
    if new_command.exists() and new_command.read_text(encoding='utf8')!=source:
        raise ValueError('Existing M01 command differs: refusing to overwrite')
    if ADDED in text:
        if not new_command.exists():raise ValueError('Plugin registers new command but its source is missing')
        return 'already applied'
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
