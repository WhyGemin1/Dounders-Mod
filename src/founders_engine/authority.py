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
        self._ecology_object = world.ecology
        self._founder_registry_object = world.founders
        self._founder_ids = frozenset(world.founders.people)
        self._founder_objects = dict(world.founders.people)
        self.book = world.book
        self._expected_tick = world.tick
        self._expected_book_sequence = world.book.seq
        self.tree_id = tree_id
        # Pin the original living Tree object, not merely its registry key.
        self._tree_object = tree
        # Pin the Tree registry itself, not only the resident Tree entry.
        self._tree_registry_object = world.world_trees
        self.gateway = WorldBoxGatewayM01(tree)
        self._gateway_object = self.gateway
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
        if self.world.ecology is not self._ecology_object:
            raise RuntimeError('authoritative ecology object replaced')
        # Equality alone accepts True == 1 and can miss ecology clock drift.
        # Reject invalid clocks before any session-mediated mutation.
        if (type(self.world.tick) is not int or self.world.tick < 0 or
                type(self.world.ecology.day) is not int or self.world.ecology.day < 0):
            raise RuntimeError('invalid canonical world clock')
        if self.world.tick != self._expected_tick or self.world.ecology.day != self.world.tick:
            raise RuntimeError('authoritative world clock changed outside session')
        # bool compares equal to 0/1 in Python; sequence must be a real counter.
        if type(self.book.seq) is not int or self.book.seq < 0:
            raise RuntimeError('invalid canonical Book sequence')
        if self.book.seq != self._expected_book_sequence:
            raise RuntimeError('canonical Book sequence changed outside session')
        if self.world.founders is not self._founder_registry_object:
            raise RuntimeError('authoritative Founder registry object replaced')
        if frozenset(self.world.founders.people) != self._founder_ids:
            raise RuntimeError('authoritative Founder identities changed')
        if any(actor is not self._founder_objects[fid]
               for fid, actor in self.world.founders.people.items()):
            raise RuntimeError('authoritative Founder object replaced')
        if self.world.founders.book is not self.book:
            raise RuntimeError('Founder registry Book authority changed')
        if self.world.book is not self.book:
            raise RuntimeError('Book authority changed')
        if (self.gateway is not self._gateway_object or
                self.gateway.tree is not self._tree_object or
                self.gateway.sim is not self.world or
                self.gateway.book is not self.book):
            raise RuntimeError('M01 gateway authority changed')
        if self.world.world_trees is not self._tree_registry_object:
            raise RuntimeError('authoritative World Tree registry object replaced')
        # Missing registry entry is authority loss, not an incidental KeyError.
        if self.tree_id not in self.world.world_trees.worlds:
            raise RuntimeError('authoritative World Tree removed')
        tree = self.world.world_trees.worlds[self.tree_id]
        if tree is not self._tree_object:
            raise RuntimeError('authoritative World Tree object replaced')
        if tree.book is not self.book or tree.sim is not self.world:
            raise RuntimeError('World Tree authority changed')
        # Every registered Tree shares the same Book, not only the M01 target.
        # Otherwise a second Tree could introduce an untracked resource writer.
        if any(other.book is not self.book or other.sim is not self.world
               for other in self.world.world_trees.worlds.values()):
            raise RuntimeError('noncanonical World Tree resource authority')

    def audit(self):
        self._assert_authority()
        # Reject metadata drift before stepping the real world, even when
        # mass/energy totals still happen to balance. The Book is authoritative.
        history = getattr(self.book, 'transaction_history', None)
        if (not isinstance(history, list) or
                type(self.book.transactions) is not int or
                self.book.transactions != len(history) or
                type(self.book.toll_count) is not int or
                self.book.toll_count != sum(tx.kind == 'transform' for tx in history) or
                len(history) != self.book.seq or
                (history[-1] if history else None) != self.book.last):
            raise RuntimeError('canonical Book history metadata drift')
        proof = self.book.audit()
        # An undefined conservation audit must never be reported as healthy.
        # Boolean and nonnumeric audit results are not measured conservation residuals.
        # Reject them explicitly before tolerance comparisons or advancement.
        if not isinstance(proof, dict) or any(
                key not in proof for key in ('mass_error', 'energy_error')):
            raise RuntimeError('incomplete canonical Book conservation audit')
        if any(type(proof[key]) not in (int, float)
               for key in ('mass_error', 'energy_error')):
            raise RuntimeError('invalid canonical Book conservation audit type')
        if not all(isfinite(proof[key]) for key in ('mass_error', 'energy_error')):
            raise RuntimeError('non-finite canonical Book conservation audit')
        if any(abs(proof[key]) > 1e-6 for key in ('mass_error', 'energy_error')):
            raise RuntimeError('canonical Book conservation drift exceeds tolerance')
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
        # Preflight conservation before allowing the live engine to mutate.
        # A failed audit must not consume a tick or touch actor resources.
        self.audit()
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
        # Reject pre-existing conservation drift before invoking the M01 adapter.
        # A failed preflight must not create a new receipt or consume inventory.
        self.audit()
        before_sequence = self.book.seq
        # Validation failures are retryable only when the canonical Book is unchanged.
        from copy import deepcopy
        before_book = deepcopy((self.book.mass, self.book.energy,
                                self.book.transactions, self.book.transaction_history,
                                self.book.request_receipts, self.book.last,
                                self.book.external, self.book.toll_count))
        try:
            receipt = self.gateway.founder_harvest(
                founder_id, source_id, revision, habitat, material,
                quantity, chemical_energy)
            self._expected_book_sequence = self.book.seq
            self.audit()
        except Exception:
            # Invalid pre-settlement requests may be retried, but an error
            # after Book mutation leaves the transaction outcome uncertain.
            # A non-validation gateway failure can mutate balances or actor
            # state before the Book sequence advances. Sequence equality is
            # insufficient evidence of rollback; fail closed for such errors.
            # A rejected ValueError is retryable only if authority still audits.
            import sys
            failure = sys.exc_info()[1]
            after_book = deepcopy((self.book.mass, self.book.energy,
                                   self.book.transactions, self.book.transaction_history,
                                   self.book.request_receipts, self.book.last,
                                   self.book.external, self.book.toll_count))
            if (self.book.seq != before_sequence or before_book != after_book or
                    not isinstance(failure, ValueError)):
                self._checkpoint_uncertain = True
            else:
                try:
                    self.audit()
                except Exception:
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
