from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


CLASSIC_PLANT_CHAPTERS: Mapping[str, tuple[str, ...]] = {
    "day": (
        "peashooter",
        "sunflower",
        "cherrybomb",
        "wallnut",
        "potato_mine",
        "snowpea",
        "chomper",
        "repeater",
    ),
    "night": (
        "puff_shroom",
        "sun_shroom",
        "fume_shroom",
        "grave_buster",
        "hypno_shroom",
        "scaredy_shroom",
        "ice_shroom",
        "doom_shroom",
    ),
    "pool": (
        "lily_pad",
        "squash",
        "threepeater",
        "tangle_kelp",
        "jalapeno",
        "spikeweed",
        "torchwood",
        "tall_nut",
    ),
    "fog": (
        "sea_shroom",
        "plantern",
        "cactus",
        "blover",
        "split_pea",
        "starfruit",
        "pumpkin",
        "magnet_shroom",
    ),
    "roof": (
        "cabbage_pult",
        "flower_pot",
        "kernel_pult",
        "coffee_bean",
        "garlic",
        "umbrella_leaf",
        "marigold",
        "melon_pult",
    ),
    "upgrades": (
        "gatling",
        "twin_sunflower",
        "gloom_shroom",
        "cattail",
        "winter_melon",
        "gold_magnet",
        "spikerock",
        "cob_cannon",
        "imitater",
    ),
}

CLASSIC_ZOMBIE_CHAPTERS: Mapping[str, tuple[str, ...]] = {
    "day": ("normal", "flag_zombie", "conehead", "pole_vaulting", "buckethead"),
    "night": ("newspaper", "screen_door", "football", "dancing", "backup_dancer"),
    "pool": ("ducky_tube", "snorkel", "zomboni", "bobsled_team", "dolphin_rider"),
    "fog": ("jack_in_the_box", "balloon", "digger", "pogo", "yeti"),
    "roof": ("bungee", "ladder", "catapult", "gargantuar", "imp", "zomboss"),
}

CLASSIC_PLANT_CHAPTER_KEYS = tuple(CLASSIC_PLANT_CHAPTERS)
CLASSIC_ZOMBIE_CHAPTER_KEYS = tuple(CLASSIC_ZOMBIE_CHAPTERS)


@dataclass(frozen=True)
class AlmanacEntry:
    key: str
    category: str
    names: Mapping[str, str]
    stats: Mapping[str, object]
    texts: Mapping[str, Mapping[str, str]]
    sprite: str
    public: bool = True

    def name(self, language: str = "en") -> str:
        return self.names.get(language) or self.names.get("en") or self.key

    def text(self, language: str, field: str) -> str:
        language_text = self.texts.get(language) or self.texts.get("en", {})
        return str(language_text.get(field, ""))

    @property
    def sprite_path(self) -> str:
        return self.sprite


@dataclass(frozen=True)
class AlmanacChapter:
    key: str
    category: str
    declared_keys: tuple[str, ...]
    entries: tuple[AlmanacEntry, ...]


@dataclass(frozen=True)
class AlmanacCatalog:
    plant_chapters: tuple[AlmanacChapter, ...]
    zombie_chapters: tuple[AlmanacChapter, ...]

    def chapters(self, category: str) -> tuple[AlmanacChapter, ...]:
        if category == "plants":
            return self.plant_chapters
        if category == "zombies":
            return self.zombie_chapters
        raise KeyError(category)

    def chapter(self, category: str, key: str) -> AlmanacChapter:
        for chapter in self.chapters(category):
            if chapter.key == key:
                return chapter
        raise KeyError((category, key))

    def entry(self, category: str, key: str) -> AlmanacEntry:
        for chapter in self.chapters(category):
            for entry in chapter.entries:
                if entry.key == key:
                    return entry
        raise KeyError((category, key))


ZOMBIE_NAMES_ZH: Mapping[str, str] = {
    "normal": "普通僵尸",
    "flag_zombie": "旗帜僵尸",
    "conehead": "路障僵尸",
    "pole_vaulting": "撑杆僵尸",
    "buckethead": "铁桶僵尸",
    "newspaper": "读报僵尸",
    "screen_door": "铁栅门僵尸",
    "football": "橄榄球僵尸",
    "dancing": "舞王僵尸",
    "backup_dancer": "伴舞僵尸",
    "ducky_tube": "鸭子救生圈僵尸",
    "snorkel": "潜水僵尸",
    "zomboni": "冰车僵尸",
    "bobsled_team": "雪橇车僵尸小队",
    "dolphin_rider": "海豚骑士僵尸",
    "jack_in_the_box": "小丑僵尸",
    "balloon": "气球僵尸",
    "digger": "矿工僵尸",
    "pogo": "跳跳僵尸",
    "bungee": "蹦极僵尸",
    "ladder": "扶梯僵尸",
    "catapult": "投石车僵尸",
    "gargantuar": "巨人僵尸",
    "imp": "小鬼僵尸",
    "zomboss": "僵王博士",
}


def _zombie_copy(mechanics_en: str, counter_en: str, flavor_en: str, mechanics_zh: str, counter_zh: str, flavor_zh: str) -> Mapping[str, Mapping[str, str]]:
    return {
        "en": {"mechanics": mechanics_en, "counter": counter_en, "flavor": flavor_en},
        "zh": {"mechanics": mechanics_zh, "counter": counter_zh, "flavor": flavor_zh},
    }


ZOMBIE_COPY: Mapping[str, Mapping[str, Mapping[str, str]]] = {
    "normal": _zombie_copy(
        "Walks straight down one lane and stops to bite the first edible plant.",
        "Any steady shooter behind a cheap blocker defeats this basic lane threat efficiently.",
        "He arrived late, hungry, and absolutely certain this was the correct address.",
        "沿固定路线缓慢前进，遇到第一株可以啃食的植物便会停下持续攻击。",
        "用低费坚果拖延，再让豌豆射手等持续火力稳定输出即可轻松处理。",
        "他走错了门牌号，却坚信脑子就在这条路的尽头。",
    ),
    "flag_zombie": _zombie_copy(
        "Leads a major wave with ordinary durability while signaling a dense group behind him.",
        "Treat the flag as a timing warning and prepare splash damage before the crowd reaches your wall.",
        "The flag is impressive, although nobody remembers voting for him.",
        "在大型波次最前方举旗登场，本体耐久普通，但预示后方会有密集僵尸群。",
        "看到旗帜就提前补齐群体火力和防线，不要等整群僵尸贴近以后才临时布阵。",
        "旗子很有气势，只是没有任何僵尸记得选举过他。",
    ),
    "conehead": _zombie_copy(
        "Wears a traffic cone that adds a solid armor layer over an otherwise normal walker.",
        "Concentrated pea fire or an early explosive removes the cone before it strains the front line.",
        "Road safety equipment has found a bold and deeply incorrect second career.",
        "头顶路障提供额外护甲，移动和啃食方式与普通僵尸相同，但更能承受正面火力。",
        "集中两路以上的持续射击，或在僵尸密集时用爆炸植物快速打掉路障护甲。",
        "交通安全设施找到了大胆却完全错误的第二份工作。",
    ),
    "pole_vaulting": _zombie_copy(
        "Runs toward the first obstacle, vaults over it once, then continues at walking speed without the pole.",
        "Place a disposable plant ahead of the real defense to spend his single vault harmlessly.",
        "Years of training were devoted to clearing exactly one garden obstacle.",
        "高速冲向首个障碍并用撑杆越过一次，落地丢杆后改为普通步行和啃食。",
        "在主防线前放置便宜植物骗掉唯一一次跳跃，再由后方火力完成击杀。",
        "多年训练最终只为了跨过花园里的一株植物。",
    ),
    "buckethead": _zombie_copy(
        "Carries a metal bucket with enough armor to absorb prolonged single-lane fire.",
        "Use high sustained damage, Magnet-shroom, or an instant attack before the bucket reaches your economy.",
        "The bucket was labeled utility grade, which he considered a personal challenge.",
        "铁桶提供厚重金属护甲，能够长时间承受单路线火力后继续向前推进。",
        "使用高持续伤害、磁力菇拆除铁桶，或在其接近经济植物前直接秒杀。",
        "铁桶标着工具用品，他却把它理解成了头盔认证。",
    ),
    "newspaper": _zombie_copy(
        "Blocks damage with his newspaper, then becomes enraged and moves much faster after it breaks.",
        "Burst him down during the transition or slow him before breaking the paper to contain the rush.",
        "Nothing ruins a quiet morning like discovering the obituary section is about you.",
        "先用报纸抵挡伤害，报纸破碎后会短暂发怒，并以更快速度冲向植物。",
        "先施加减速再打碎报纸，或在发怒过渡期间集中爆发，避免其快速冲破防线。",
        "安静早晨最糟的事情，是发现讣告栏写的正是自己。",
    ),
    "screen_door": _zombie_copy(
        "Holds a screen door as a large frontal shield that absorbs ordinary projectiles before his body is harmed.",
        "Fume attacks pierce the door, while Magnet-shroom can strip the metal defense completely.",
        "He brought the front door along because knocking felt unnecessarily formal.",
        "手持铁栅门形成高耐久正面盾牌，普通子弹必须先摧毁门板才能伤到本体。",
        "大喷菇的烟雾可以穿透门板，磁力菇也能直接拆掉金属防具。",
        "他把自家前门也带来了，因为敲门显得过于正式。",
    ),
    "football": _zombie_copy(
        "Charges at exceptional speed in heavy armor and delivers severe bite pressure on contact.",
        "Slow him immediately, remove his helmet with Magnet-shroom, or reserve an instant kill for his lane.",
        "The playbook contains one diagram, and every arrow points toward your lawn.",
        "身穿重甲高速冲锋，接触植物后还能造成极高啃食压力，是危险的突破单位。",
        "立即减速并用磁力菇拆盔，或为所在路线保留窝瓜等一次性处决手段。",
        "战术板上只有一张图，所有箭头都指向你的草坪。",
    ),
    "dancing": _zombie_copy(
        "Periodically summons backup dancers into nearby lanes, turning one attacker into a compact formation.",
        "Eliminate the leader quickly with focused or area damage before repeated summons surround your defense.",
        "His choreography is infectious in every possible meaning of the word.",
        "会周期性在相邻路线召唤伴舞僵尸，使单个威胁迅速扩张成小型阵列。",
        "优先集火舞王并搭配范围伤害，在多轮召唤包围防线之前消灭核心。",
        "他的舞步具有传染性，而且是这个词的每一种含义。",
    ),
    "backup_dancer": _zombie_copy(
        "Appears beside a Dancing Zombie as a fast supporting body that adds pressure across adjacent lanes.",
        "Area attacks erase the formation efficiently, while killing the leader prevents replacement dancers.",
        "Every star needs an ensemble, even when the venue is a vegetable garden.",
        "由舞王在相邻路线召唤，移动较快，用数量为多条路线同时增加压力。",
        "范围攻击能高效清理伴舞阵列，同时尽快击杀舞王以阻止后续补员。",
        "每位明星都需要伴舞，即使舞台只是一片菜园。",
    ),
    "ducky_tube": _zombie_copy(
        "Uses a ducky tube to enter pool lanes while otherwise behaving like a standard walking zombie.",
        "Build normal ranged damage on Lily Pads and keep water lanes covered just like the grass lanes.",
        "The duck is inflatable, but his confidence is regrettably permanent.",
        "借助鸭子救生圈进入泳池路线，除此之外移动和啃食方式接近普通僵尸。",
        "在睡莲上建立正常远程火力，确保水路和草地路线一样始终有人防守。",
        "鸭子可以放气，但他的自信显然无法收回。",
    ),
    "snorkel": _zombie_copy(
        "Travels submerged and untargetable by normal shots, surfacing only when he reaches a plant to attack.",
        "Use Tangle Kelp or close-range water defenses, then focus fire during his exposed attack window.",
        "He mistakes holding his breath for a complete tactical doctrine.",
        "潜水前进时普通射击无法锁定，只有抵达植物附近并浮出水面后才会暴露。",
        "用缠绕水草或近距离水路防御拦截，并抓住其浮出攻击时的窗口集中输出。",
        "他把憋气当成了一整套完整的战术理论。",
    ),
    "zomboni": _zombie_copy(
        "Drives forward as a crushing vehicle, destroys plants on contact, and leaves an icy trail behind.",
        "Spikeweed or Spikerock stops the machine, while heavy burst damage prevents a long ice lane.",
        "The warranty definitely did not include landscaping services.",
        "驾驶冰车向前碾压，接触植物便会摧毁整格，并在经过路线留下持续冰道。",
        "地刺或地刺王能够克制车辆，也可用高爆发尽早击毁以缩短冰道长度。",
        "保修条款里绝对没有包含任何园林维护服务。",
    ),
    "bobsled_team": _zombie_copy(
        "Rushes over an existing ice lane as a fast team, then breaks into multiple attackers after the ride ends.",
        "Prevent Zomboni ice, place spikes on the route, or prepare splash damage for the dismounting group.",
        "Teamwork makes the dream work, although the dream is mostly property damage.",
        "沿现有冰道高速滑行，雪橇结束后会变成多个独立成员继续向前攻击。",
        "阻止冰车铺路，在行进路线上布置地刺，或准备范围伤害清理下车小队。",
        "团队合作成就梦想，只是这个梦想主要涉及财产损失。",
    ),
    "dolphin_rider": _zombie_copy(
        "Sprints through a pool lane, leaps over the first blocker once, then continues at reduced speed.",
        "Offer a cheap Lily Pad plant to consume the leap before he reaches the real water defense.",
        "The dolphin has wisely declined every request for an interview.",
        "在泳池路线高速冲刺并越过首个阻挡植物一次，落地后会以较低速度继续前进。",
        "用便宜的睡莲或植物提前骗掉跳跃，保护后方真正承担防守的水路阵地。",
        "海豚非常明智地拒绝了所有采访请求。",
    ),
    "jack_in_the_box": _zombie_copy(
        "Carries a jack-in-the-box that may detonate near the defense and destroy plants in a wide area.",
        "Kill him at long range, freeze the advance, or use Magnet-shroom to neutralize the metal box.",
        "The tune is catchy right up until the final, extremely loud note.",
        "携带会随机引爆的小丑盒，靠近防线时可能用大范围爆炸摧毁多株植物。",
        "尽量远距离击杀并控制推进速度，或使用磁力菇提前解除金属小丑盒。",
        "旋律一直很上头，直到最后那个特别响亮的音符。",
    ),
    "balloon": _zombie_copy(
        "Floats over ground plants and ordinary projectiles while the balloon remains intact.",
        "Cactus can pop the balloon, while Blover removes airborne threats from the lawn immediately.",
        "He packed for altitude but forgot to plan the landing.",
        "气球完整时会飞越地面植物并免疫普通子弹，能够直接绕过常规路线防线。",
        "仙人掌可以击破气球，三叶草则能立刻清除草坪上的空中威胁。",
        "他为高空准备得很充分，却完全忘记规划降落。",
    ),
    "digger": _zombie_copy(
        "Tunnels beneath the lawn, emerges behind the formation, then turns to attack from the rear.",
        "Magnet-shroom removes the pickaxe, and Split Pea protects the vulnerable back side of each lane.",
        "He believes every problem can be solved by approaching it from underneath.",
        "从地下穿过正面防线，在阵型后方出土并转身，从背面啃食经济与火力植物。",
        "磁力菇可以吸走矿镐，双向射手则能持续保护每条路线脆弱的后方。",
        "他相信所有问题都能通过从地下接近来解决。",
    ),
    "pogo": _zombie_copy(
        "Repeatedly hops over low obstacles and keeps advancing without spending a single one-time vault.",
        "Tall-nut blocks the pogo path, while Magnet-shroom removes the metal pogo stick entirely.",
        "He has mistaken relentless bouncing for a mature transportation policy.",
        "能够反复跳过低矮障碍，不像撑杆僵尸那样只跳一次，因此会持续突破普通阻挡。",
        "高坚果能够挡住跳跃，磁力菇也可以直接吸走金属跳跳杆。",
        "他把不停弹跳误认为一套成熟的交通政策。",
    ),
    "bungee": _zombie_copy(
        "Descends from above, locks onto a plant, then steals it and retreats vertically out of the battle.",
        "Umbrella Leaf protects nearby cells, and fast burst damage can interrupt the theft before lift-off.",
        "He specializes in express delivery, except the package travels the wrong way.",
        "从空中下降并锁定一株植物，抓取成功后会带着目标垂直撤离战场。",
        "叶子保护伞能够覆盖附近格子，也可在起飞前用快速爆发打断偷取。",
        "他专营极速快递，只是包裹总朝错误方向运输。",
    ),
    "ladder": _zombie_copy(
        "Carries a ladder that lets following zombies cross a defensive wall after he places it.",
        "Magnet-shroom removes the ladder, while damage or replacement can clear the compromised blocker.",
        "He supports accessibility, provided the destination contains brains.",
        "携带梯子并架在坚果类防线上，使后续僵尸能够直接越过原本可靠的阻挡。",
        "磁力菇可吸走梯子，也可尽快处理或替换已经被架梯的防御植物。",
        "他支持无障碍通行，前提是目的地里存放着脑子。",
    ),
    "catapult": _zombie_copy(
        "Stops at range and lobs projectiles toward backline plants instead of biting the front blocker.",
        "Umbrella Leaf intercepts incoming shots, while spikes and focused fire punish the slow vehicle.",
        "Siege engineering was easier than learning where the garden gate opens.",
        "会停在远处向后排植物投掷弹药，不必先啃穿最前方的阻挡植物。",
        "叶子保护伞可以拦截投射物，地刺与集中火力则能惩罚移动缓慢的车辆。",
        "学习攻城工程，比弄清花园大门怎么开更加容易。",
    ),
    "gargantuar": _zombie_copy(
        "Absorbs enormous damage, smashes plants with a club, and throws an Imp when badly wounded.",
        "Layer instant attacks and heavy artillery, then keep rear defenses ready for the thrown Imp.",
        "He carries a telephone pole because subtlety was already out of stock.",
        "拥有极高耐久，会用重物直接砸毁植物，并在重伤后把小鬼投向阵地后方。",
        "叠加一次性处决与重型火力，同时为被投掷到后排的小鬼预留防守。",
        "他扛着一根电线杆，因为商店里的低调已经售罄。",
    ),
    "imp": _zombie_copy(
        "A small fast attacker commonly thrown over the front line by a wounded Gargantuar.",
        "Maintain cheap rear coverage or quick-response plants so the landing cannot reach your economy freely.",
        "Compact, aerodynamic, and furious about the complete lack of landing instructions.",
        "体型小而移动迅速，通常由受伤的巨人越过前线直接投掷到阵地后方。",
        "后排保留便宜火力或快速反应植物，避免其落地后无阻碍攻击经济区。",
        "小巧、流线、愤怒，而且完全没有收到降落说明。",
    ),
    "zomboss": _zombie_copy(
        "Controls a giant machine with exposed damage windows, elemental attacks, stomps, and summoned zombies.",
        "Preserve conveyor answers for each telegraphed attack and focus lobbed damage during exposure windows.",
        "A doctorate is no guarantee of sensible lawn-care decisions.",
        "操纵巨型机器轮换元素攻击、重踩与召唤，只有暴露阶段才能受到有效伤害。",
        "为每种攻击保留传送带反制卡，并在暴露窗口集中所有投掷火力攻击本体。",
        "拥有博士学位，并不代表会做出合理的草坪管理决定。",
    ),
}


def _plant_entry(key: str, cfg: object) -> AlmanacEntry:
    behavior = str(getattr(cfg, "behavior", "special"))
    damage = float(getattr(cfg, "damage", 0.0))
    sun_amount = int(getattr(cfg, "sun_amount", 0))
    mechanics_en = f"Uses the {behavior.replace('_', ' ')} role with values taken directly from the configured battle unit."
    mechanics_zh = f"定位为{behavior.replace('_', ' ')}，基础数值直接来自当前战斗配置。"
    if damage > 0:
        mechanics_en += f" Its configured damage is {damage:g}."
        mechanics_zh += f"当前配置伤害为{damage:g}。"
    if sun_amount > 0:
        mechanics_en += f" It produces {sun_amount} sun per activation."
        mechanics_zh += f"每次产出{sun_amount}点阳光。"
    return AlmanacEntry(
        key=key,
        category="plants",
        names={
            "en": str(getattr(cfg, "display_name_en", "") or getattr(cfg, "name", key)),
            "zh": str(getattr(cfg, "display_name_zh", "") or getattr(cfg, "name", key)),
        },
        stats={
            "cost": int(getattr(cfg, "cost", 0)),
            "hp": int(getattr(cfg, "hp", 0)),
            "cooldown": float(getattr(cfg, "cooldown", 0.0)),
            "behavior": behavior,
            "damage": damage,
            "interval": float(getattr(cfg, "interval", 0.0)),
        },
        texts={
            "en": {
                "mechanics": mechanics_en,
                "counter": "Protect its role with suitable lane support and replace it when the defense changes.",
                "flavor": "A familiar garden specialist ready for another carefully planned defense.",
            },
            "zh": {
                "mechanics": mechanics_zh,
                "counter": "根据它的定位搭配前排与火力，并在战线变化时及时调整或补种。",
                "flavor": "熟悉的花园专家，随时准备加入下一次防守。",
            },
        },
        sprite=str(getattr(cfg, "sprite_path", "") or f"assets/plants/{key}.png"),
    )


def _zombie_entry(key: str, cfg: object) -> AlmanacEntry:
    copy = ZOMBIE_COPY.get(key)
    if copy is None:
        raise ValueError(f"Missing specific almanac copy for zombie {key}")
    speed = tuple(getattr(cfg, "speed", (0.0, 0.0)))
    dps = tuple(getattr(cfg, "dps", (0.0, 0.0)))
    return AlmanacEntry(
        key=key,
        category="zombies",
        names={
            "en": str(getattr(cfg, "display_name_en", "") or getattr(cfg, "name", key)),
            "zh": ZOMBIE_NAMES_ZH.get(key, str(getattr(cfg, "display_name_zh", "") or getattr(cfg, "name", key))),
        },
        stats={
            "hp": int(getattr(cfg, "hp", 0)),
            "speed": speed,
            "dps": dps,
            "behavior": str(getattr(cfg, "behavior", "special")),
        },
        texts=copy,
        sprite=str(getattr(cfg, "sprite_path", "") or f"assets/zombies/{key}.png"),
    )


def _build_chapters(
    category: str,
    declarations: Mapping[str, Sequence[str]],
    configured: Mapping[str, object],
) -> tuple[AlmanacChapter, ...]:
    entry_builder = _plant_entry if category == "plants" else _zombie_entry
    chapters = []
    seen = set()
    for chapter_key, declared in declarations.items():
        declared_keys = tuple(str(key) for key in declared)
        entries = []
        for key in declared_keys:
            cfg = configured.get(key)
            if cfg is None:
                continue
            if key in seen:
                raise ValueError(f"Duplicate {category} almanac key {key}")
            entries.append(entry_builder(key, cfg))
            seen.add(key)
        chapters.append(
            AlmanacChapter(
                key=chapter_key,
                category=category,
                declared_keys=declared_keys,
                entries=tuple(entries),
            )
        )
    unassigned = set(configured) - seen
    if unassigned:
        names = ", ".join(sorted(unassigned))
        raise ValueError(f"Unassigned {category} almanac entries {names}")
    return tuple(chapters)


def build_almanac_catalog(
    plants: Mapping[str, object],
    zombies: Mapping[str, object],
) -> AlmanacCatalog:
    return AlmanacCatalog(
        plant_chapters=_build_chapters("plants", CLASSIC_PLANT_CHAPTERS, plants),
        zombie_chapters=_build_chapters("zombies", CLASSIC_ZOMBIE_CHAPTERS, zombies),
    )
