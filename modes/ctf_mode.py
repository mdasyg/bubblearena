"""
modes/ctf_mode.py - Capture The Flag arcade mode for Bubble Arena.
"""
from modes.base_mode import BaseGameMode
from constants import MODE_CTF, GLOBAL_MATCH_TIME, MIN_ROUND_DURATION

class CTFMode(BaseGameMode):
    """Capture The Flag mode: Fight for control of the golden flag."""
    def __init__(self, score_limit=20000, match_duration=GLOBAL_MATCH_TIME, min_round_duration=MIN_ROUND_DURATION):
        super().__init__(MODE_CTF, match_duration=match_duration, min_round_duration=min_round_duration)
        self.score_limit = score_limit

    def on_player_popped(self, popping_player, trapped_bubble, result_type, points):
        if result_type == "KILL":
            popping_player.kills += 1
            popping_player.score += points
        elif result_type == "RESCUE":
            popping_player.rescues += 1
            popping_player.score += points

    def update(self, dt, players, flag=None, sound_mgr=None):
        super().update(dt, players, flag, sound_mgr)
        if self.is_match_over:
            return

        # Check if any player hit the CTF score limit (only after guaranteed minimum round duration)
        if self.round_elapsed_time >= self.min_round_duration:
            for p in players:
                if p.score >= self.score_limit:
                    self.is_match_over = True
                    self.evaluate_winner(players)
                    if sound_mgr:
                        sound_mgr.play_sfx("victory")
                    break

    def evaluate_winner(self, players):
        if not players:
            self.winner_info = {"text": "NO CONTEST", "player_id": None}
            return

        sorted_players = sorted(players, key=lambda p: (p.score, p.kills, -p.deaths), reverse=True)
        winner = sorted_players[0]
        self.winner_info = {
            "text": f"{winner.name} WINS FLAG CARRIER CHAMPION!",
            "player_id": winner.id,
            "team": winner.team,
            "score": winner.score,
            "kills": winner.kills
        }
