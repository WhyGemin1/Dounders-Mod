"""Deterministic serialization-based continuity signature of live simulation."""
import hashlib,pickle
def signature(sim):
    return hashlib.sha256(pickle.dumps(sim,protocol=4)).hexdigest()
