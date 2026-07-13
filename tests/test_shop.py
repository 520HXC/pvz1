from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from adventure_levels import SHOP_UPGRADE_PLANT_KEYS
from progression import SAVE_VERSION


try:
    from shop import (
        SHOP_CATALOG,
        ShopCatalog,
        ShopItem,
        ShopPurchaseStatus,
        prepare_shop_purchase,
    )

    SHOP_AVAILABLE = True
except ImportError:
    SHOP_AVAILABLE = False


def test_shop_api_exists():
    assert SHOP_AVAILABLE, "shop purchase API is required"


requires_shop = pytest.mark.skipif(not SHOP_AVAILABLE, reason="shop API not implemented yet")


def make_save(**overrides):
    saved = {
        "save_version": SAVE_VERSION,
        "coins": 2000,
        "upgrades": {},
        "cleared_levels": ["3-4", "4-4", "5-1", "5-10"],
        "unlocked": 1,
    }
    saved.update(overrides)
    return saved


@requires_shop
def test_catalog_is_immutable_ordered_and_covers_every_shop_upgrade():
    expected = (
        ("gatling", 500, "3-4"),
        ("twin_sunflower", 500, "3-4"),
        ("gloom_shroom", 750, "4-4"),
        ("spikerock", 800, "5-1"),
        ("winter_melon", 1000, "5-10"),
        ("cob_cannon", 1200, "5-10"),
    )

    assert isinstance(SHOP_CATALOG, ShopCatalog)
    assert tuple((item.key, item.price, item.unlock_level) for item in SHOP_CATALOG.items) == expected
    assert SHOP_CATALOG.keys() == tuple(key for key, _price, _level in expected)
    assert set(SHOP_CATALOG.keys()) == SHOP_UPGRADE_PLANT_KEYS
    assert SHOP_CATALOG.get("gloom_shroom") == ShopItem("gloom_shroom", 750, "4-4")
    assert SHOP_CATALOG.get("missing") is None

    with pytest.raises(FrozenInstanceError):
        SHOP_CATALOG.items = ()
    with pytest.raises(FrozenInstanceError):
        SHOP_CATALOG.items[0].price = 1


@requires_shop
def test_purchase_succeeds_without_mutating_input_and_ignores_unlocked():
    saved = make_save(
        coins=700,
        cleared_levels=["3-4"],
        unlocked=1,
    )
    original = deepcopy(saved)

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.PURCHASED
    assert candidate["coins"] == 200
    assert candidate["upgrades"] == {"gatling": True}
    assert saved == original
    assert candidate is not saved
    assert candidate["upgrades"] is not saved["upgrades"]


@requires_shop
def test_purchase_accepts_an_exact_coin_balance():
    status, candidate = prepare_shop_purchase(
        make_save(coins=500, cleared_levels=["3-4"]),
        "twin_sunflower",
    )

    assert status is ShopPurchaseStatus.PURCHASED
    assert candidate["coins"] == 0
    assert candidate["upgrades"]["twin_sunflower"] is True


@requires_shop
def test_purchase_rejects_one_coin_short():
    saved = make_save(coins=499, cleared_levels=["3-4"])

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.INSUFFICIENT
    assert candidate == saved
    assert candidate is not saved


@requires_shop
def test_owned_item_overrides_missing_unlock_milestone():
    saved = make_save(
        coins=0,
        upgrades={"winter_melon": True},
        cleared_levels=[],
        unlocked=50,
    )

    status, candidate = prepare_shop_purchase(saved, "winter_melon")

    assert status is ShopPurchaseStatus.OWNED
    assert candidate == saved
    assert candidate is not saved


@requires_shop
def test_locked_item_does_not_use_unlocked_level_count():
    saved = make_save(coins=2000, cleared_levels=[], unlocked=50)

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.LOCKED
    assert candidate == saved


@requires_shop
def test_future_save_is_not_interpreted_or_modified():
    saved = {
        "save_version": SAVE_VERSION + 1,
        "future_payload": {"keep": [1, 2, 3]},
    }

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.FUTURE_SAVE
    assert candidate == saved
    assert candidate is not saved
    assert candidate["future_payload"] is not saved["future_payload"]


@requires_shop
@pytest.mark.parametrize("coins", [True, False, -1, 1.0, "500", None])
def test_invalid_coins_are_rejected(coins):
    saved = make_save(coins=coins)

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.INVALID_DATA
    assert candidate == saved


@requires_shop
@pytest.mark.parametrize("upgrades", [None, [], "gatling", 1])
def test_invalid_upgrades_are_rejected(upgrades):
    saved = make_save(upgrades=upgrades)

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.INVALID_DATA
    assert candidate == saved


@requires_shop
@pytest.mark.parametrize("cleared_levels", [None, {}, "3-4", ("3-4",)])
def test_invalid_cleared_levels_are_rejected(cleared_levels):
    saved = make_save(cleared_levels=cleared_levels)

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.INVALID_DATA
    assert candidate == saved


@requires_shop
def test_unknown_item_key_is_invalid_data():
    saved = make_save()

    status, candidate = prepare_shop_purchase(saved, "not_a_shop_item")

    assert status is ShopPurchaseStatus.INVALID_DATA
    assert candidate == saved
    assert candidate is not saved


@requires_shop
def test_success_preserves_unknown_fields_by_deep_copy():
    saved = make_save(
        coins=500,
        cleared_levels=["3-4"],
        custom_field={"nested": ["keep"]},
    )

    status, candidate = prepare_shop_purchase(saved, "gatling")

    assert status is ShopPurchaseStatus.PURCHASED
    assert candidate["custom_field"] == saved["custom_field"]
    assert candidate["custom_field"] is not saved["custom_field"]
    assert candidate["custom_field"]["nested"] is not saved["custom_field"]["nested"]


@requires_shop
def test_repeated_purchase_returns_owned_without_charging_twice():
    saved = make_save(coins=1000, cleared_levels=["3-4"])

    first_status, first_candidate = prepare_shop_purchase(saved, "gatling")
    second_status, second_candidate = prepare_shop_purchase(first_candidate, "gatling")

    assert first_status is ShopPurchaseStatus.PURCHASED
    assert second_status is ShopPurchaseStatus.OWNED
    assert first_candidate["coins"] == 500
    assert second_candidate["coins"] == 500
    assert second_candidate == first_candidate
    assert second_candidate is not first_candidate


@requires_shop
def test_status_enum_includes_save_failed_for_game_io_handling():
    assert {status.value for status in ShopPurchaseStatus} == {
        "purchased",
        "owned",
        "insufficient",
        "locked",
        "future_save",
        "invalid_data",
        "save_failed",
    }
