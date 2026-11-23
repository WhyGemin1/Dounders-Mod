"""C182: malformed Tree lot observations must fail closed without touching Book."""
from collections import defaultdict
from types import SimpleNamespace
from founders_civ.core.founder_harvesting import observed_lots


def tree(lots, maturity_days=3):
    return SimpleNamespace(
        id="WORLD-024", age=10,
        provisioning=SimpleNamespace(lots=lots, maturity_days=maturity_days),
        book=SimpleNamespace(mass=defaultdict(float)),
    )


def test_missing_or_invalid_lot_collection():
    for lots in (None, [], "corrupt", 17):
        assert observed_lots(tree(lots)) == []


def test_corrupted_lot_records_are_skipped():
    lots = {
        "missing": None,
        "number": 7,
        "string": "mature",
        42: SimpleNamespace(kind="food", created=1, state="stored"),
        "future": SimpleNamespace(kind="food", created=11, state="stored"),
    }
    assert observed_lots(tree(lots)) == []


def test_invalid_fruit_maturity_configuration_fails_closed():
    record = SimpleNamespace(kind="fruit", created=1, state="mature")
    for days in (None, True, 2.5, -1, "3"):
        assert observed_lots(tree({"fruit-a": record}, days)) == []


def test_valid_food_and_mature_fruit_remain_observable():
    lots = {
        "food-a": SimpleNamespace(kind="food", created=1, state="stored"),
        "fruit-a": SimpleNamespace(kind="fruit", created=5, state="mature"),
    }
    t = tree(lots)
    t.book.mass["portable_food:lot:food-a:tree:WORLD-024"] = 1
    t.book.mass["fruit:lot:fruit-a:tree:WORLD-024"] = 1
    assert [(x["lot"], x["kind"]) for x in observed_lots(t)] == [
        ("food-a", "food"), ("fruit-a", "fruit")
    ]
