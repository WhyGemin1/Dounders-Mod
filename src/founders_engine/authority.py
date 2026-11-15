"""One-world authority boundary: Core151 IntegratedWorld and M01 Book gateway.

Not a second simulation engine; WorldBox adapters are observational only until
the material-identity and native-ACK protocol is independently validated.
"""
from dataclasses import dataclass

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
        self.book = world.book
        self.tree_id = tree_id
        self.gateway = WorldBoxGatewayM01(tree)

    def _assert_authority(self):
        if self.world.book is not self.book:
            raise RuntimeError('Book authority changed')
        tree = self.world.world_trees.worlds[self.tree_id]
        if tree.book is not self.book or tree.sim is not self.world:
            raise RuntimeError('World Tree authority changed')

    def audit(self):
        self._assert_authority()
        proof = self.book.audit()
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
        result = self.world.step()
        if self.world.tick != before + 1:
            raise RuntimeError('non-monotonic or duplicated simulation clock')
        self.audit()
        return result

    def harvest(self, founder_id, source_id, revision, habitat, material,
                quantity, chemical_energy=0.0):
        """Optional Book-funded tree inventory transfer, not measured game harvest."""
        self._assert_authority()
        receipt = self.gateway.founder_harvest(
            founder_id, source_id, revision, habitat, material,
            quantity, chemical_energy)
        self.audit()
        return receipt

    def attach_observer(self, observer):
        """Reject secondary clocks/writable ledgers; only read-only snapshot probes."""
        if any(hasattr(observer, attr) for attr in
               ('book', 'ledger', 'sqlite_book', 'clock', 'step', 'write')):
            raise ValueError('observer exposes independent state authority')
        if not callable(getattr(observer, 'snapshot', None)):
            raise TypeError('read-only snapshot method required')
        return observer
