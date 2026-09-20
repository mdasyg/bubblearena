# AGENTS.md

## Project Identity

- **Project Name:** Bubble Arena
- **Purpose:** Fast-paced retro 2D single-screen 4-player arcade platform brawler inspired by *Bubble Bobble*, featuring competitive local & LAN/Internet multiplayer, a headless dedicated Linux/FreeBSD console server, CPU bot personalities, and cascading chain-reaction bubble explosions.
- **Current Phase:** Feature-complete arcade core; active refinement, network interpolation, bugfixing, and dedicated server maintenance.
- **Primary Branch:** `main` (Remote: `https://github.com/mdasyg/bubblearena.git`)

## Tech Stack & Environment

- **Language:** Python 3.10+ (Current runtime: Python 3.12.10 64-bit on Windows)
- **Game Framework / Engine:** Pygame 2.5+ (Pygame 2.6.1 / SDL 2.28.4)
- **Networking:** Pure Python standard library (`socket`, `select`, `threading`, `json`). Zero GUI/audio dependency for headless dedicated server.
- **Packaging / Distribution:** PyInstaller (standalone Windows onefile binary in `./Releases/BubbleArena.exe`).
- **Version Control:** Custom Python Git tool via Dulwich & subprocess fallback (`python git_tool.py <cmd>`).

## Build & Run

### 1. Dependencies Installation
```bash
pip install pygame pyinstaller dulwich
```

### 2. Running Game Client (Local / LAN / Internet)
```bash
# Launch interactive graphical client & menus
python main.py

# Direct connect to a LAN or Internet dedicated server
python main.py --join 127.0.0.1:28888
python main.py --join 83.212.19.100:28888
```

### 3. Running Headless Dedicated Console Server
```bash
# Standalone dedicated server (Linux, FreeBSD, Windows, macOS)
python bubblearena_server.py -i 0.0.0.0 -p 28888 --no-beacon

# With custom initial mode and stage level
python bubblearena_server.py -i 0.0.0.0 -p 28888 -m team -l 5 --no-beacon
```

### 4. Running Automated Unit Test Suite
```bash
python -m unittest discover tests
```

### 5. Compiling & Publishing Releases (GitHub Releases)
```powershell
# 1. Compile Windows client binary
pyinstaller --noconfirm --clean --onefile --name "BubbleArena" --add-data "assets;assets" --add-data "Animation;Animation" --collect-all pygame main.py
Copy-Item -Force "dist\BubbleArena.exe" "Releases\BubbleArena.exe"

# 2. Publish to GitHub Releases (Windows PowerShell or Linux bash)
.\release-push.ps1
# or on Linux / Git Bash:
./release-push.sh
```

### 6. Version Control Commands
```bash
python git_tool.py pull
python git_tool.py commit "Your commit message"
python git_tool.py push
```

## Architecture Snapshot

- **Virtual Resolution & Scaling:** Internal game canvas is fixed at `480 x 320` (`VIRTUAL_WIDTH`, `VIRTUAL_HEIGHT`), rendered to a `960 x 640` window (`SCREEN_WIDTH`, `SCREEN_HEIGHT`) using nearest-neighbor pixel preservation. All gameplay logic, platform boundaries, and projectile physics operate strictly in virtual coordinates.
- **Game Loop & Speed Multipliers:** Fixed 60 FPS target loop with delta-time tunneling caps (`min(dt, 0.05)`). Gameplay speed multiplier (`self.game_speed_mult`: `0.8x`, `1.0x`, `1.25x`) scales in-game physics, timers, and cooldowns during `STATE_PLAYING`, while menu and UI animations remain at constant 60 FPS.
- **Audio Subsystem (`engine/sound.py`):** Procedural 8-bit chiptune sound synthesis and dynamic BGM without external audio asset dependencies. Includes a silent fallback guard if WASAPI/SDL audio endpoints are missing or fail.
- **Entity Subsystems:**
  - `Player` (`entities/player.py`): Responsive platformer physics, 1-way platform jump-through, 140ms jump buffer, 100ms coyote grace time, state animations, and shooting.
  - `Bubble` (`entities/bubble.py`): Phase 1 horizontal burst (`280px/s`), Phase 2 buoyant sinusoidal float (`-35px/s`), 30-second lifespan with 24s warning flash, and trampoline bounce physics.
  - `TrappedBubble` (`entities/trapped_bubble.py`): Wraps trapped player, float drift, struggle counter (16 presses to escape), teammate rescue (shield) vs opponent elimination (pop/kill).
  - `PowerUp` (`entities/powerup.py`): Candies (blue range, yellow rapid fire, purple 2x giant), fast shoes, star shield, bonus fruits, and gems.
  - `Flag` (`entities/flag.py`): Capture-The-Flag banner, pickup/drop mechanics, and carrier tracking.
- **Match Modes & Multi-Round Flow:**
  - Modes inherit from `BaseGameMode` (`modes/base_mode.py`): `FFAMode`, `TeamMode`, `CTFMode`.
  - Multi-round matches support configurable rounds (1-10, default 4). `BaseGameMode.start_round(reset_scores=False)` preserves cumulative scores, kills, deaths, and rescues across rounds.
- **Unified Network Architecture:**
  - `network/protocol.py`: Line-delimited JSON wire protocol (`MSG_HELLO`, `MSG_WELCOME`, `MSG_LOBBY_STATE`, `MSG_READY`, `MSG_CHAT`, `MSG_MATCH_START`, `MSG_INPUT`, `MSG_STATE`, `MSG_PING`, `MSG_PONG`, `MSG_KICK`).
  - `network/server_core.py`: `BaseBubbleServer` engine supporting non-blocking `select`, live ping RTT latency calculation, 4-slot management, IP blacklist/ban filtering, and broadcast chat relay.
  - `network/lan_server.py`: Subclasses `BaseBubbleServer` for local listen-hosts with UDP discovery beacons (`PORT 28889`).
  - `network/lan_client.py`: Client connection manager, background packet reader thread, and ping responder.
  - `bubblearena_server.py`: Headless dedicated console server with interactive administrative shell (`ConsoleManager`).
- **UI & HUD Subsystems:**
  - `ui/menu.py`: Title screen, player count select, mode select, 14-stage 2x7 level select grid, game settings (speed + rounds), LAN interface & room lobbies with broadcast chat, and victory screen scoreboard.
  - `ui/hud.py`: Top arcade HUD displaying player scores, match timer, hurry-up alert, and round indicators (`RND X/Y`).

## Repository Map

- `main.py`: Client entrypoint and CLI argument parser.
- `bubblearena_server.py`: Standalone headless dedicated console server for Linux/FreeBSD/Windows.
- `constants.py`: Central configuration, physics constants, speed multipliers, color palette, keybindings, network ports.
- `git_tool.py`: Local Git version control helper script (Dulwich + CLI fallback).
- `build_exe.bat`: Batch script to build standalone Windows client executable.
- `engine/`:
  - `game.py`: `GameEngine` orchestrating loop, state machine, collisions, chain pops, round transitions.
  - `bot_ai.py`: `BotAI` implementing Aggressive, Passive, and Standard personality behaviors.
  - `input_handler.py`: Unified keyboard & gamepad polling with buffering.
  - `sound.py`: Procedural synth, SFX generator, and silent mode guard.
  - `sprites.py`: Sprite sheet parsing, procedural sprite fallbacks, and animation frame cache.
  - `particles.py`: Particle effects, pop bursts, dust, floating combat text.
- `entities/`: `player.py`, `bubble.py`, `trapped_bubble.py`, `powerup.py`, `flag.py`.
- `levels/`:
  - `level_data.py`: ASCII tilemaps for all 14 stages.
  - `level_manager.py`: Level loader, platform collision builder, spawn point parser.
- `modes/`: `base_mode.py`, `ffa_mode.py`, `team_mode.py`, `ctf_mode.py`.
- `network/`: `protocol.py`, `server_core.py`, `lan_server.py`, `lan_client.py`.
- `ui/`: `menu.py` (MenuSystem), `hud.py` (HUD).
- `assets/`: Spritesheets, sliced frames, audio resources.
- `Animation/`: Raw source dragon spritesheets.
- `tools/`: Build scripts (`build_player_animations.py`).
- `tests/`: 11 test files, 78 automated unit tests (`test_bubble_mechanics.py`).
- `Releases/`: Distributable standalone Windows executable (`BubbleArena.exe`).

## Development Rules

- **Git Protocol**: ALWAYS run `python git_tool.py pull` before modifying code, and `python git_tool.py push` after completing work and passing all tests.
- **Client Executable Distribution**: Binaries (`Releases/`, `dist/`, `*.exe`) MUST NEVER be committed to Git. The `Releases/` folder is gitignored. Standalone binaries are published exclusively via GitHub Releases using `release-push.sh` or `release-push.ps1`.
- **Minimal Dedicated Server Footprint**: The dedicated server (`bubblearena_server.py`) MUST remain 100% headless with zero dependencies on Pygame, SDL, or graphic assets. Only 4 files required: `bubblearena_server.py`, `constants.py`, `network/protocol.py`, `network/server_core.py` (and an empty `network/__init__.py`). Total footprint must remain under 50 KB.
- **Resolution & Scaling**: Virtual canvas is fixed at `480 x 320`. Never change native physics coordinates or draw directly in window coordinates.
- **Testing Integrity**: Every new feature or bugfix MUST include unit tests in `tests/`. All 78 existing tests must remain passing. Run `python -m unittest discover tests`.
- **Sprite Orientation Standard**: All base dragon sprite frames (`idle`, `walk`, `jump`, `fall`, `shoot`) stored on disk MUST face RIGHT by default. Runtime flip logic (`if facing < 0: pygame.transform.flip(...)`) expects right-facing base frames.
- **Silent Mode Compatibility**: Never assume an audio endpoint exists. `SoundManager` must never crash when WASAPI/SDL audio is unavailable.
- **Code Reuse**: Never duplicate server logic between `bubblearena_server.py` and `lan_server.py`; both must inherit from `network.server_core.BaseBubbleServer`.

## Current State

- **Authentic Retro Arcade Pacing:** Calibrated player speed (`105.0px/s`), smoothed ground acceleration (`800.0px/s²`), softened gravity (`640.0px/s²`), floaty jump impulse (`-260.0px/s`), and bubble burst speed (`220.0px/s`) for genuine classic *Bubble Bobble* platformer feel.
- **Bubble Trampoline & Vertical Column Climbing:** Players can land on and bounce off any floating bubble (own or other players') continuously without breaking them. Holding or buffering Jump delivers a boosted super-bounce (`BUBBLE_BOUNCE_SPEED * 1.15`). Players pass smoothly through bubbles from below, enabling vertical bubble stream climbing to arena ceilings. Empty bubbles never pop on player contact.
- **Trapped Player Retention (Anti Self-Break):** Trapped players (CPU bots and humans) cannot break their own bubble through button mashing or struggle counters. Only another player can pop the bubble (opponents eliminate for +1000 pts and bounce upward; teammates rescue for +500 pts with invulnerability shield).
- **Comprehensive Game Settings Customization (v1.1.0):** 8-option settings menu allowing players to toggle BGM music volume (Off / Low 35% / Normal 100%), SFX volume, customizable minimum stage duration (0s, 30s, 45s, 60s, 90s), round time limit (60s, 90s, 120s, 180s), bot opponent profiles (Mixed, All Aggressive, All Passive, All Standard), game speed multiplier (0.8x, 1.0x, 1.25x), and match rounds (1-10).
- **CPU Bot Deliberation & Jump Cooldown:** Bot jump cooldown timer (`0.5s - 1.4s`) and widened horizontal steering deadzones eliminate frantic spasms and twitch jumping.
- **Guaranteed Minimum Stage Duration:** Protects rounds from premature endings upon player elimination or early score milestones, fully customizable from 0s to 90s across all game modes.
- **Dynamic Platform Respawns:** `LevelManager.get_distinct_platform_spawns()` randomly spreads characters across arena platforms at match/round start and upon player death respawns instead of predictable static slot coordinates.
- **14 Arena Stages Grid:** All 14 stages cleanly selectable in a 2-column x 7-row interactive grid with arrow navigation.
- **Multi-Round Flow & Scoring:** Cumulative player scores, kills, deaths, and rescues persist across rounds. Top HUD shows `RND X/Y`. Mid-match transition banners announce upcoming rounds.
- **Headless Dedicated Server:** Standalone console server with interactive CLI shell (`status`, `players`, `kick`, `ban`, `mode`, `level`, `bot`, `say`, etc.) and live ping RTT latency calculation.
- **Automated Tests:** 78/78 automated unit tests passing across 11 test suites.
- **Release Executable:** Pre-compiled standalone Windows binary updated in `./Releases/BubbleArena.exe`.

## Active Priorities

1. **Network Input & State Interpolation:** Enhance client-side prediction and server state interpolation for high-latency WAN connections.
2. **Arcade Survival Mode (`MODE_SURVIVAL`):** Implement cooperative PVE wave defense mode with escalating enemy monster spawns.
3. **Dedicated Server Remote Webhook / REST API:** Optional lightweight HTTP monitoring endpoint for server metrics and web dashboards.
4. **Custom Gamepad Remapping:** In-game controls screen option to rebind gamepad buttons.

## Recent Architectural Decisions

1. **Bubble Trampoline & Vertical Climbing Mechanics**: Removed unintended player-upward collision popping from `engine/game.py`; empty bubbles never pop on player contact and remain floating. Implemented one-way vertical ascent pass-through so players can jump through bubbles from below, reach apex, and bounce off top surfaces repeatedly to climb stacks.
2. **Trapped Player Retention & Anti Self-Break**: Removed `struggle_count` escape thresholds and age acceleration from `TrappedBubble` and ensured `check_pop_by_player` returns `None` for self-pop attempts. Trapped players stay trapped for the full 30s lifespan unless popped by another player. Popping players receive an upward trampoline bounce when landing on an enemy trapped bubble from above.
3. **Retro Arcade Platformer Calibration**: Tuned physics to match authentic arcade gameplay tempo rather than twitchy hyper-speed; reduced jump frequency of bots through cooldown throttles and deadzones.
4. **Minimum Round Duration Guarantee (`MIN_ROUND_DURATION = 45.0s`)**: Guarded score limit triggers in `FFAMode` and `CTFMode` behind `round_elapsed_time >= min_round_duration` to prevent jarring premature stage switches right after player deaths.
5. **Dynamic Platform Spawn Allocation (`get_distinct_platform_spawns`)**: Filtered out exterior arena border walls from candidate platforms and ensured random, well-spaced placement across multiple platform tiers.
6. **Unified Server Core (`network/server_core.py`)**: Extracted `BaseBubbleServer` so both local listen-hosts and remote dedicated servers share identical packet parsing, slot assignment, client tracking, and ping calculation logic without code duplication.

## Important Files

- `main.py`: Graphical client entrypoint and CLI argument dispatcher.
- `bubblearena_server.py`: Standalone headless dedicated console server for Linux/FreeBSD.
- `constants.py`: Central source of truth for physics, gameplay limits, states, and speed options.
- `engine/game.py`: Core game engine, update loops, collision handlers, and rendering pipeline.
- `engine/bot_ai.py`: Heuristic AI decision engine for Aggressive, Passive, and Standard bots.
- `entities/player.py`: Dragon entity handling movement, collision rects, and shooting.
- `entities/bubble.py`: Bubble entity with 2-phase physics and trampoline bounce.
- `entities/trapped_bubble.py`: Entrapment logic, struggle counters, teammate rescues, and opponent pops.
- `network/server_core.py`: Shared base server engine with non-blocking socket loops and admin handlers.
- `network/protocol.py`: Wire protocol specification and packet serialization.
- `ui/menu.py`: UI system containing all menu screens, grids, lobbies, and justified victory tables.
- `ui/hud.py`: Top arcade HUD displaying scores, timer, hurry-up alert, and round indicators.
- `git_tool.py`: Version control manager enforcing pull-first push-last workflow.

## Known Risks

- **Pygame Window Scaling on HiDPI Displays**: Integer 2x scaling (`480 x 320` to `960 x 640`) must maintain nearest-neighbor interpolation to prevent blur on fractional Windows scaling.
- **WAN Socket Packet Timing**: Non-blocking TCP sockets handle bursts cleanly on LAN; high-latency WAN connections should be tested with simulated packet jitter.
- **Release Binary Hosting**: Executable binaries are gitignored and published to GitHub Releases via `release-push.sh` / `release-push.ps1`, preserving a lightweight (~7 MB) repository footprint.

## Next Session Handoff

- **Where to continue**: Read `AGENTS.md` first. Next focus is network gameplay state interpolation for remote clients and exploring Survival wave mode.
- **First file to open**: `engine/game.py` for gameplay state or `network/server_core.py` for network synchronization.
- **Immediate verification step**: Run `python -m unittest discover tests` to ensure all 64 tests pass before making any changes.
- **What NOT to change without reason**:
  - Do not introduce Pygame imports into `bubblearena_server.py` or `network/server_core.py`.
  - Do not alter the `480 x 320` virtual canvas resolution.
  - Do not bypass the `git_tool.py` pull/push workflow.
