"""Atomic trusted-local checkpoints for ONE Core151 IntegratedWorld.

Do not load untrusted pickle files. Not a WorldBox save or a second Book.
"""
from __future__ import annotations
import hashlib
import os
import pickle
import struct
import tempfile
from pathlib import Path

MAGIC = b'FOUNDERS-CIV-CORE151-CP1\n'
MAX_BYTES = 512 * 1024 * 1024

def _encode(payload: bytes) -> bytes:
    if len(payload) > MAX_BYTES:
        raise ValueError('checkpoint exceeds size limit')
    return MAGIC + struct.pack('>Q', len(payload)) + hashlib.sha256(payload).digest() + payload

def _decode(data: bytes) -> bytes:
    offset = len(MAGIC)
    if not data.startswith(MAGIC) or len(data) < offset + 40:
        raise ValueError('checkpoint format mismatch')
    size = struct.unpack('>Q', data[offset:offset + 8])[0]
    if size > MAX_BYTES or len(data) != offset + 40 + size:
        raise ValueError('checkpoint length mismatch')
    digest = data[offset + 8:offset + 40]
    payload = data[offset + 40:]
    if hashlib.sha256(payload).digest() != digest:
        raise ValueError('checkpoint digest mismatch')
    return payload

def _validate_world(world, tree_id):
    from founders_engine.authority import SingleEngineSession
    session = SingleEngineSession(world, tree_id)
    if world.tick != world.ecology.day:
        raise ValueError('ecology and Founder clocks disagree')
    session.audit()
    # Fail closed on Book receipt corruption before saving or accepting a
    # restored world. A receipt must refer to a real committed Book move.
    # The Book's resource accounts remain the only settlement authority.
    from founders_civ.core.ledger import Transaction
    receipts = getattr(session.book, 'request_receipts', None)
    if not isinstance(receipts, dict):
        raise ValueError('missing authoritative Book replay receipts')
    history = getattr(session.book, 'transaction_history', None)
    # Older checkpoints cannot prove historical replay receipts. Do not
    # fabricate a transaction history from balances or silently migrate.
    if history is None:
        raise ValueError('legacy checkpoint missing canonical Book transaction history; reviewed migration required')
    if (not isinstance(history, list) or len(history) != session.book.seq or
            any(not isinstance(tx, Transaction) or type(tx.seq) is not int or tx.seq != i or
                tx.kind not in {'move', 'ingest', 'transform', 'wellspring'} or
                not isinstance(tx.material, tuple) or not isinstance(tx.energy, tuple)
                for i, tx in enumerate(history, 1)) or
            (history[-1] if history else None) != session.book.last):
        raise ValueError('inconsistent canonical Book transaction history')
    # Historical transaction metadata is part of the canonical Book proof.
    # A valid checkpoint checksum cannot legitimize NaN/negative tolls or
    # forged external inflows. Only Wellspring may add external energy.
    import math
    for tx in history:
        if (any(isinstance(value, bool) or
                not isinstance(value, (int, float)) or
                not math.isfinite(value) or value < 0
                for value in (tx.toll, tx.external)) or
                (tx.kind != 'transform' and tx.toll != 0) or
                (tx.kind == 'transform' and tx.toll <= 0) or
                (tx.kind != 'wellspring' and tx.external != 0) or
                (tx.kind == 'wellspring' and tx.external <= 0)):
            raise ValueError('malformed canonical Book transaction metadata')
    # Reject malformed historical legs even when the transaction was not an
    # M01 receipt. A valid checkpoint digest is not proof of valid Book data.
    import math
    for tx in history:
        for legs in (tx.material, tx.energy):
            for leg in legs:
                if (not isinstance(leg, tuple) or len(leg) != 3 or
                        not isinstance(leg[0], str) or not isinstance(leg[1], str) or
                        not leg[0] or not leg[1] or leg[0] != leg[0].strip() or
                        leg[1] != leg[1].strip() or leg[0] == leg[1] or
                        isinstance(leg[2], bool) or
                        not isinstance(leg[2], (int, float)) or
                        not math.isfinite(leg[2]) or leg[2] <= 0):
                    raise ValueError('malformed canonical Book transaction leg')
    seen_sequences = set()
    for request_id, record in receipts.items():
        if (not isinstance(request_id, str) or not request_id.strip() or
                request_id != request_id.strip()):
            raise ValueError('invalid Book replay request id')
        if not isinstance(record, tuple) or len(record) != 2:
            raise ValueError('invalid Book replay record')
        legs, receipt = record
        if (not isinstance(legs, tuple) or len(legs) != 2
                or not isinstance(receipt, Transaction)
                or receipt.kind != 'move'
                or receipt.material != legs[0] or receipt.energy != legs[1]
                or receipt.seq < 1 or receipt.seq > session.book.seq):
            raise ValueError('inconsistent Book replay receipt')
        # Every receipt, including historical ones, must match its committed
        # transaction in this SAME authoritative Book.
        if receipt != history[receipt.seq - 1]:
            raise ValueError('receipt does not match canonical Book transaction history')
        if receipt.seq in seen_sequences:
            raise ValueError('duplicate Book settlement sequence')
        seen_sequences.add(receipt.seq)
    return session

def save_checkpoint(world, tree_id, path):
    """Save complete object graph and Book receipts, replacing one trusted local file."""
    _validate_world(world, tree_id)
    payload = pickle.dumps((tree_id, world), protocol=pickle.HIGHEST_PROTOCOL)
    data = _encode(payload)
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=dest.parent, prefix='.checkpoint-',
                                         suffix='.tmp', delete=False) as f:
            temp_path = f.name
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, dest)
        temp_path = None
        if hasattr(os, 'O_DIRECTORY'):
            fd = os.open(dest.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    finally:
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
    return hashlib.sha256(data).hexdigest()

def load_checkpoint(path, expected_tree_id=None):
    """Only read a trusted local file: pickle can execute code on deserialization."""
    dest = Path(path)
    if dest.stat().st_size > MAX_BYTES + len(MAGIC) + 40:
        raise ValueError('checkpoint exceeds size limit')
    payload = _decode(dest.read_bytes())
    tree_id, world = pickle.loads(payload)
    if expected_tree_id is not None and tree_id != expected_tree_id:
        raise ValueError('unexpected World Tree ID')
    return _validate_world(world, tree_id)
