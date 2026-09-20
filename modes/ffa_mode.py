"""
modes/ffa_mode.py - Solo Free-For-All 4-player deathmatch mode.
"""
from modes.base_mode import BaseGameMode
from constants import MODE_FFA, GLOBAL_MATCH_TIME, MIN_ROUND_DURATION

class FFAMode(BaseGameMode):
    """4 individual players, every other player is an opponent."""
    def __init__(self, score_limit=20000, match_duration=GLOBAL_MATCH_TIME, min_round_duration=MIN_ROUND_DURATION):
        super().__init__(MODE_FFA, match_duration=match_duration, min_round_duration=min_round_duration)
        self.score_limit = score_limit

    def on_player_popped(self, popping_player, trapped_bubble, result_type, points):
        if result_type == "KILL":
            popping_player.kills += 1
            popping_player.score += points
            # Check score limit early win (only if guaranteed minimum round duration has elapsed)
            if popping_player.score >= self.score_limit and self.round_elapsed_time >= self.min_round_duration:
                self.is_match_over = True
                self.winner_info = {
                    "text": f"{popping_player.name} WINS!",
                    "player_id": popping_player.id,
                    "team": None,
                    "score": popping_player.score
                }

    def evaluate_winner(self, players):
        if not players:
            self.winner_info = {"text": "NO CONTEST", "player_id": None}
            return

        sorted_players = sorted(players, key=lambda p: (p.score, p.kills, -p.deaths), reverse=True)
        winner = sorted_players[0]
        self.winner_info = {
            "text": f"{winner.name} WINS!",
            "player_id": winner.id,
            "team": None,
            "score": winner.score,
            "kills": winner.kills
        }
