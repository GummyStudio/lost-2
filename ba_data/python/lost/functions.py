"""Helpful functions."""
import bascenev1 as bs
from dataclasses import dataclass

@dataclass
class PlayerInfoPlus:
    """A class that can hold a lot of player's info."""
    name: str
    color: tuple[float]
    highlight: tuple[float]
    character: str

def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(
            lerp(x, y, t)
            for x, y in zip(a, b)
        )
    return a + (b - a) * t

def assignspazinput(spaz, player):
    player.resetinput()
    player.assigninput(
        bs.InputType.LEFT_RIGHT, spaz.on_move_left_right
    )
    player.assigninput(
        bs.InputType.UP_DOWN, spaz.on_move_up_down
    )
    player.assigninput(bs.InputType.RUN, spaz.on_run)
    player.assigninput(
        bs.InputType.BOMB_PRESS, spaz.on_bomb_press
    )
    player.assigninput(
        bs.InputType.BOMB_RELEASE, spaz.on_bomb_release
    )
    player.assigninput(
        bs.InputType.PICK_UP_PRESS, spaz.on_pickup_press
    )
    player.assigninput(
        bs.InputType.PICK_UP_RELEASE, spaz.on_pickup_release
    )
    player.assigninput(
        bs.InputType.PUNCH_PRESS, spaz.on_punch_press
    )
    player.assigninput(
        bs.InputType.PUNCH_RELEASE, spaz.on_punch_release
    )
    player.assigninput(
        bs.InputType.JUMP_PRESS, spaz.on_jump_press
    )
    player.assigninput(
        bs.InputType.JUMP_RELEASE, spaz.on_jump_release
    )


def choppify(keys, fps=30):
    """Given keyframes {time: value}, returns a new dict with
    more choppy-ish keyframes based on FPS arg."""
    times = sorted(keys)

    def sample(t):
        for i in range(len(times) - 1):
            t1, t2 = times[i], times[i + 1]

            if t1 <= t <= t2:
                v1 = keys[t1]
                v2 = keys[t2]

                frac = (t - t1) / (t2 - t1)

                # Number interpolation.
                if isinstance(v1, (int, float)):
                    return lerp(v1, v2, frac)

                # Tuple/list interpolation.
                return type(v1)(
                    lerp(a, b, frac)
                    for a, b in zip(v1, v2)
                )

        return keys[times[-1]]

    result = {}
    dt = 1.0 / fps
    duration = times[-1]

    t = 0.0
    while t < duration:
        value = sample(t)

        result[t] = value
        result[min(t + dt - 0.0001, duration)] = value

        t += dt

    result[duration] = keys[duration]
    return result