"""Fail-closed reconciliation of M01 paused actor snapshots and M05 native events.

Read-only; no Soul or WorldBox mutation. This module does not certify live gameplay.
"""
def reconcile(snapshot, events):
    if not isinstance(snapshot, dict) or not isinstance(events, list):
        raise ValueError("invalid evidence")
    for key, expected in (("paused", True), ("world_loading", False), ("has_more", False),
                          ("offset", 0), ("missing_identity_count", 0),
                          ("duplicate_identity_count", 0)):
        if snapshot.get(key) != expected:
            raise ValueError("incomplete M01 snapshot")
    rows = snapshot.get("items")
    if not isinstance(rows, list) or snapshot.get("returned") != len(rows) or snapshot.get("matched") != len(rows):
        raise ValueError("inconsistent M01 actor count")
    ids = []
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("native_actor_id", "")).strip() or not str(row.get("asset_id", "")).strip():
            raise ValueError("invalid native actor identity")
        ids.append(str(row["native_actor_id"]).strip())
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate M01 identity")
    if snapshot.get("world_seed") is None:
        raise ValueError("missing world seed")
    known = set(ids)
    mapping, reverse = {}, {}
    last_seq = None
    session = world = None
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("invalid event")
        if event.get("kind") == "bridge_loss":
            raise ValueError("lost M05 observations")
        seq = event.get("seq")
        if type(seq) is not int or seq < 1 or (last_seq is not None and seq != last_seq + 1):
            raise ValueError("M05 sequence gap or duplicate")
        last_seq = seq
        sid, wid = event.get("session_id"), event.get("world_key")
        if not sid or not wid or wid == "UNBOUND":
            raise ValueError("unbound M05 event")
        if session is None:
            session, world = sid, wid
        elif (sid, wid) != (session, world):
            raise ValueError("mixed M05 session or world")
        if event.get("kind") not in ("nutrition_call", "resource_consume_call") or event.get("native_success") is not True:
            continue
        callback_id = str(event.get("actor_id", "")).strip()
        data_id = str(event.get("actor_data_id", "")).strip()
        if callback_id in ("", "-1", "None") or data_id not in known:
            raise ValueError("unresolved M01/M05 identity")
        if callback_id in mapping and mapping[callback_id] != data_id:
            raise ValueError("callback ID remapped")
        if data_id in reverse and reverse[data_id] != callback_id:
            raise ValueError("native actor ID remapped")
        mapping[callback_id] = data_id
        reverse[data_id] = callback_id
    return mapping


def reconcile_epoch(snapshot, events, checkpoint=None):
    """Bind a reconciled actor mapping to an explicit native-world epoch.

    A changed world seed or session cannot silently inherit actor identities.
    The caller must explicitly start a new epoch with checkpoint=None.
    Checkpoint is JSON-compatible and contains no game mutation or Soul awards.
    """
    mapping = reconcile(snapshot, events)
    if not events:
        raise ValueError("epoch requires native events")
    seed = snapshot["world_seed"]
    if type(seed) not in (int, str) or str(seed).strip() == "":
        raise ValueError("invalid world seed")
    session = events[0]["session_id"]
    world = events[0]["world_key"]
    if checkpoint is not None:
        if not isinstance(checkpoint, dict) or checkpoint.get("schema") != 1:
            raise ValueError("invalid epoch checkpoint")
        if (checkpoint.get("world_seed"), checkpoint.get("world_key"),
                checkpoint.get("session_id")) != (seed, world, session):
            raise ValueError("epoch boundary requires explicit reset")
        # C085: fail closed on replay or skipped sequences across batches.
        prior_seq = checkpoint.get("last_seq")
        if type(prior_seq) is not int or prior_seq < 1:
            raise ValueError("legacy checkpoint lacks sequence continuity")
        if type(events[0].get("seq")) is not int or events[0]["seq"] != prior_seq + 1:
            raise ValueError("replayed or skipped event batch")
        prior = checkpoint.get("mapping")
        if not isinstance(prior, dict):
            raise ValueError("invalid checkpoint mapping")
        for callback_id, native_id in mapping.items():
            if callback_id in prior and prior[callback_id] != native_id:
                raise ValueError("actor identity changed within epoch")
            if native_id in prior.values() and prior.get(callback_id) != native_id:
                raise ValueError("native identity reassigned within epoch")
        merged = dict(prior)
        merged.update(mapping)
    else:
        merged = dict(mapping)
    return {"schema": 1, "world_seed": seed, "world_key": world,
            "session_id": session, "mapping": merged, "last_seq": events[-1]["seq"]}
