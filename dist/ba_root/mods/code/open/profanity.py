# Released under the MIT License. See LICENSE for details.
# Created for gosquad server. By nΘΘbiliτγ.
#
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from unidecode import unidecode
from better_profanity import profanity
from extra.textmanager import TextManager

if TYPE_CHECKING:
    pass


custom = TextManager()
bad_words = custom.load('blacklist_words', 'blacklist.txt')
white_words = custom.load('whitelist_words', 'whitelist.txt')

profanity.load_censor_words(whitelist_words=white_words)
profanity.add_censor_words(custom_words=bad_words)


# Precompiled regex
_REPEAT_RE = re.compile(r'([a-z])\1+')


def _normalize(text: str) -> str:
    text = unidecode(text)
    text = _REPEAT_RE.sub(r'\1', text)

    return text


def censor_message(message: str) -> str:
    simple = _normalize(message)

    # If changed, return the censored
    if profanity.contains_profanity(simple):
        return profanity.censor(simple)

    return message


def is_bad_name(name: str) -> bool:
    simple = _normalize(name)
    return profanity.contains_profanity(simple)
