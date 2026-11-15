"""Trusted local extension resolution. Module imports can run arbitrary Python.
No remote loading or sandboxing; require explicit opt-in for external modules.
"""
from __future__ import annotations
import importlib
from .host import Extension,BUILTIN_EXTENSIONS
from .contracts import API_VERSION,CompatibilityError

def resolve_extensions(names, *, allow_local_code=False):
    result=[]
    for name in names:
        if name in BUILTIN_EXTENSIONS:
            result.append(BUILTIN_EXTENSIONS[name]())
            continue
        if not allow_local_code:
            raise CompatibilityError(f'extension {name!r} is not built-in; pass --allow-local-code only for reviewed local Python')
        if ':' not in name:raise CompatibilityError('extension must use module:Class syntax')
        module,klass=name.rsplit(':',1)
        obj=getattr(importlib.import_module(module),klass,None)
        if not isinstance(obj,type) or not issubclass(obj,Extension):raise CompatibilityError(f'{name}: must subclass Extension')
        result.append(obj())
    return tuple(result)
