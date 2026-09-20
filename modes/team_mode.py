"""
modes/team_mode.py - 2v2 Team Brawler / Group Kill mode with friendly rescues and combined scores.
"""
from modes.base_mode import BaseGameMode
from constants import MODE_TEAM, GLOBAL_MATCH_TIME, MIN_ROUND_DURATION

class TeamMode(BaseGameMode):
    """2v2 Team Brawler: Team Green/Gold (0) vs Team Blue/Pink (1)."""
    def __init__(self, score_limit=15000, match_duration=GLOBAL_MATCH_TIME, min_round_duration=MIN_ROUND_DURATION):
        super().__init__(MODE_TEAM, match_duration=match_duration, min_round_duration=min_round_duration)
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

        # Check if either team reached the score limit after min_round_duration
        if self.round_elapsed_time >= self.min_round_duration:
            team0_score = sum(p.score for p in players if p.team == 0)
            team1_score = sum(p.score for p in players if p.team == 1)
            if team0_score >= self.score_limit or team1_score >= self.score_limit:
                self.is_match_over = True
                self.evaluate_winner(players)
                if sound_mgr:
                    sound_mgr.play_sfx("victory")

    def evaluate_winner(self, players):
        team_scores = {0: 0, 1: 0}
        team_kills = {0: 0, 1: 0}

        for p in players:
            team_scores[p.team] += p.score
            team_kills[p.team] += p.kills

        if team_scores[0] > team_scores[1]:
            winning_team = 0
            win_text = "TEAM GREEN / YELLOW WINS!"
        elif team_scores[1] > team_scores[0]:
            winning_team = 1
            win_text = "TEAM BLUE / PINK WINS!"
        else:
            winning_team = None
            win_text = "DRAW / TIE MATCH!"

        self.winner_info = {
            "text": win_text,
            "team": winning_team,
            "player_id": None,
            "team0_score": team_scores[0],
            "team1_score": team_scores[1]
        }
