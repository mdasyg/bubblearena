"""
engine/input_handler.py - Unified input manager supporting 4-player local keyboard, gamepads, AI bots, and LAN clients.
"""
import pygame
from constants import LOCAL_KEY_MAPPINGS

class InputHandler:
    """Collects and organizes inputs for up to 4 players."""
    def __init__(self):
        self.joysticks = []
        self._init_joysticks()
        self.remote_inputs = {}  # {player_id: action_dict}

    def _init_joysticks(self):
        """Initializes connected gamepads and controllers."""
        try:
            pygame.joystick.init()
            count = pygame.joystick.get_count()
            self.joysticks = [pygame.joystick.Joystick(i) for i in range(count)]
            for joy in self.joysticks:
                joy.init()
        except Exception as e:
            print(f"[InputHandler] Joystick init notice: {e}")

    def poll_inputs(self, player_id, is_bot=False, bot_action=None):
        """Returns action dictionary for the specified player_id."""
        if is_bot and bot_action:
            return bot_action

        # Check if remote LAN client provided input
        if player_id in self.remote_inputs:
            return self.remote_inputs[player_id]

        actions = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
            "jump": False,
            "shoot": False,
            "action": False,
            "struggle": False,
        }

        # 1. Keyboard Polling
        keys = pygame.key.get_pressed()
        keymap = LOCAL_KEY_MAPPINGS.get(player_id, {})
        for act, key_codes in keymap.items():
            if isinstance(key_codes, (list, tuple)):
                if any(keys[kc] for kc in key_codes if kc is not None):
                    actions[act] = True
            elif key_codes is not None and keys[key_codes]:
                actions[act] = True

        # 2. Gamepad Polling (if player has an assigned joystick)
        if player_id < len(self.joysticks):
            joy = self.joysticks[player_id]
            try:
                # Axis 0: Left Stick X
                axis_x = joy.get_axis(0)
                if axis_x < -0.3:
                    actions["left"] = True
                elif axis_x > 0.3:
                    actions["right"] = True

                # Axis 1: Left Stick Y
                axis_y = joy.get_axis(1)
                if axis_y < -0.3:
                    actions["up"] = True
                    actions["jump"] = True
                elif axis_y > 0.3:
                    actions["down"] = True

                # Buttons: A (0) = Jump, X (2) or B (1) = Shoot, Y (3) = Action
                if joy.get_button(0):  # Button A
                    actions["jump"] = True
                if joy.get_button(1) or joy.get_button(2):  # Button B or X
                    actions["shoot"] = True
                    actions["struggle"] = True
                if joy.get_button(3):  # Button Y
                    actions["action"] = True
            except Exception:
                pass

        return actions

    def set_remote_input(self, player_id, actions):
        """Sets input received over LAN socket."""
        self.remote_inputs[player_id] = actions
