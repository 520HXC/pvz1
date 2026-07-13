from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from adventure_levels import ADVENTURE_LEVELS


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


def _build_zombie_first_appearances() -> Mapping[str, str]:
    appearances: dict[str, str] = {}
    for level in ADVENTURE_LEVELS:
        kinds = set(level.zombie_roster)
        kinds.update(kind for wave in level.fixed_waves for kind in wave)
        kinds.update(kind for _wave, kind, _count in level.guaranteed_zombies)
        for kind in kinds:
            appearances.setdefault(str(kind), str(level.code))
    appearances["yeti"] = "4-10"
    return MappingProxyType(appearances)


ZOMBIE_FIRST_APPEARANCE = _build_zombie_first_appearances()


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(values: Mapping[str, object]) -> Mapping[str, object]:
    frozen = _freeze_value(dict(values))
    if not isinstance(frozen, Mapping):
        raise TypeError("Expected a mapping")
    return frozen


@dataclass(frozen=True)
class AlmanacEntry:
    key: str
    category: str
    names: Mapping[str, str]
    stats: Mapping[str, object]
    texts: Mapping[str, Mapping[str, str]]
    sprite: str
    public: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "names", _freeze_mapping(self.names))
        object.__setattr__(self, "stats", _freeze_mapping(self.stats))
        object.__setattr__(self, "texts", _freeze_mapping(self.texts))

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
    "yeti": _zombie_copy(
        "Enters as a rare armored visitor, then turns around after a short window and escapes at high speed.",
        "Prepare burst damage before the encounter and focus every lane weapon before the retreat reaches the edge.",
        "The rarest lawn guest is also the least interested in staying for dinner.",
        "作为罕见的高耐久访客登场，短暂停留后会突然转身并高速逃离草坪。",
        "在遭遇前准备爆发火力，并在它退到场地边缘前集中整条路线的输出。",
        "最稀有的草坪客人，偏偏最不愿意留下来吃晚饭。",
    ),
}


PlantCopyProvider = Mapping[str, object] | Callable[[str, object], object]


DEFAULT_PLANT_FLAVOR: Mapping[str, Mapping[str, str]] = {
    "peashooter": {
        "en": "Peashooter calls it a straight line because every problem eventually stands in one.",
        "zh": "豌豆射手喜欢直线思考，因为麻烦最后总会站到直线上。",
    },
    "sunflower": {
        "en": "Sunflower runs the lawn economy and still finds time to smile for payroll.",
        "zh": "向日葵掌管整片草坪的经济，还坚持微笑着发工资。",
    },
    "cherrybomb": {
        "en": "The Cherry twins agree on everything, especially dramatic exits.",
        "zh": "樱桃兄弟难得意见一致，尤其赞成用爆炸退场。",
    },
    "wallnut": {
        "en": "Wall-nut has no attack plan, only an extremely patient face.",
        "zh": "坚果墙没有进攻计划，只有一张特别耐心的脸。",
    },
    "potato_mine": {
        "en": "Potato Mine believes good surprises should be planted well in advance.",
        "zh": "土豆雷认为，真正的惊喜都应该提前埋好。",
    },
    "snowpea": {
        "en": "Snow Pea keeps every argument cool and every lane considerably slower.",
        "zh": "寒冰射手擅长让争论降温，也让整条路线一起慢下来。",
    },
    "chomper": {
        "en": "Chomper never reads the menu because the menu is usually walking toward him.",
        "zh": "大嘴花从不看菜单，因为菜单通常正自己走过来。",
    },
    "repeater": {
        "en": "Repeater repeats himself, but the second point is usually another pea.",
        "zh": "双发射手喜欢重复发言，而第二句通常还是一颗豌豆。",
    },
    "puff_shroom": {
        "en": "Puff-shroom works for free and reminds everyone of it at every short-range meeting.",
        "zh": "小喷菇免费上班，并在每次近距离会议上反复强调这点。",
    },
    "sun_shroom": {
        "en": "Sun-shroom starts small, then quietly becomes the tallest accountant at night.",
        "zh": "阳光菇起步很小，后来悄悄长成夜班里最高的会计。",
    },
    "fume_shroom": {
        "en": "Fume-shroom considers doors a suggestion rather than a defensive structure.",
        "zh": "大喷菇觉得门板只是建议，从来算不上真正的防御。",
    },
    "grave_buster": {
        "en": "Grave Buster accepts one reservation at a time and always clears the table.",
        "zh": "墓碑吞噬者一次只接一桌，但保证把桌面清得干净。",
    },
    "hypno_shroom": {
        "en": "Hypno-shroom wins debates by letting the opponent argue with his own team.",
        "zh": "魅惑菇赢辩论的方法，是让对手转身去和队友争。",
    },
    "scaredy_shroom": {
        "en": "Scaredy-shroom is fearless at a professionally maintained distance.",
        "zh": "胆小菇在符合职业标准的安全距离外完全无所畏惧。",
    },
    "ice_shroom": {
        "en": "Ice-shroom can pause an entire battlefield but still dislikes waiting in line.",
        "zh": "寒冰菇能让全场暂停，却依然讨厌自己排队。",
    },
    "doom_shroom": {
        "en": "Doom-shroom leaves a lasting impression, usually shaped like a crater.",
        "zh": "毁灭菇总会留下深刻印象，而且通常是弹坑形状。",
    },
    "lily_pad": {
        "en": "Lily Pad carries the whole pool strategy and politely pretends it is not heavy.",
        "zh": "睡莲托着整套泳池战术，还礼貌地假装一点也不重。",
    },
    "squash": {
        "en": "Squash takes one look at a problem and decides vertical discussion is best.",
        "zh": "窝瓜看一眼问题，就决定用垂直方式进行沟通。",
    },
    "threepeater": {
        "en": "Threepeater attends three lane meetings at once and brings peas to all of them.",
        "zh": "三线射手同时参加三场路线会议，并给每场都带了豌豆。",
    },
    "tangle_kelp": {
        "en": "Tangle Kelp offers swimmers a private tour of the pool bottom.",
        "zh": "缠绕水草专门邀请游泳者参观泳池底部，而且是单程。",
    },
    "jalapeno": {
        "en": "Jalapeno solves lane disputes with a single very spicy underline.",
        "zh": "火爆辣椒用一条特别辣的下划线解决整行争端。",
    },
    "spikeweed": {
        "en": "Spikeweed never chases trouble because trouble has to step on him eventually.",
        "zh": "地刺从不追赶麻烦，因为麻烦迟早会自己踩上来。",
    },
    "torchwood": {
        "en": "Torchwood improves every passing pea and charges no consulting fee.",
        "zh": "火炬树桩升级每颗路过的豌豆，而且不收咨询费。",
    },
    "tall_nut": {
        "en": "Tall-nut heard the jumpers were coming and simply became more wall.",
        "zh": "高坚果听说有人想跳过去，于是决定再多长一点墙。",
    },
    "sea_shroom": {
        "en": "Sea-shroom works the free night shift and requests payment in dry towels.",
        "zh": "海蘑菇免费值夜班，只要求下班时给一条干毛巾。",
    },
    "plantern": {
        "en": "Plantern brightens the fog and every tactical conversation around it.",
        "zh": "路灯花照亮浓雾，也顺便照亮附近所有战术讨论。",
    },
    "cactus": {
        "en": "Cactus keeps one eye on the lane and the other on suspicious balloons.",
        "zh": "仙人掌一只眼看路线，另一只专门盯着可疑气球。",
    },
    "blover": {
        "en": "Blover has one powerful opinion about airborne visitors and expresses it loudly.",
        "zh": "三叶草对空中访客只有一个强烈意见，而且表达得很响。",
    },
    "split_pea": {
        "en": "Split Pea never turns his back on danger because one face is already there.",
        "zh": "裂荚射手从不背对危险，因为背后本来就有一张脸。",
    },
    "starfruit": {
        "en": "Starfruit refuses to choose a direction when five directions are available.",
        "zh": "杨桃拒绝只选一个方向，毕竟明明有五个可以选。",
    },
    "pumpkin": {
        "en": "Pumpkin believes personal space should come with reinforced orange walls.",
        "zh": "南瓜头认为，私人空间就该配上加固的橙色外墙。",
    },
    "magnet_shroom": {
        "en": "Magnet-shroom collects metal fashion before it can become a battlefield trend.",
        "zh": "磁力菇专收金属时装，免得它们在战场上流行起来。",
    },
    "cabbage_pult": {
        "en": "Cabbage-pult proved vegetables can fly if the roof angle is persuasive enough.",
        "zh": "卷心菜投手证明，只要屋顶角度合适，蔬菜也能飞。",
    },
    "flower_pot": {
        "en": "Flower Pot provides premium roof real estate with excellent drainage.",
        "zh": "花盆提供屋顶黄金地段，而且排水条件相当优秀。",
    },
    "kernel_pult": {
        "en": "Kernel-pult serves corn with occasional butter and absolutely no table manners.",
        "zh": "玉米投手供应玉米和偶尔的黄油，唯独不供应餐桌礼仪。",
    },
    "coffee_bean": {
        "en": "Coffee Bean wakes mushrooms faster than any alarm clock dares to try.",
        "zh": "咖啡豆叫醒蘑菇的速度，连闹钟都不敢尝试。",
    },
    "garlic": {
        "en": "Garlic redirects traffic with a fragrance stronger than painted arrows.",
        "zh": "大蒜用气味指挥交通，比地上的箭头有效得多。",
    },
    "umbrella_leaf": {
        "en": "Umbrella Leaf checks the forecast for falling zombies and suspicious basketballs.",
        "zh": "叶子保护伞每天查看天气，重点关注落下的僵尸和篮球。",
    },
    "marigold": {
        "en": "Marigold grows pocket change and insists this counts as agriculture.",
        "zh": "金盏花种出零钱，并坚持认为这当然属于农业。",
    },
    "melon_pult": {
        "en": "Melon-pult believes every crowded gathering needs a very large fruit.",
        "zh": "西瓜投手相信，拥挤聚会都需要一颗特别大的水果。",
    },
    "gatling": {
        "en": "Gatling Pea measures conversation in bursts of four.",
        "zh": "机枪射手用四连发作为一句话的标准长度。",
    },
    "twin_sunflower": {
        "en": "Twin Sunflower doubled the sunshine and split the bookkeeping evenly.",
        "zh": "双子向日葵把阳光翻倍，也把账本公平地分成两份。",
    },
    "gloom_shroom": {
        "en": "Gloom-shroom prefers close company, provided the company regrets arriving.",
        "zh": "忧郁菇喜欢近距离作伴，前提是客人马上后悔靠近。",
    },
    "cattail": {
        "en": "Cattail tracks every target except the red dot nobody brought to battle.",
        "zh": "香蒲会追踪所有目标，除了战场上根本不存在的红点。",
    },
    "winter_melon": {
        "en": "Winter Melon delivers heavy fruit with complimentary battlefield refrigeration.",
        "zh": "冰西瓜投递重型水果，还免费附赠战场冷藏服务。",
    },
    "gold_magnet": {
        "en": "Gold Magnet handles loose change so nobody has to crawl under the lawn chairs.",
        "zh": "吸金磁负责捡零钱，免得大家钻到草坪椅下面寻找。",
    },
    "spikerock": {
        "en": "Spikerock upgraded from painful floor to formally hostile terrain.",
        "zh": "地刺王从扎脚地板升级成了正式敌对地形。",
    },
    "cob_cannon": {
        "en": "Cob Cannon calls every launch a harvest and every crater a receipt.",
        "zh": "玉米加农炮把每次发射叫收割，把每个弹坑叫收据。",
    },
    "imitater": {
        "en": "Imitater is original enough to admit that copying was the entire plan.",
        "zh": "模仿者最大的原创之处，是坦白复制本来就是计划。",
    },
}


PLANT_ROLE_LABELS: Mapping[str, tuple[str, str]] = {
    "shoot": ("steady lane fire", "稳定单线射击"),
    "shoot_slow": ("slowing lane fire", "减速单线射击"),
    "shoot_short": ("short-range lane fire", "短距离射击"),
    "sun": ("sun production", "阳光生产"),
    "sun_shroom": ("growing sun production", "成长型阳光生产"),
    "block": ("frontline blocking", "前排阻挡"),
    "bomb": ("area burst damage", "范围爆发"),
    "row_blast": ("full-lane clearing", "整行清场"),
    "pult": ("lobbed artillery", "抛投火力"),
    "kernel_pult": ("control artillery", "控制型抛投"),
    "melon_pult": ("splash artillery", "范围抛投"),
    "support": ("board support", "阵地辅助"),
    "armor": ("protective armor", "外层防护"),
    "spike": ("ground attrition", "地面持续伤害"),
    "cattail": ("homing coverage", "追踪覆盖"),
    "cob": ("heavy artillery", "重型火炮"),
}


def _cfg_display_names(cfg: object, key: str) -> Mapping[str, str]:
    names = {
        "en": str(getattr(cfg, "display_name_en", "")),
        "zh": str(getattr(cfg, "display_name_zh", "")),
    }
    if not names["en"] or not names["zh"]:
        raise ValueError(f"Missing configured display name for {key}")
    return names


def _provider_item(
    provider: PlantCopyProvider | None,
    key: str,
    cfg: object,
) -> object | None:
    if provider is None:
        return None
    if isinstance(provider, Mapping):
        return provider.get(key)
    return provider(key, cfg)


def _description_pair(payload: object, language: str) -> tuple[str, str]:
    if not isinstance(payload, Mapping):
        return "", ""
    localized = payload.get(language)
    if isinstance(localized, Mapping):
        return str(localized.get("short", "")), str(localized.get("summary", ""))
    if isinstance(localized, Sequence) and not isinstance(localized, (str, bytes)):
        values = tuple(localized)
        if len(values) >= 2:
            return str(values[0]), str(values[1])
    return "", ""


def _flavor_text(payload: object, language: str) -> str:
    if not isinstance(payload, Mapping):
        return ""
    localized = payload.get(language)
    if isinstance(localized, Mapping):
        return str(localized.get("flavor", ""))
    if localized is not None:
        return str(localized)
    return ""


def _plant_texts(
    key: str,
    cfg: object,
    plant_descriptions: PlantCopyProvider | None,
    plant_flavor: PlantCopyProvider | None,
) -> Mapping[str, Mapping[str, str]]:
    names = _cfg_display_names(cfg, key)
    behavior = str(getattr(cfg, "behavior", ""))
    role_en, role_zh = PLANT_ROLE_LABELS.get(
        behavior,
        ("specialized garden utility", "专项花园功能"),
    )
    description_payload = _provider_item(plant_descriptions, key, cfg)
    flavor_payload = _provider_item(plant_flavor, key, cfg)
    default_flavor = DEFAULT_PLANT_FLAVOR.get(key)
    if default_flavor is None:
        raise ValueError(f"Missing default plant flavor for {key}")
    texts = {}
    for language in ("en", "zh"):
        mechanics, counter = _description_pair(description_payload, language)
        flavor = _flavor_text(flavor_payload, language)
        if language == "en":
            mechanics = mechanics or f"{names['en']} provides {role_en} using its configured battle values."
            counter = counter or f"Place and protect {names['en']} where that role contributes to the active lanes."
            flavor = flavor or _flavor_text(default_flavor, language)
        else:
            mechanics = mechanics or f"{names['zh']}负责{role_zh}，具体效果采用当前战斗配置。"
            counter = counter or f"把{names['zh']}放在能覆盖当前压力的位置，并为它补足必要保护。"
            flavor = flavor or _flavor_text(default_flavor, language)
        texts[language] = {
            "mechanics": mechanics,
            "counter": counter,
            "flavor": flavor,
        }
    return texts


def _plant_runtime_stats(cfg: object) -> Mapping[str, object]:
    key = str(getattr(cfg, "key", ""))
    behavior = str(getattr(cfg, "behavior", "special"))
    damage = float(getattr(cfg, "damage", 0.0))
    projectile_count = max(1, int(getattr(cfg, "proj_count", 1)))
    sun_amount = int(getattr(cfg, "sun_amount", 0))

    if sun_amount > 0:
        output_kind = "sun"
        output_value: int | float = sun_amount
    elif behavior == "marigold":
        output_kind = "coin"
        output_value = 0
    elif behavior == "gold_magnet":
        output_kind = "collection"
        output_value = 0
    elif damage > 0:
        output_kind = "damage"
        output_value = damage * projectile_count
    elif behavior in {"hypno", "ice", "blover", "magnet", "garlic", "coffee"}:
        output_kind = "control"
        output_value = 0
    else:
        output_kind = "utility"
        output_value = 0

    lane_range = {
        "shoot",
        "shoot_slow",
        "scaredy",
        "split",
        "pult",
        "kernel_pult",
        "melon_pult",
    }
    short_range = {"shoot_short", "fume", "chomp", "gloom", "squash", "potato"}
    if behavior in lane_range:
        range_name = "lane"
    elif behavior in short_range:
        range_name = "short"
    elif behavior == "threepeat":
        range_name = "three_lanes"
    elif behavior in {"star", "cattail"}:
        range_name = "multi_lane"
    elif behavior == "row_blast":
        range_name = "full_lane"
    elif behavior in {"ice", "blover", "gold_magnet"}:
        range_name = "global"
    elif behavior == "cob":
        range_name = "targeted"
    else:
        range_name = "cell"

    if behavior in {"bomb", "doom"}:
        area = "radius"
    elif behavior == "row_blast":
        area = "lane"
    elif behavior in {"ice", "blover"}:
        area = "all_lanes"
    elif behavior in {"threepeat", "star", "cattail"}:
        area = "multi_lane"
    elif behavior in {"melon_pult", "gloom", "cob"} or key == "winter_melon":
        area = "splash"
    else:
        area = "single"

    restrictions = []
    if bool(getattr(cfg, "is_mushroom", False)):
        restrictions.append("night_or_coffee")
    if bool(getattr(cfg, "aquatic_only", False)) or key in {
        "lily_pad",
        "sea_shroom",
        "tangle_kelp",
        "cattail",
    }:
        restrictions.append("water")
    if key == "flower_pot":
        restrictions.append("roof")
    if key == "grave_buster":
        restrictions.append("grave")
    if key == "coffee_bean":
        restrictions.append("sleeping_mushroom")
    if bool(getattr(cfg, "is_overlay", False)):
        restrictions.append("overlay_layer")
    if bool(getattr(cfg, "is_support", False)):
        restrictions.append("support_layer")

    return {
        "cost": int(getattr(cfg, "cost", 0)),
        "hp": int(getattr(cfg, "hp", 0)),
        "cooldown": float(getattr(cfg, "cooldown", 0.0)),
        "behavior": behavior,
        "damage": damage,
        "interval": float(getattr(cfg, "interval", 0.0)),
        "output_kind": output_kind,
        "output_value": output_value,
        "range": range_name,
        "area": area,
        "restrictions": tuple(restrictions),
    }


def _plant_entry(
    key: str,
    cfg: object,
    plant_descriptions: PlantCopyProvider | None = None,
    plant_flavor: PlantCopyProvider | None = None,
) -> AlmanacEntry:
    return AlmanacEntry(
        key=key,
        category="plants",
        names=_cfg_display_names(cfg, key),
        stats=_plant_runtime_stats(cfg),
        texts=_plant_texts(key, cfg, plant_descriptions, plant_flavor),
        sprite=str(getattr(cfg, "sprite_path", "") or f"assets/plants/{key}.png"),
    )


def _zombie_entry(key: str, cfg: object) -> AlmanacEntry:
    copy = ZOMBIE_COPY.get(key)
    if copy is None:
        raise ValueError(f"Missing specific almanac copy for zombie {key}")
    first_appearance = ZOMBIE_FIRST_APPEARANCE.get(key, "")
    if not first_appearance:
        raise ValueError(f"Missing first appearance for zombie {key}")
    return AlmanacEntry(
        key=key,
        category="zombies",
        names=_cfg_display_names(cfg, key),
        stats={
            "hp": int(getattr(cfg, "hp", 0)),
            "speed": tuple(getattr(cfg, "speed", (0.0, 0.0))),
            "dps": tuple(getattr(cfg, "dps", (0.0, 0.0))),
            "behavior": str(getattr(cfg, "behavior", "special")),
            "first_appearance": first_appearance,
        },
        texts=copy,
        sprite=str(getattr(cfg, "sprite_path", "") or f"assets/zombies/{key}.png"),
    )


def _build_chapters(
    category: str,
    declarations: Mapping[str, Sequence[str]],
    configured: Mapping[str, object],
    plant_descriptions: PlantCopyProvider | None = None,
    plant_flavor: PlantCopyProvider | None = None,
) -> tuple[AlmanacChapter, ...]:
    chapters = []
    seen = set()
    for chapter_key, declared in declarations.items():
        declared_keys = tuple(str(key) for key in declared)
        entries = []
        for key in declared_keys:
            cfg = configured.get(key)
            if cfg is None:
                if category == "zombies" and key == "yeti":
                    continue
                raise KeyError(f"Missing declared {category} almanac key {key}")
            if key in seen:
                raise ValueError(f"Duplicate {category} almanac key {key}")
            if category == "plants":
                entry = _plant_entry(key, cfg, plant_descriptions, plant_flavor)
            else:
                entry = _zombie_entry(key, cfg)
            entries.append(entry)
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
    plant_descriptions: PlantCopyProvider | None = None,
    plant_flavor: PlantCopyProvider | None = None,
) -> AlmanacCatalog:
    return AlmanacCatalog(
        plant_chapters=_build_chapters(
            "plants",
            CLASSIC_PLANT_CHAPTERS,
            plants,
            plant_descriptions,
            plant_flavor,
        ),
        zombie_chapters=_build_chapters("zombies", CLASSIC_ZOMBIE_CHAPTERS, zombies),
    )
