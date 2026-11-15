"""Process-local exclusive source edit lease; not distributed coordination."""
from contextlib import contextmanager
from pathlib import Path
import os

@contextmanager
def exclusive_source_edit(root, owner):
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    lock=root/'.source_edit.lock'
    
    try:
        fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as exc:
        raise RuntimeError('Source-edit lease already held') from exc
    try:
        os.write(fd,str(owner).encode());os.fsync(fd)
        yield lock
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)
