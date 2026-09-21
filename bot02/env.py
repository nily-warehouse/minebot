import math
import random
from collections import namedtuple

TURN_STEP = math.pi / 12

Decision   = namedtuple("Decision", "state action")
Transition = namedtuple("Transition", "state action reward next_state done")


class MinecraftEnv:
    COMMANDS = {
        "noop":
            {},
        "forward":
            {"controls": ("forward",)},
        "back":
            {"controls": ("back",)},
        "left":
            {"controls": ("left",)},
        "right":
            {"controls": ("right",)},
        "jump":
            {"controls": ("jump",)},
        "sprint_forward":
            {"controls": ("forward", "sprint")},
        "turn_left":
            {"dyaw": TURN_STEP},
        "turn_right":
            {"dyaw": -TURN_STEP},
        "look_up":
            {"dpitch": TURN_STEP},
        "look_down":
            {"dpitch": -TURN_STEP},
        "attack":
            {"attack": True},
    }
    ACTIONS = list(COMMANDS)

    def __init__(self, policy=None, reward_function=None, grid_radius=1, tick_every=2):

        self.policy = policy or (lambda state: random.randrange(self.n_actions))
        self.reward_function = reward_function or (lambda prev_state, state, done: 0)

        self.grid_radius = grid_radius

        self.tick_every = tick_every 
        # decide once every X game ticks

        self.transitions = []
        self._pending = None

    @property
    def n_actions(self):
        return len(self.ACTIONS)


    # --- steps ---

    def on_tick(self, state):
        self._finish_pending_step(state, done=False)
        action = self.policy(state)
        self._pending = Decision(state, action)
        return self.COMMANDS[self.ACTIONS[action]]

    def on_death(self, last_state=None):
        if self._pending is None:
            return
        final_state = self._pending.state or last_state
        self._finish_pending_step(final_state, done=True)

    def _finish_pending_step(self, next_state, done):
        if self._pending is None:
            return
        state, action = self._pending
        reward = self.reward_function(state, next_state, done)
        self.transitions.append(Transition(state, action, reward, next_state, done))
        self._pending = None