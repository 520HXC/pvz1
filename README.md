# Python PvZ Clone

A `pygame` Plants vs. Zombies inspired project that is being rebuilt toward the feel and structure of the original PvZ PC / GOTY version while keeping the art and implementation original.

This repo is no longer just a small prototype. The current branch already includes major campaign, menu, special-stage, and minigame refactors, with the remaining work focused on polishing mode accuracy, visuals, and unit behavior.

## Project Overview

- Built with `pygame`
- Default UI language is Simplified Chinese, with `EN / 中文` switching
- Uses original redraw / procedural fallback art instead of official PvZ asset files
- Keeps internal gameplay IDs in English and uses localized display text on top

## Current Status

### Core flows already working

- `Start -> Adventure / Mini-games / Puzzle / Survival -> Plant Select / Direct Special Entry -> Battle -> Result`
- Adventure has been rebuilt into **50 stages** from `1-1` to `5-10`
- The campaign now uses a **5-world structure**:
  - Day
  - Night
  - Pool
  - Fog
  - Roof

### Adventure progress

- Adventure stage select was rebuilt into:
  - chapter cover page
  - 10-stage photo-card page per world
- Adventure wave pacing was reworked away from endless time spawning into:
  - flag-based waves
  - world-aware zombie unlock order
  - wave-budget driven spawn queues
- Special Adventure stages now route by **stage style** instead of always forcing plant selection:
  - `normal_select`
  - `conveyor`
  - `bonus_special`
  - `boss_conveyor`

### Important special-stage changes already in place

- `5-10` now enters as a **boss conveyor battle** instead of normal plant selection
- `mini_dr_zomboss_revenge` also enters directly as a **boss conveyor** battle
- `4-5 Vasebreaker` uses vase-driven rules instead of normal Adventure waves
- `5-5 Bungee Blitz` is treated as a special roof conveyor stage
- `Last Stand` now has a **prep phase -> defense phase**
- `Zombiquarium` is no longer just a normal defense reskin and now centers its fish-zombie economy loop

## Mini-games / Puzzle / Survival Status

### Mini-games with dedicated rule work already done

- `Wall-nut Bowling`
- `Whack a Zombie`
- `Dr. Zomboss's Revenge`
- `Zombiquarium`
- `Last Stand`
- `Beghouled`
- `Beghouled Twist`
- `Seeing Stars`

### Puzzle modes

- `Vasebreaker`
  - plants revealed from vases are stored for manual placement
  - no longer auto-planted directly onto the revealed tile
- `I, Zombie`
  - uses fixed puzzle-style boards
  - keeps zombie-side sunlight economy logic

### Survival

- Survival pages and UI are present
- Survival structure is being pushed toward the original multi-round PvZ flow
- More round-to-round persistence and rule refinement is still in progress

## Special Stage Rules

The repo now distinguishes between normal plant-selection battles and special stage types.

Current examples:

- Adventure special stages no longer all share one generic entry flow
- Conveyor and boss-conveyor stages bypass normal `plant_select`
- Special minigames are increasingly using their own rule presets and overlays instead of generic battle tuning

## UI / UX Direction

Recent work has pushed the project toward a PvZ PC / GOTY style layout:

- Start menu reworked around a **main tombstone** style composition
- Adventure chapter page rebuilt as a **chapter booklet / cover page**
- Adventure level pages rebuilt into **photo-card style stage pages**
- `Mini / Puzzle / Survival` pages restyled as a **challenge booklet**
- Battle HUD reworked toward a **top seed-bank layout**
- Plant selection reworked toward a **PvZ-style seed chooser**

This project is using a **wide-screen adaptation of the original PvZ structure**, not a strict 4:3 black-bar recreation.

## Controls

- Left click:
  - buttons
  - packets / cards
  - tiles
  - scene interactions
- `O`: toggle in-battle settings panel
- `[` / `]`: decrease / increase game speed
- `P` or `Space`: pause / resume battle
- `R`: restart current level
- `A`: toggle almanac in battle
- `ESC`:
  - battle: open / close battle menu
  - other scenes: return to previous / main scene

## Saves / Config

- Progress: `save.json`
- Runtime settings: `config.json`

Runtime settings currently include:

- game speed
- auto collect options
- HP bar toggles
- wave UI toggles
- difficulty multipliers
- debug toggles

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the game:

```bash
python game.py
```

If you want to use the local Windows Python install directly:

```powershell
"C:\Users\huang\AppData\Local\Programs\Python\Python313\python.exe" game.py
```

## Art / Asset Policy

- This project does **not** rely on official PvZ art files in the repo
- The visual direction aims to be strongly inspired by PvZ1 while staying original
- If external art is missing, procedural / drawn fallback rendering keeps the project playable

## Known Gaps / Current Focus

The project is much further along than the original prototype, but it is **not finished**.

Current ongoing work includes:

- making more minigames match the original PvZ rules more closely
- continuing to refine special-stage pacing and world-specific difficulty
- improving unit behaviors and state changes to better match classic PvZ readability
- continuing to push UI proportions and scene composition closer to PvZ PC / GOTY
- polishing original redraw / fallback art so units and menus feel less placeholder-like

---

# Python PvZ 克隆项目

这是一个使用 `pygame` 开发的《植物大战僵尸》风格项目，目前正在持续朝 **原版 PvZ PC / GOTY 版的结构、节奏和界面体验** 收口，但仍坚持使用原创重绘和程序化回退，而不是直接使用官方素材文件。

这个仓库已经不只是早期原型。当前主分支已经完成了大量 Adventure、特殊关、小游戏规则和菜单/UI 重构，后续重点是继续把模式规则、单位行为和视觉细节做得更接近原版。

## 项目概述

- 基于 `pygame`
- 默认语言为**简体中文**
- 支持 `EN / 中文` 切换
- 内部逻辑 ID 保持英文，显示层再做本地化
- 美术方向为原创重绘 / 程序化回退，不使用官方 PvZ 资源文件

## 当前完成度

### 主流程已经打通

- `开始 -> Adventure / Mini-games / Puzzle / Survival -> 选卡或直接进入特殊关 -> 战斗 -> 结算`
- Adventure 已重构为 **50 关**：`1-1` 到 `5-10`
- Adventure 采用 **五个世界** 的结构：
  - 白天
  - 夜晚
  - 泳池
  - 迷雾
  - 屋顶

### Adventure 当前进度

- Adventure 选关已经改成：
  - 五章入口页
  - 每章 10 关的图片关卡页
- Adventure 刷怪和难度已经改成更接近原版的：
  - 旗帜波结构
  - 按世界推进的僵尸引入顺序
  - 基于波次预算的刷怪队列
- Adventure 关卡不再一律先进选卡，而是按 **关卡类型** 分流：
  - `normal_select`
  - `conveyor`
  - `bonus_special`
  - `boss_conveyor`

### 已经完成的重要特殊关纠偏

- `5-10` 已经改成 **Boss 传送带关**，不再先进选卡
- `mini_dr_zomboss_revenge` 也已经改成直接进入 **Boss conveyor**
- `4-5 Vasebreaker` 已按砸罐子规则运行，而不是普通 Adventure 波次
- `5-5 Bungee Blitz` 已改成特殊屋顶 conveyor 关
- `Last Stand` 已做成 **准备阶段 -> 防守阶段**
- `Zombiquarium` 已不再是普通守家换皮，而是以养鱼僵尸经济循环为主

## Mini-games / Puzzle / Survival 现状

### 已经有独立规则改造的小游戏

- `Wall-nut Bowling`
- `Whack a Zombie`
- `Dr. Zomboss's Revenge`
- `Zombiquarium`
- `Last Stand`
- `Beghouled`
- `Beghouled Twist`
- `Seeing Stars`

### Puzzle 模式

- `Vasebreaker`
  - 砸出植物后会进入临时库存
  - 不会再自动种到原地
- `I, Zombie`
  - 使用固定谜题式布局
  - 保留“僵尸方阳光经济”逻辑

### Survival

- Survival 页面和基础流程已经接上
- 目前正在继续向原版那种“多轮、保留草坪、轮间重选卡”的结构推进
- 轮次之间的衔接和压力曲线还在继续收口

## 特殊关与模式规则现状

现在项目已经明确区分：

- 普通选卡关
- 传送带关
- 特殊奖励关
- Boss 传送带关

这意味着：

- Adventure 特殊关不再都走同一条普通流程
- Conveyor / Boss conveyor 关会跳过正常 `plant_select`
- 越来越多小游戏会使用自己的规则预设和专用 HUD，而不是继续套普通 battle 数值

## UI 还原方向

最近这一批改动，重点是把项目的整体前端结构继续往原版 PvZ PC / GOTY 靠：

- 开始页改成以**主墓碑**为核心的布局
- Adventure 五章入口页改成更像**章节册页**
- Adventure 每章关卡页改成更像**图片关卡册页**
- `Mini / Puzzle / Survival` 改成更像**挑战菜单册页**
- 战斗 HUD 改成更像**顶部种子栏**
- 选卡页改成更像**原版 seed chooser**

这里采用的是 **宽屏适配下尽量还原原版结构** 的方向，不是硬做 4:3 黑边复刻。

## 操作说明

- 鼠标左键：
  - 按钮
  - 卡片 / 种子包
  - 草地格子
  - 场景交互
- `O`：打开 / 关闭战斗内设置面板
- `[` / `]`：降低 / 提高游戏速度
- `P` 或 `Space`：暂停 / 继续
- `R`：重开当前关卡
- `A`：战斗内打开 / 关闭图鉴
- `ESC`：
  - 战斗中：打开 / 关闭战斗菜单
  - 其它界面：返回上一级或主界面

## 存档与配置

- 进度存档：`save.json`
- 运行配置：`config.json`

当前运行配置包括：

- 游戏速度
- 自动收集选项
- 血条显示开关
- 波次 UI 开关
- 难度倍率
- 调试开关

## 运行方式

先安装依赖：

```bash
pip install -r requirements.txt
```

再运行游戏：

```bash
python game.py
```

如果你想直接用本机的 Windows Python：

```powershell
"C:\Users\huang\AppData\Local\Programs\Python\Python313\python.exe" game.py
```

## 美术与资源说明

- 仓库内不直接使用官方 PvZ 美术文件
- 视觉方向是“强烈受 PvZ1 启发的原创重绘”
- 如果外部美术缺失，程序化 / 自绘 fallback 仍会保证可玩

## 当前仍在继续补齐的部分

这个项目已经比最初原型完整很多，但**还没有完全做完**。

当前仍在继续推进的重点包括：

- 继续把剩下的小游戏规则体感往原版靠
- 继续收紧特殊关、世界后段和特殊模式的难度节奏
- 继续补单位状态机和行为反馈，让植物/僵尸更像原版
- 继续把 UI 比例、菜单语法和战斗界面往原版 PC / GOTY 压
- 继续提升原创重绘 / 程序化 fallback 的完成度，减少占位感
