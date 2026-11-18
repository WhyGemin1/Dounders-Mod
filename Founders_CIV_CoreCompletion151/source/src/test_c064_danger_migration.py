"""C064: defensive actions must not trigger opportunistic migration."""
from types import SimpleNamespace
from core_physiology_v2 import PhysiologyBridgeV2


class _Actor:
    species = "red_fox"
    stage = "adult"
    habitat = "forest"


class _NoAccess:
    def __getattr__(self, key):
        raise AssertionError(f"defensive migration accessed {key}")


def test_hide_never_enters_migration_path():
    assert PhysiologyBridgeV2._migrate(_NoAccess(), _Actor(), "hide") is False


def test_defend_never_enters_migration_path():
    assert PhysiologyBridgeV2._migrate(_NoAccess(), _Actor(), "defend") is False


def test_sleep_never_enters_migration_path():
    assert PhysiologyBridgeV2._migrate(_NoAccess(), _Actor(), "sleep") is False


def test_search_still_can_enter_migration_path():
    bridge = SimpleNamespace(
        tree=SimpleNamespace(habitats={"forest": SimpleNamespace(neighbors=[])}),
        eco_flags=SimpleNamespace(spatial=False),
    )
    assert PhysiologyBridgeV2._migrate(bridge, _Actor(), "search") is False
