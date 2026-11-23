"""Versioned DTOs and strict input checks for experiment compatibility."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from math import isfinite
import json
from pathlib import Path

API_VERSION = '1.0'
SUPPORTED_BRANCHES = ('SOCIAL-021','WORLD-022','WORLD-023','WORLD-024')
GOVERNANCE = frozenset(('collective','owner','fragmented','none'))
EXTRACTION = frozenset(('careful','intensive','none'))
SOCIAL_MODES = frozenset(('full','no_partner','no_teach','no_faction','neutral_trust','isolated'))

class CompatibilityError(ValueError):
    """Unsupported extension schema or release contract."""

@dataclass(frozen=True)
class StressWindow:
    start: int = 0
    end: int | None = None
    upkeeps: float = 1.
    rainfall: float = 1.
    disease: float = 0.
    founder_drain: float = 0.

    def __post_init__(self):
        if not isinstance(self.start,int) or isinstance(self.start,bool) or self.start<0:
            raise ValueError('stress.start must be nonnegative integer')
        if self.end is not None and (not isinstance(self.end,int) or isinstance(self.end,bool) or self.end<=self.start):
            raise ValueError('stress.end must be greater than start')
        for key in ('upkeeps','rainfall','disease','founder_drain'):
            v=getattr(self,key)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) or v<0:
                raise ValueError(f'invalid stress.{key}')
        if self.disease>1: raise ValueError('disease probability above 1')

    @classmethod
    def from_dict(cls, data: dict[str,Any]):
        _strict(data, set(cls.__dataclass_fields__), 'stress')
        return cls(**data)

@dataclass(frozen=True)
class ScenarioSpec:
    schema_version: str = API_VERSION
    seed: int = 820
    cycles: int = 30
    governance: str = 'collective'
    extraction: str = 'careful'
    allow_private: bool = False
    social_mode: str = 'full'
    stress: tuple[StressWindow,...] = ()
    extensions: tuple[str,...] = ('event_tally','tree_watch')

    def __post_init__(self):
        if self.schema_version!=API_VERSION:raise CompatibilityError(f'expected API {API_VERSION}, got {self.schema_version}')
        if not isinstance(self.seed,int) or isinstance(self.seed,bool):raise ValueError('seed must be integer')
        if not isinstance(self.cycles,int) or isinstance(self.cycles,bool) or not 0<=self.cycles<=19997:raise ValueError('invalid cycles')
        if self.governance not in GOVERNANCE:raise ValueError('unknown governance')
        if self.extraction not in EXTRACTION:raise ValueError('unknown extraction')
        if self.social_mode not in SOCIAL_MODES:raise ValueError('unknown social_mode')
        if not isinstance(self.allow_private,bool):raise ValueError('allow_private must be bool')
        if any(not isinstance(s,StressWindow) for s in self.stress):raise ValueError('invalid stress entry')
        if not isinstance(self.extensions,tuple) or any(not isinstance(e,str) or not e for e in self.extensions):
            raise ValueError('invalid extensions')

    @classmethod
    def from_dict(cls, data: dict[str,Any]):
        _strict(data, set(cls.__dataclass_fields__), 'scenario')
        d=dict(data)
        d['stress']=tuple(StressWindow.from_dict(x) for x in d.get('stress',()))
        d['extensions']=tuple(d.get('extensions',('event_tally','tree_watch')))
        return cls(**d)

    @classmethod
    def from_file(cls, path: str | Path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding='utf8')))

    def to_dict(self):
        return asdict(self)


def _strict(data, permitted, label):
    if not isinstance(data,dict):raise ValueError(f'{label} must be JSON object')
    keys=set(data)-permitted
    if keys:raise ValueError(f'unknown {label} fields: {sorted(keys)}')
