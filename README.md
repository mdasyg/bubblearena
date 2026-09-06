# 🫧 BUBBLE ARENA - Game Design Document & Technical Specification

> **A fast-paced 4-player retro 2D single-screen arcade platform brawler inspired by *Bubble Bobble*, featuring competitive local & LAN multiplayer, chain-reaction bubble explosions, 14 arena stages, ready-checked lobbies, and in-game broadcast chat.**

---

## 📖 Table of Contents
1. [Game Overview](#-game-overview)
2. [Core Game Design & Pillars](#-core-game-design--pillars)
3. [Gameplay Mechanics & Controls](#-gameplay-mechanics--controls)
4. [Game Modes](#-game-modes)
5. [Arenas & Stage Themes](#-arenas--stage-themes)
6. [Items, Power-Ups & Collectibles](#-items-power-ups--collectibles)
7. [LAN Multiplayer & Networking Architecture](#-lan-multiplayer--networking-architecture)
8. [Codebase Architecture & Class Hierarchy](#-codebase-architecture--class-hierarchy)
9. [Installation, Running & Building](#-installation-running--building)
10. [Automated Test Suite](#-automated-test-suite)

---

## 🎮 Game Overview

**Bubble Arena** is an arcade-style competitive platformer built with **Python 3** and **Pygame 2**. Players take control of colorful dragon-like bubblers who trap opponents inside bubbles, ride bubbles to reach elevated platforms, and trigger cascading chain-reaction explosions to rack up high scores and claim victory.

- **Target Resolution:** Virtual screen at `480 × 320` scaled with crisp nearest-neighbor pixel preservation to `960 × 640` (2x window).
- **Target Frame Rate:** 60 FPS deterministic simulation.
- **Audio:** Custom procedural 8-bit chiptune sound synthesis and multi-voice dynamic background music without external asset dependencies.
- **Visuals:** High-contrast 16-color retro arcade palette with custom animated sprite-sheets and procedural fallbacks.

---

## 🏛️ Core Game Design & Pillars

1. **Classic Arcade Accessibility with High Skill Ceiling:**
   - Simple, responsive controls (WASD / Arrows + Jump + Shoot).
   - Advanced movement: bubble trampoline hopping, corner-cutting ledge jumps, jump buffering, and coyote grace time.
2. **Chain-Reaction Explosions:**
   - Popping a bubble triggers a cascade that detonates all touching and adjacent bubbles, awarding compounding combo multipliers (`x2`, `x3`, `x4+`).
3. **Dynamic Arena Flow:**
   - 3-minute global match timer.
   - At 30 seconds remaining, the game triggers a high-tempo **"HURRY UP!"** mode with fast music.
   - Random stage selection on match start and rematches.
4. **Cooperative & Competitive Versatility:**
   - Single keyboard 4-player local multiplayer.
   - Full LAN multiplayer with network adapter selection, 4-player ready check lobby, and broadcast chat.

---

## 🕹️ Gameplay Mechanics & Controls

### 1. Platforming & Movement
- **One-Way Platforms:** Players jump smoothly through platforms from underneath and land securely on top.
- **Jump Buffering (140ms):** Pressing jump right before touching the floor queues the jump for immediate execution upon landing.
- **Coyote Time (100ms):** Allows jumping for a brief fraction of a second after stepping off a platform ledge.

### 2. Bubble Physics & Trapping
- **Phase 1: Horizontal Shot:** Bubbles fire forward horizontally at high speed (`280 px/s`). Hitting an opponent traps them inside.
- **Phase 2: Buoyant Drift & Sway:** Once bubbles travel their distance or hit a side brick wall, they rise upward (`-35 px/s`) with sinusoidal sway.
- **Bubble Riding (Trampoline):** Players can land on top of any floating bubble to bounce upward and reach higher arena tiers.
- **Timeout & Struggle Escape:** Bubbles have a 30-second lifespan. Warning flashes begin at 24 seconds. Trapped players can mash action buttons to break out early.
- **Elimination & Teammate Rescue:**
  - **Opponent Pop:** Touching or head-butting an enemy trapped bubble eliminates the player (+1,000 pts).
  - **Teammate Rescue:** In 2v2 mode, touching a teammate's bubble instantly frees and shields them (+500 pts).

### 3. Controls Mapping

#### Single Keyboard 4-Player Layout:
| Player | Color | Movement | Jump | Shoot / Struggle | Action |
|---|---|---|---|---|---|
| **Player 1** | Green | `W, A, S, D` or `Arrows` | `SPACE`, `W`, `UP` | `F`, `J`, `Z`, `ENTER` | `G` |
| **Player 2** | Blue | `Arrow Keys` | `UP Arrow` | `K` | `L` |
| **Player 3** | Yellow | `I, J, K, L` | `I` | `U` | `O` |
| **Player 4** | Pink | `Numpad 8, 4, 5, 6` | `Numpad 8` | `Numpad 7` | `Numpad 9` |

#### Gamepad Support:
- Plug-and-play support for up to 4 standard USB / Bluetooth controllers:
  - **Move:** D-Pad or Left Analog Stick
  - **Jump:** `A` / Cross button
  - **Shoot / Struggle:** `X` / Square or `B` / Circle button

---

## 🏆 Game Modes

1. **Free-For-All (FFA):**
   - 4-player solo deathmatch. Every bubbler for themselves. Highest score when timer expires wins.
2. **2v2 Team Brawler:**
   - Team Green/Yellow vs. Team Blue/Pink. Friendly bubble pops rescue teammates with temporary shields.
3. **Capture The Flag (CTF):**
   - A golden flag spawns in the arena. Holding the flag awards accumulating points over time. Eliminating the flag-carrier forces a drop.
4. **Single-Player / Practice vs. AI Bots:**
   - Play locally against heuristic bots equipped with autonomous pathfinding, bubble-shooting, and bubble-riding logic.

---

## 🗺️ Arenas & Stage Themes

Bubble Arena features **14 handcrafted single-screen maps**, each featuring distinct platform configurations and visual themes:

1. **Emerald Meadow:** Classic multi-tiered grassland with central climbing gaps.
2. **Azure Castle:** Fortified stone battlements with tall side watchtowers.
3. **Neon Cyber Grid:** High-tech digital grid with narrow speed platforms.
4. **Dungeon Vault:** Heavy stone brick platforms and close-quarters combat lanes.
5. **Skyward Spire:** Vertical platform columns emphasizing bubble-riding ascension.
6. **Amethyst Cavern:** Crystal caverns with stepped diagonal walkways.
7. **Double Helix:** Intertwined winding ramps requiring precision jumping.
8. **Lava Forge:** Heated subterranean foundry with suspended platform bridges.
9. **Candy Factory:** Bright pastel confectionery ledges with wide float zones.
10. **Grand Champion Arena:** Symmetrical tournament stage designed for pure competitive combat.
11. **Coral Reef:** Deep-sea oceanic tiers with wide bubble drift currents.
12. **Haunted Manor:** Gothic Victorian architecture with floating platforms.
13. **Starry Cosmos:** Celestial platforms suspended in deep space.
14. **Mushroom Grove:** Organic fungal canopy with tiered caps.

---

## 🍬 Items, Power-Ups & Collectibles

Items spawn randomly during matches or drop from popped bubble chain explosions:

### Combat Power-Ups:
- 👟 **Fast Shoes (12s):** Increases movement speed by +40%.
- 🍬 **Blue Candy (15s):** Extends bubble shot horizontal distance by +60%.
- 🍭 **Yellow Candy (15s):** Enables rapid-fire shooting cooldown (`0.16s` vs `0.35s`).
- 🔮 **Purple Mega Candy (30s):** Shoots **2x Giant Bubbles** (`24px` radius) with massive capture hitboxes!
- ⭐ **Star Shield (6s):** Grants temporary invulnerability and auto-pops touching bubbles.

### Score Collectibles:
- 💎 **Diamond:** +2,500 pts
- 💠 **Ruby Gem:** +1,500 pts
- 🔔 **Golden Bell:** +2,000 pts
- 🍉 **Watermelon:** +800 pts
- 🍌 **Banana:** +700 pts
- 🍇 **Grapes:** +600 pts
- 🍎 **Red Apple:** +500 pts
- 🥕 **Carrot:** +400 pts

---

## 🌐 LAN Multiplayer & Networking Architecture

```
                       +-------------------------+
                       |    LAN Server (Host)    |
                       |  - Interface Selector   |
                       |  - UDP Discovery Beacon |
                       |  - TCP Non-Blocking Hub |
                       +------------+------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
+---------v---------+     +---------v---------+     +---------v---------+
|   Client 1 (P2)   |     |   Client 2 (P3)   |     |   Client 3 (P4)   |
| TCP Input & State |     | TCP Input & State |     | TCP Input & State |
+-------------------+     +-------------------+     +-------------------+
```

### 1. Network Interface Selection
- Automatically enumerates all available physical and virtual IPv4 interfaces (e.g. `192.168.0.100`, `10.100.101.10`, `127.0.0.1`).
- The host can cycle and bind to any specific network adapter from the LAN setup menu.
- Advertises the selected host address via UDP discovery beacons (`PORT 28889`).

### 2. Dedicated 4-Player Room Lobby & Ready System
- Hosting does not immediately launch into the game; instead, it enters the **LAN Room Lobby**.
- Displays 4 player slot cards (P1 Green, P2 Blue, P3 Yellow, P4 Pink) with connection state and ready status.
- Each human player toggles **`[READY]`** with `[R]` or `[SPACE]`.
- Host can fill open slots with AI Bots using `[B]`.
- **Match Auto-Start:** When all 4 slots are occupied and marked **`READY`**, the match starts synchronously for all players.

### 3. Generic Broadcast Chat
- Built-in real-time lobby chat.
- Players press `[TAB]` or `[C]` to focus the chat input bar, type messages (up to 32 characters), and press `[ENTER]` to send.
- Messages are broadcast to all connected clients and displayed with sender player colors.

---

## 📁 Codebase Architecture & Class Hierarchy

```
BubbleArena/
├── main.py                  # Application entrypoint & CLI argument parser
├── constants.py             # Global constants, physics, colors, keybindings, states
├── engine/
│   ├── game.py              # GameEngine: State machine, loop, collisions, rendering
│   ├── input_handler.py     # Keyboard & Gamepad polling, jump buffer, coyote timers
│   ├── sprites.py           # SpriteManager: Pixel-art generator & sheet slicer
│   ├── sound.py             # SoundManager: Procedural 8-bit sound synthesizer & BGM
│   └── particles.py         # ParticleManager: Floating combat text & pop bursts
├── entities/
│   ├── player.py            # Player entity: Platformer physics, animations, buffs
│   ├── bubble.py            # Bubble entity: Burst horizontal flight & float sway
│   ├── trapped_bubble.py    # TrappedBubble: Entrapment, struggle, pop elimination
│   ├── powerup.py           # PowerUp: Collectibles, fruits, candies, shields
│   └── flag.py              # Flag: Capture-The-Flag pickup & drop mechanics
├── levels/
│   ├── level_data.py        # ASCII matrix maps for all 14 stages
│   └── level_manager.py     # LevelManager: Map parsing, platforms, spawn points
├── modes/
│   ├── game_mode.py         # BaseGameMode: Common scoring & timer interface
│   ├── ffa_mode.py          # FFAMode: Solo free-for-all deathmatch rules
│   ├── team_mode.py         # TeamMode: 2v2 team brawler rules & rescue tracking
│   └── ctf_mode.py          # CTFMode: Flag-holding scoring & drop rules
├── network/
│   ├── protocol.py          # JSON newline-delimited packet serialization
│   ├── lan_server.py        # Non-blocking TCP server, lobby hub & UDP beacon
│   └── lan_client.py        # Non-blocking TCP client & discovery receiver
├── ui/
│   ├── hud.py               # HUD: Scores, timer, level name, hurry-up banners
│   └── menu.py              # MenuSystem: Title, mode select, level select, lobbies
└── tests/                   # Automated unittest suite (32 tests)
```

---

## 🚀 Installation, Running & Building

### Requirements
- Python 3.10+
- Pygame 2.5+ (`pip install pygame`)

### 1. Launch Main Menu
```bash
python main.py
```

### 2. Launch Local Bot Match
```bash
python main.py --bots --mode ffa --level 1
```

### 3. Build Standalone Windows Executable
To package the game as a single standalone `.exe` with all assets included:
```bash
pyinstaller --noconfirm --clean --onefile --name "BubbleArena" --add-data "assets;assets" --add-data "Animation;Animation" --collect-all pygame main.py
```
The resulting binary is generated in `dist/BubbleArena.exe`.

---

## 🧪 Automated Test Suite

Bubble Arena includes a comprehensive suite of 32 automated unit and integration tests:

```bash
python -m unittest discover tests
```

### Test Coverage:
- **`test_game.py`**: Physics, platform collisions, jump mechanics, one-way floors, scoring.
- **`test_boundaries_and_controls.py`**: Screen border containment, multi-key bindings, jump buffering.
- **`test_lan_lobby.py`**: Network adapter enumeration, ready state machine, broadcast chat, and trapped bubble elimination state.
- **`test_platform_edge.py`**: Platform edge boundary alignment and precision landing.
- **`test_sprites.py`**: Sprite sheet parsing and character frame animations.
- **`test_simulation.py`**: 150-frame end-to-end game simulation across all 3 game modes.
- **`test_bot_personalities.py`**: AI decision engine, personality archetypes (Aggressive, Passive, Standard), CTF retrieval/carrier delivery tactics, team rescue priorities, and bonus utility appraisal.
- **`test_player_count_and_lan_modes.py`**: Local human count ratios (1-4 players + bots), LAN game mode cycling & sync, and sound card silent-mode fallback.

---

## 🤖 Computer Player AI & Personalities

Bubble Arena features a dedicated decision engine ([`engine/bot_ai.py`](file:///c:/Temp/BubbleArena/engine/bot_ai.py)) with three distinct personality profiles:

| Personality | Combat Style | Bonus Appraisal | Game Mode Tactics |
| :--- | :--- | :--- | :--- |
| **Aggressive** | Relentlessly chases closest opponent; rapid bubble fire; prioritizes popping trapped foes | Pursues combat buffs (Shield, Giant Candy, Speed); **skips bonuses** when locked on an urgent target | **CTF**: Hunts enemy flag carrier relentlessly to force drop; charges defenders when escorting.<br>**Team**: Focuses on eliminating trapped enemies. |
| **Passive** | Keeps safe distance; flees if enemy is within 85px; uses defensive covering fire | High priority on **Star Shield**; **skips bonuses** if enemies are nearby; gathers safe items on empty tiers | **CTF**: Intercepts from elevated platforms; guards base; takes high stealth routes when carrying.<br>**Team**: High rescue priority for trapped allies. |
| **Standard** | Balanced tactical navigation; bubble bouncing; opportunist attacks | Balanced utility formula (`utility - distance`); detours for gems/candies $\ge 70$ utility | **CTF**: Balances flag grabbing, intercepting, and escorting.<br>**Team**: Rescues allies about to expire, else pops foes. |

---

## 🌐 Pushing to a Brand New Remote GitHub Repository

To share this codebase with other agents and developers via a new GitHub repository:

### Step 1: Create an Empty GitHub Repository
1. Log in to [GitHub](https://github.com) and click **New Repository** (or run `gh repo create BubbleArena --public`).
2. **Do NOT initialize** with a README, .gitignore, or license (the local repo already contains these).
3. Copy your repository's remote URL:
   - HTTPS: `https://github.com/<YOUR-USERNAME>/BubbleArena.git`
   - Or SSH: `git@github.com:<YOUR-USERNAME>/BubbleArena.git`

### Step 2: Ensure Git CLI is Installed on Your System
If `git` command is not recognized in your terminal, install Git for Windows:
```powershell
winget install --id Git.Git -e --source winget
```
*(After installing, open a new terminal window to refresh PATH)*.

### Step 3: Configure Remote Origin and Push
In your `c:\Temp\BubbleArena` directory, run:
```powershell
# 1. Ensure the default branch is named 'main'
git branch -M main

# 2. Add your remote repository origin
git remote add origin https://github.com/<YOUR-USERNAME>/BubbleArena.git

# 3. Push all commits and set upstream tracking
git push -u origin main
```

> [!TIP]
> If your local Git repository was managed using the bundled pure-Python Dulwich manager (`python git_tool.py`), running the standard `git` commands above will seamlessly read all existing commits and history.

### Step 4: Instructions for Cooperating Agents
Other agents or developers can immediately clone and run the project:
```bash
git clone https://github.com/<YOUR-USERNAME>/BubbleArena.git
cd BubbleArena
pip install pygame
python -m unittest discover tests
python main.py
```
