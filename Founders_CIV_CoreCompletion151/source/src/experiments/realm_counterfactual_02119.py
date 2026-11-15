"""Isolated, deterministic causal counterfactual snapshots."""
import copy,hashlib,pickle

def clone(sim):
    result=copy.deepcopy(sim)
    if result.host.book is sim.host.book:
        raise RuntimeError('Clone shares authoritative Book')
    return result

def digest(sim):
    # Full serialized state detects differences in Book, actor and ecological state.
    snapshot=copy.deepcopy(sim)
    # Migration cooldown is a policy input, not an instantaneous physical state.
    snapshot.bridge.tree.migration_cooldown_days=0
    return hashlib.sha256(pickle.dumps(snapshot,protocol=4)).hexdigest()
