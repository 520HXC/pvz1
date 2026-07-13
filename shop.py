from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from progression import SAVE_VERSION


@dataclass(frozen=True)
class ShopItem:
    key: str
    price: int
    unlock_level: str


@dataclass(frozen=True)
class ShopCatalog:
    items: tuple[ShopItem, ...]

    def get(self, key: str) -> ShopItem | None:
        return next((item for item in self.items if item.key == key), None)

    def keys(self) -> tuple[str, ...]:
        return tuple(item.key for item in self.items)


class ShopPurchaseStatus(str, Enum):
    PURCHASED = "purchased"
    OWNED = "owned"
    INSUFFICIENT = "insufficient"
    LOCKED = "locked"
    FUTURE_SAVE = "future_save"
    INVALID_DATA = "invalid_data"
    SAVE_FAILED = "save_failed"


SHOP_CATALOG = ShopCatalog(
    items=(
        ShopItem("gatling", 500, "3-4"),
        ShopItem("twin_sunflower", 500, "3-4"),
        ShopItem("gloom_shroom", 750, "4-4"),
        ShopItem("spikerock", 800, "5-1"),
        ShopItem("winter_melon", 1000, "5-10"),
        ShopItem("cob_cannon", 1200, "5-10"),
    )
)


def prepare_shop_purchase(
    save_data: Mapping[str, object],
    item_key: str,
) -> tuple[ShopPurchaseStatus, dict[str, object]]:
    candidate = deepcopy(dict(save_data))
    save_version = candidate.get("save_version")
    if type(save_version) is int and save_version > SAVE_VERSION:
        return ShopPurchaseStatus.FUTURE_SAVE, candidate

    item = SHOP_CATALOG.get(item_key)
    coins = candidate.get("coins")
    upgrades = candidate.get("upgrades")
    cleared_levels = candidate.get("cleared_levels")
    if (
        item is None
        or type(coins) is not int
        or coins < 0
        or not isinstance(upgrades, dict)
        or not isinstance(cleared_levels, list)
    ):
        return ShopPurchaseStatus.INVALID_DATA, candidate

    if upgrades.get(item.key):
        return ShopPurchaseStatus.OWNED, candidate
    if item.unlock_level not in cleared_levels:
        return ShopPurchaseStatus.LOCKED, candidate
    if coins < item.price:
        return ShopPurchaseStatus.INSUFFICIENT, candidate

    candidate["coins"] = coins - item.price
    upgrades[item.key] = True
    return ShopPurchaseStatus.PURCHASED, candidate
