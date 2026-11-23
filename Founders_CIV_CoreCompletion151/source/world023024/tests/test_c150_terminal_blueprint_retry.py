"""C150: terminal World proposals must not permanently block autonomous retry."""
from types import SimpleNamespace
from founders_civ.core.founder_tree_agency import _own_blueprint


def test_terminal_blueprints_do_not_block_new_world_proposal():
    for stage in ("planted", "abandoned", "failed", "rejected", "cancelled"):
        sim = SimpleNamespace(seeds=SimpleNamespace(blueprints={
            "old": SimpleNamespace(author="F001", kind="world", stage=stage)
        }))
        assert _own_blueprint(sim, "F001") is None


def test_active_blueprint_remains_single_authoritative_proposal():
    sim = SimpleNamespace(seeds=SimpleNamespace(blueprints={
        "old": SimpleNamespace(author="F001", kind="world", stage="failed"),
        "other": SimpleNamespace(author="F002", kind="world", stage="draft"),
        "active": SimpleNamespace(author="F001", kind="world", stage="validated"),
    }))
    assert _own_blueprint(sim, "F001") is sim.seeds.blueprints["active"]
    assert _own_blueprint(sim, "F002") is sim.seeds.blueprints["other"]
