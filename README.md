# 🫧 BUBBLE ARENA - 4-Player Retro 2D Arcade Brawler

A fast-paced retro 2D single-screen arcade platform brawler inspired by *Bubble Bobble*, built in Python with Pygame.

---

## 🎮 Features & Mechanics

1. **Snappy 2D Arcade Physics & One-Way Platforms:**
   - Jump through platforms from underneath. Land solidly on top.
2. **Horizontal Bubble Shooting & Trapping:**
   - Shoot bubbles horizontally to trap opponents into floating, swaying bubbles.
   - **Mega Giant Candy (30s):** Shoot 2x size giant bubbles for 30 seconds with wide capture hitboxes!
3. **Chain Bubble Popping & Combos:**
   - When a bubble is popped by a player, **all connected or touching bubbles explode in a cascade!**
   - Earn escalating Chain Combo multipliers (`x2`, `x3`, `x4+` combo bonuses).
4. **Bubble Riding & Trampoline Jumps:**
   - Jump on top of any floating bubble to bounce upward and reach higher platform tiers.
5. **Popping & Team Logic:**
   - **Opponent Pop:** Eliminates the enemy (+1000 pts) and causes them to respawn after a short delay with an invulnerability shield.
   - **Teammate Rescue (2v2 Mode):** Touch trapped allies to instantly rescue and shield them (+500 pts).
   - **30-Second Lifespan:** Bubbles flash and pop automatically after 30 seconds, freeing trapped players. Button mashing allows escaping early!
6. **Global 3-Minute Timer & 'Hurry Up!' Alert:**
   - 180-second countdown in the arcade HUD.
   - At 30 seconds remaining, triggers a flashing **"HURRY UP!"** banner and accelerated chiptune music tempo.
7. **Power-Ups & Collectible Bonus Fruits/Gems:**
   - 👟 **Fast Shoes**: +40% movement speed (12s).
   - 🍬 **Blue Candy**: Long-distance bubble shot (15s).
   - 🍭 **Yellow Candy**: Rapid-fire bubbles (15s).
   - 🔮 **Purple Mega Candy**: 2x Giant Bubbles for **30 seconds**!
   - ⭐ **Star Shield**: Invulnerability shield (6s).
   - 💎 **Diamond**: +2,500 bonus points!
   - 💠 **Ruby Gem**: +1,500 bonus points!
   - 🔔 **Golden Bell**: +2,000 bonus points!
   - 🍉 **Watermelon**: +800 bonus points!
   - 🍌 **Banana**: +700 bonus points!
   - 🍇 **Grapes**: +600 bonus points!
   - 🍎 **Red Apple**: +500 bonus points!
   - 🥕 **Carrot**: +400 bonus points!
8. **14 Handcrafted Retro Arena Levels & Random Map Flow:**
   - Matches start on a **random map**, cycling to the next random level on rematch!
   - Level 1: Emerald Meadow | Level 2: Azure Castle | Level 3: Neon Cyber Grid
   - Level 4: Dungeon Vault | Level 5: Skyward Spire | Level 6: Amethyst Cavern
   - Level 7: Double Helix | Level 8: Lava Forge | Level 9: Candy Factory
   - Level 10: Grand Champion Arena | Level 11: Coral Reef | Level 12: Haunted Manor
   - Level 13: Starry Cosmos | Level 14: Mushroom Grove
8. **3 Competitive Game Modes:**
   - ⚔️ **Free-For-All (FFA)**: 4-player solo deathmatch.
   - 🤝 **2v2 Team Brawler**: Team Green/Yellow vs Team Blue/Pink with friendly rescues.
   - 🚩 **Capture The Flag (CTF)**: Fight for control of the golden flag.
9. **Audio & Visuals:**
   - Procedural 8-bit chiptune sound synthesizer (SFX & dynamic multi-voice BGM).
   - Procedural 8-bit retro pixel-art sprite generator with animations for all 4 players, bubbles, tiles, and effects.

---

## 🕹️ Controls

### 4-Player Split Keyboard:
- **Player 1 (Green)**: `W, A, S, D` (Move/Jump) | `F` (Shoot / Struggle) | `G` (Action)
- **Player 2 (Blue)**: `Arrows` (Move/Jump) | `K` (Shoot / Struggle) | `L` (Action)
- **Player 3 (Yellow)**: `I, J, K, L` (Move/Jump) | `U` (Shoot / Struggle) | `O` (Action)
- **Player 4 (Pink)**: `Numpad 8, 4, 5, 6` (Move/Jump) | `Numpad 7` (Shoot / Struggle) | `Numpad 9` (Jump)

### Gamepad Support:
- Auto-detects up to 4 USB / Bluetooth controllers (`D-Pad/Stick` = Move, `A` = Jump, `X/B` = Shoot).

---

## 🚀 How to Run

### 1. Launch Game with Menu
```bash
python main.py
```

### 2. Instant 1-Player vs 3 AI Bots Match
```bash
python main.py --bots --mode ffa --level 1
```

### 3. Host a LAN Multiplayer Match
```bash
python main.py --host --mode team --level 2
```

### 4. Join a LAN Match
```bash
python main.py --join 192.168.1.15
```

### 5. Run Automated Tests
```bash
python -m unittest discover tests
```
