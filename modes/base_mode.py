"""
modes/base_mode.py - Base GameMode interface and shared match rule logic.
"""
from constants import GLOBAL_MATCH_TIME, HURRY_UP_TIME

class BaseGameMode:
    """Base class for all arcade match modes."""
    def __init__(self, name):
        self.name = name
        self.match_time_remaining = GLOBAL_MATCH_TIME  # 3 minutes (180s)
        self.is_hurry_up = False
        self.is_match_over = False
        self.winner_info = None

    def start_round(self, players):
        """Initializes match state for all players."""
        self.match_time_remaining = GLOBAL_MATCH_TIME
        self.is_hurry_up = False
        self.is_match_over = False
        self.winner_info = None
        for p in players:
            p.score = 0
            p.kills = 0
            p.deaths = 0
            p.rescues = 0
            p.flag_captures = 0

    def update(self, dt, players, flag=None, sound_mgr=None):
        """Updates match countdown timer and triggers Hurry Up alert."""
        if self.is_match_over:
            return

        self.match_time_remaining -= dt
        if self.match_time_remaining <= HURRY_UP_TIME and not self.is_hurry_up:
            self.is_hurry_up = True
            if sound_mgr:
                sound_mgr.play_sfx("hurry")
                sound_mgr.set_hurry_mode(True)

        if self.match_time_remaining <= 0.0:
            self.match_time_remaining = 0.0
            self.is_match_over = True
            self.evaluate_winner(players)
            if sound_mgr:
                sound_mgr.play_sfx("victory")

    def on_player_popped(self, popping_player, trapped_bubble, result_type, points):
        """Callback when a trapped bubble is popped."""
        pass

    def evaluate_winner(self, players):
        """Evaluates final winner based on mode rules."""
        raise NotImplementedError
