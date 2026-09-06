"""
engine/bot_ai.py - AI Decision Engine for Computer Players in Bubble Arena.
Features distinct personalities (Aggressive, Passive, Standard), game-mode strategies
(FFA, 2v2 Team, Capture the Flag), and bonus/powerup utility appraisal.
"""
import math
import random
from constants import (
    BOT_PERSONALITY_AGGRESSIVE, BOT_PERSONALITY_PASSIVE, BOT_PERSONALITY_STANDARD,
    MODE_FFA, MODE_TEAM, MODE_CTF,
    POWERUP_SHIELD, POWERUP_PURPLE_CANDY, POWERUP_SHOES, POWERUP_YELLOW_CANDY,
    POWERUP_BLUE_CANDY, POWERUP_DIAMOND, POWERUP_GOLDEN_BELL, POWERUP_RUBY,
    POWERUP_WATERMELON, POWERUP_BANANA, POWERUP_GRAPES, POWERUP_APPLE, POWERUP_CARROT,
    POWERUP_FRUIT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT
)

# Utility scoring for powerups and collectibles (0 - 100)
ITEM_UTILITY = {
    POWERUP_SHIELD: 100,        # Star Shield (Invulnerability)
    POWERUP_PURPLE_CANDY: 95,   # Giant Bubble Candy (2x size bubbles)
    POWERUP_SHOES: 90,          # Speed Shoes
    POWERUP_YELLOW_CANDY: 85,   # Rapid Fire Candy
    POWERUP_BLUE_CANDY: 75,     # Long Shot Candy
    POWERUP_DIAMOND: 80,        # +2500 Points
    POWERUP_GOLDEN_BELL: 75,    # +2000 Points
    POWERUP_RUBY: 70,           # +1500 Points
    POWERUP_WATERMELON: 45,     # +800 Points
    POWERUP_FRUIT: 45,          # +800 Points
    POWERUP_BANANA: 40,         # +700 Points
    POWERUP_GRAPES: 35,         # +600 Points
    POWERUP_APPLE: 30,          # +500 Points
    POWERUP_CARROT: 25,         # +400 Points
}

class BotAI:
    """Evaluates the arena state and generates controls for a bot player."""

    @staticmethod
    def evaluate_best_bonus(bot, powerups, all_players, has_urgent_combat_target=False):
        """
        Judges available bonuses/powerups based on bot personality, distance, and current priorities.
        Returns the best PowerUp to collect, or None if the bot chooses to skip.
        """
        if not powerups:
            return None

        personality = bot.personality
        active_powerups = [p for p in powerups if p.is_alive]
        if not active_powerups:
            return None

        # AGGRESSIVE: Skip bonus if locked in combat with urgent objective
        if personality == BOT_PERSONALITY_AGGRESSIVE:
            if has_urgent_combat_target:
                return None  # Stays locked onto enemy/flag
            # Only pursues combat buffs or top-tier collectibles within medium range
            viable = []
            for p in active_powerups:
                score = ITEM_UTILITY.get(p.item_type, 30)
                dist = math.hypot(p.x - bot.x, p.y - bot.y)
                # Aggressive prefers combat items (shield, giant candy, speed, rapid)
                if score >= 80 and dist <= 180:
                    viable.append((p, score - dist * 0.2))
            if viable:
                viable.sort(key=lambda x: x[1], reverse=True)
                return viable[0][0]
            return None

        # PASSIVE: Values safety and Star Shield; skips bonus if aggressive enemies are near the item
        elif personality == BOT_PERSONALITY_PASSIVE:
            safe_items = []
            for p in active_powerups:
                dist = math.hypot(p.x - bot.x, p.y - bot.y)
                if dist > 240:
                    continue

                # Check if any enemy is camping or near the item
                enemy_near = False
                for opp in all_players:
                    if opp.id != bot.id and opp.is_alive and not opp.is_trapped:
                        opp_item_dist = math.hypot(opp.x - p.x, opp.y - p.y)
                        if opp_item_dist < 75:
                            enemy_near = True
                            break

                if enemy_near:
                    continue  # Skip dangerous bonus!

                score = ITEM_UTILITY.get(p.item_type, 30)
                # Shield is top priority for passive survival
                if p.item_type == POWERUP_SHIELD:
                    score += 50
                safe_items.append((p, score - dist * 0.3))

            if safe_items:
                safe_items.sort(key=lambda x: x[1], reverse=True)
                return safe_items[0][0]
            return None

        # STANDARD: Balanced tactical utility evaluation
        else:
            evaluated = []
            for p in active_powerups:
                dist = math.hypot(p.x - bot.x, p.y - bot.y)
                score = ITEM_UTILITY.get(p.item_type, 30)
                # High-tier items worth detouring up to 200px
                if score >= 70 and dist <= 210:
                    evaluated.append((p, score - dist * 0.25))
                elif score < 70 and dist <= 60:
                    # Low-tier items only if directly along current path
                    evaluated.append((p, score - dist * 0.5))

            if evaluated:
                evaluated.sort(key=lambda x: x[1], reverse=True)
                return evaluated[0][0]
            return None

    @classmethod
    def decide_action(cls, bot, dt, all_players, bubbles, trapped_bubbles, flag=None, powerups=None, game_mode=MODE_FFA, level_mgr=None):
        """
        Comprehensive decision engine executing mode tactics and personality quirks.
        """
        actions = {"left": False, "right": False, "jump": False, "shoot": False, "struggle": True}
        if not bot.is_bot or not bot.is_alive or bot.is_trapped:
            return actions

        personality = getattr(bot, "personality", BOT_PERSONALITY_STANDARD)

        # 1. CTF STRATEGY
        if game_mode == MODE_CTF and flag:
            target = cls._handle_ctf_tactics(bot, flag, all_players, personality)
            if target:
                target_x, target_y, force_shoot = target
                cls._steer_towards(bot, target_x, target_y, actions, personality)
                if force_shoot:
                    actions["shoot"] = True
                return actions

        # 2. 2v2 TEAM STRATEGY
        if game_mode == MODE_TEAM:
            team_target = cls._handle_team_tactics(bot, all_players, trapped_bubbles, personality)
            if team_target:
                target_x, target_y, shoot = team_target
                cls._steer_towards(bot, target_x, target_y, actions, personality)
                if shoot:
                    actions["shoot"] = True
                return actions

        # 3. FFA / STANDARD STRATEGY
        # Check for trapped bubbles to pop
        trapped_target = None
        for tb in trapped_bubbles:
            if tb.is_alive and tb.trapped_player.id != bot.id:
                # If team mode, only pop enemy trapped bubbles
                if game_mode == MODE_TEAM and tb.trapped_player.team == bot.team:
                    continue
                trapped_target = tb
                break

        has_urgent_target = (trapped_target is not None)

        # Bonus / PowerUp consideration
        best_bonus = cls.evaluate_best_bonus(bot, powerups, all_players, has_urgent_combat_target=has_urgent_target)

        target_x, target_y = None, None
        shoot_target = False

        if trapped_target and (personality == BOT_PERSONALITY_AGGRESSIVE or not best_bonus):
            target_x, target_y = trapped_target.x, trapped_target.y
        elif best_bonus:
            target_x, target_y = best_bonus.x, best_bonus.y
        else:
            # Target active opponents
            opponents = [p for p in all_players if p.id != bot.id and p.is_alive and not p.is_trapped]
            if game_mode == MODE_TEAM:
                opponents = [p for p in opponents if p.team != bot.team]

            if opponents:
                if personality == BOT_PERSONALITY_AGGRESSIVE:
                    # Aggressive targets closest enemy
                    closest = min(opponents, key=lambda p: (p.x - bot.x)**2 + (p.y - bot.y)**2)
                    target_x, target_y = closest.x, closest.y
                    shoot_target = True
                elif personality == BOT_PERSONALITY_PASSIVE:
                    # Passive stays away if enemy is too close
                    closest = min(opponents, key=lambda p: (p.x - bot.x)**2 + (p.y - bot.y)**2)
                    dist = math.hypot(closest.x - bot.x, closest.y - bot.y)
                    if dist < 85:
                        # Flee away from closest enemy!
                        flee_dir = -1 if closest.x > bot.x else 1
                        target_x = bot.x + flee_dir * 120
                        target_y = bot.y - 40  # Jump to higher platforms
                        actions["shoot"] = True  # Defensive covering fire
                    else:
                        target_x, target_y = closest.x, closest.y
                else:  # Standard
                    closest = min(opponents, key=lambda p: (p.x - bot.x)**2 + (p.y - bot.y)**2)
                    target_x, target_y = closest.x, closest.y
                    shoot_target = True

        if target_x is not None:
            cls._steer_towards(bot, target_x, target_y, actions, personality)
            if shoot_target and abs(target_y - bot.y) < 26 and random.random() < 0.65:
                facing_target = (target_x > bot.x and bot.facing > 0) or (target_x < bot.x and bot.facing < 0)
                if facing_target:
                    actions["shoot"] = True

        # Bubble riding: bounce off bubbles when below them
        for b in bubbles:
            if b.is_alive and b.is_floating:
                if abs(b.x - bot.x) < 18 and bot.y > b.rect.bottom and bot.y - b.rect.bottom < 40:
                    if bot.is_grounded:
                        actions["jump"] = True

        return actions

    @classmethod
    def _handle_ctf_tactics(cls, bot, flag, all_players, personality):
        """Dedicated CTF objective management: Flag carrier, Flag retrieval, and Home Base returns."""
        # Case A: Bot itself has the flag -> Deliver to home base!
        if flag.carrier == bot:
            home_x, home_y = bot.spawn_x, bot.spawn_y
            return (home_x, home_y, personality == BOT_PERSONALITY_AGGRESSIVE)

        # Case B: Flag is stolen by an enemy! -> Intercept and retrieve!
        if flag.carrier and flag.carrier.team != bot.team:
            carrier = flag.carrier
            # Relentlessly pursue carrier to pop him and force flag drop
            return (carrier.x, carrier.y, True)

        # Case C: Friendly teammate has the flag -> Escort carrier!
        if flag.carrier and flag.carrier.team == bot.team:
            carrier = flag.carrier
            if personality == BOT_PERSONALITY_AGGRESSIVE:
                # Rush ahead of friendly carrier to clear path
                lead_x = carrier.x + (60 if carrier.facing > 0 else -60)
                return (lead_x, carrier.y, True)
            else:
                # Escort close behind
                trail_x = carrier.x + (-30 if carrier.facing > 0 else 30)
                return (trail_x, carrier.y, False)

        # Case D: Flag is dropped or neutral on platform -> Grab the flag!
        return (flag.x, flag.y, False)

    @classmethod
    def _handle_team_tactics(cls, bot, all_players, trapped_bubbles, personality):
        """2v2 Team tactics: Coordinate ally rescues vs enemy trapped pops."""
        # Check for trapped allies
        trapped_ally = None
        trapped_enemy = None

        for tb in trapped_bubbles:
            if tb.is_alive:
                if tb.trapped_player.team == bot.team and tb.trapped_player.id != bot.id:
                    trapped_ally = tb
                elif tb.trapped_player.team != bot.team:
                    trapped_enemy = tb

        # PASSIVE: Rescues trapped teammate above all else
        if personality == BOT_PERSONALITY_PASSIVE and trapped_ally:
            return (trapped_ally.x, trapped_ally.y, False)

        # AGGRESSIVE: Pops trapped enemy first for kill; only rescues ally if no enemy trapped
        if personality == BOT_PERSONALITY_AGGRESSIVE:
            if trapped_enemy:
                return (trapped_enemy.x, trapped_enemy.y, True)
            if trapped_ally:
                return (trapped_ally.x, trapped_ally.y, False)

        # STANDARD: Rescues ally if ally is nearing timeout, otherwise eliminates enemy
        if trapped_ally and trapped_ally.lifespan < 10.0:
            return (trapped_ally.x, trapped_ally.y, False)
        if trapped_enemy:
            return (trapped_enemy.x, trapped_enemy.y, True)
        if trapped_ally:
            return (trapped_ally.x, trapped_ally.y, False)

        return None

    @staticmethod
    def _steer_towards(bot, target_x, target_y, actions, personality):
        """Steering and jump mechanics with personality adjustments."""
        dx = target_x - bot.x
        dy = target_y - bot.y

        deadzone = 8 if personality == BOT_PERSONALITY_AGGRESSIVE else 14
        if dx < -deadzone:
            actions["left"] = True
        elif dx > deadzone:
            actions["right"] = True

        # Vertical navigation: jump if target is on higher level
        if dy < -18 and bot.is_grounded:
            actions["jump"] = True

        # Random agility jump to prevent wall corners
        jump_rate = 0.10 if personality == BOT_PERSONALITY_AGGRESSIVE else (0.05 if personality == BOT_PERSONALITY_PASSIVE else 0.07)
        if bot.is_grounded and random.random() < jump_rate:
            actions["jump"] = True
