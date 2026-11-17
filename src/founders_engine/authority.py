"""One-world authority boundary: Core151 IntegratedWorld and M01 Book gateway.

Not a second simulation engine; WorldBox adapters are observational only until
the material-identity and native-ACK protocol is independently validated.
"""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class AuthoritySnapshot:
    tick: int
    founder_count: int
    tree_count: int
    book_sequence: int
    book_mass_error: float
    book_energy_error: float

class SingleEngineSession:
    """Retains precisely one IntegratedWorld, Book, and advancing clock."""
    def __init__(self, world, tree_id):
        from founders_civ.experimental.world_integration import IntegratedWorld
        from founders_civ.experimental.worldbox_gateway_m01 import WorldBoxGatewayM01
        from founders_civ.core.ledger import Book
        if not isinstance(world, IntegratedWorld):
            raise TypeError('Core151 IntegratedWorld required, not a second simulation')
        if not isinstance(world.book, Book) or world.founders.book is not world.book:
            raise ValueError('World must use one canonical Book')
        if len(world.founders.people) != 100:
            raise ValueError('Founder identity registry must contain exactly 100 Founders')
        if tree_id not in world.world_trees.worlds:
            raise ValueError('unknown living World Tree')
        tree = world.world_trees.worlds[tree_id]
        if tree.sim is not world or tree.book is not world.book:
            raise ValueError('World Tree uses different resource authority')
        self.world = world
        self._founder_ids = frozenset(world.founders.people)
        self._founder_objects = dict(world.founders.people)
        self.book = world.book
        self._expected_tick = world.tick
        self._expected_book_sequence = world.book.seq
        self.tree_id = tree_id
        self.gateway = WorldBoxGatewayM01(tree)
        # If persistence fails after settlement, callers must discard this
        # in-memory session and recover from the last durable checkpoint.
        self._checkpoint_uncertain = False
        # A failed world step may have partially mutated the Book or actors.
        self._step_uncertain = False

    def _assert_authority(self):
        if self._checkpoint_uncertain:
            raise RuntimeError('checkpoint outcome uncertain: reload durable world')
        if self._step_uncertain:
            raise RuntimeError('simulation step outcome uncertain: reload durable world')
        # Equality alone accepts True == 1 and can miss ecology clock drift.
        # Reject invalid clocks before any session-mediated mutation.
        if (type(self.world.tick) is not int or self.world.tick < 0 or
                type(self.world.ecology.day) is not int or self.world.ecology.day < 0):
            raise RuntimeError('invalid canonical world clock')
        if self.world.tick != self._expected_tick or self.world.ecology.day != self.world.tick:
            raise RuntimeError('authoritative world clock changed outside session')
        if self.book.seq != self._expected_book_sequence:
            raise RuntimeError('canonical Book sequence changed outside session')
        if frozenset(self.world.founders.people) != self._founder_ids:
            raise RuntimeError('authoritative Founder identities changed')
        if any(actor is not self._founder_objects[fid]
               for fid, actor in self.world.founders.people.items()):
            raise RuntimeError('authoritative Founder object replaced')
        if self.world.founders.book is not self.book:
            raise RuntimeError('Founder registry Book authority changed')
        if self.world.book is not self.book:
            raise RuntimeError('Book authority changed')
        tree = self.world.world_trees.worlds[self.tree_id]
        if tree.book is not self.book or tree.sim is not self.world:
            raise RuntimeError('World Tree authority changed')

    def audit(self):
        self._assert_authority()
        proof = self.book.audit()
        # An undefined conservation audit must never be reported as healthy.
        if not all(isfinite(proof[key]) for key in ('mass_error', 'energy_error')):
            raise RuntimeError('non-finite canonical Book conservation audit')
        return AuthoritySnapshot(
            tick=self.world.tick,
            founder_count=len(self.world.founders.people),
            tree_count=len(self.world.world_trees.worlds),
            book_sequence=self.book.seq,
            book_mass_error=proof['mass_error'],
            book_energy_error=proof['energy_error'],
        )

    def step(self):
        self._assert_authority()
        before = self.world.tick
        try:
            result = self.world.step()
            if self.world.tick != before + 1:
                raise RuntimeError('non-monotonic or duplicated simulation clock')
            self._expected_tick = self.world.tick
            self._expected_book_sequence = self.book.seq
            self.audit()
        except Exception:
            # The engine may already have changed resources or actors.
            # Do not acknowledge another mutation until durable recovery.
            self._step_uncertain = True
            raise
        return result

    def harvest(self, founder_id, source_id, revision, habitat, material,
                quantity, chemical_energy=0.0):
        """Optional Book-funded tree inventory transfer, not measured game harvest."""
        self._assert_authority()
        before_sequence = self.book.seq
        try:
            receipt = self.gateway.founder_harvest(
                founder_id, source_id, revision, habitat, material,
                quantity, chemical_energy)
            self._expected_book_sequence = self.book.seq
            self.audit()
        except Exception:
            # Invalid pre-settlement requests may be retried, but an error
            # after Book mutation leaves the transaction outcome uncertain.
            if self.book.seq != before_sequence:
                self._checkpoint_uncertain = True
            raise
        return receipt

    def checkpointed_harvest(self, checkpoint_path, founder_id, source_id,
                             revision, habitat, material, quantity,
                             chemical_energy=0.0):
        """Settle synthetic M01 claim and durably checkpoint before returning.

        The returned receipt is only a LOCAL durable-settlement signal, never
        native WorldBox ACK. A failed checkpoint poisons this in-memory session:
        reload from the previous durable checkpoint and replay the same request
        ID. External WorldBox writes are prohibited. The Book remains sole
        resource authority; the checkpoint is its persisted representation.
        """
        from founders_engine.checkpoint import save_checkpoint
        self._assert_authority()
        receipt = self.harvest(founder_id, source_id, revision, habitat,
                               material, quantity, chemical_energy)
        try:
            save_checkpoint(self.world, self.tree_id, checkpoint_path)
        except Exception:
            # Settlement might exist only in RAM; do not permit further
            # mutations or a false durable ACK on this session.
            self._checkpoint_uncertain = True
            raise
        return receipt

    def attach_observer(self, observer):
        """Reject secondary clocks/writable ledgers; only read-only snapshot probes."""
        if any(hasattr(observer, attr) for attr in
               ('book', 'ledger', 'sqlite_book', 'clock', 'step', 'write')):
            raise ValueError('observer exposes independent state authority')
        if not callable(getattr(observer, 'snapshot', None)):
            raise TypeError('read-only snapshot method required')
        return observer
