"""Stable, opt-in compatibility layer for the WORLD-024 experimental engine.

This layer is NOT a replacement for the authoritative conservation ledger.
It exposes read-only snapshots and vetted scenario interventions.
"""
from .contracts import API_VERSION, ScenarioSpec, StressWindow, CompatibilityError
from .host import IntegrationHost, Extension, Observation, EventEnvelope
__all__ = ['API_VERSION', 'ScenarioSpec', 'StressWindow', 'CompatibilityError',
           'IntegrationHost','Extension','Observation','EventEnvelope']
