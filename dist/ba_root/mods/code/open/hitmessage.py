# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.actor.popuptext import PopupText
from extra.textmanager import textlist

if TYPE_CHECKING:
    from collections.abc import Sequence


hit_time = -9999
messages = []


def handle_hit(pos: Sequence[float], vel: Sequence[float], mag: float):
    time = bs.time()
    global messages, hit_time
    if mag <= 250.0 or (time - hit_time) < 2:
        return

    if not messages:
        messages = textlist.getall('hit_messages')

    hit_time = time
    text = 'NOOB'
    scale = 1.0

    if 701.0 <= mag < 2500.0:
        text = f'\ue043{random.choice(messages)}\ue043'
        scale = 1.8
    elif 551.0 <= mag < 700.0:
        text = f'\ue048{random.choice(messages)}\ue048'
        scale = 1.6
    elif 451.0 <= mag < 550.0:
        text = '\ue04fIMPRESSIVE!\ue04f'
        scale = 1.4
    elif 351.0 <= mag < 450.0:
        text = '\ue049GREAT!\ue049'
        scale = 1.2
    elif 251.0 <= mag < 350.0:
        text = '\ue04cGOOD!\ue04c'
        scale = 1.2
    elif 101.0 <= mag < 250.0:
        text = 'OOPSIE WOOPSIE!'
        scale = 1.0
    else:
        # Just in case
        text = 'NOOB'
        scale = 1.0

    pos = pos if pos is not None else bs.Vec3()
    PopupText(
        text,
        position=(
            pos[0] + random.uniform(-1.5, 1.5),
            pos[1] + random.uniform(0.5, 1.0),
            pos[2],
        ),
        color=get_random_color(),
        scale=scale,
    ).autoretain()

    if mag < 551:
        return

    bs.emitfx(
        position=pos,
        velocity=vel if vel is not None else bs.Vec3(),
        count=15 + int(mag / 40),
        scale=random.uniform(0.5, 1.0),
        spread=float(mag / 500),
        chunk_type=random.choice(
            ['spark', 'slime', 'metal', 'ice', 'splinter']
        ),
    )


def get_random_color() -> Sequence[float]:
    return bs.safecolor((random.random(), random.random(), random.random()))


class HitMessage(bs.HitMessage):
    def __init__(self, *args, **kwargs):
        if kwargs['hit_type'] == 'punch':
            handle_hit(kwargs['pos'], kwargs['velocity'], kwargs['magnitude'])
        super().__init__(*args, **kwargs)
