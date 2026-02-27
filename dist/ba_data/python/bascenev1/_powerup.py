# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from gocommon.gosetting import getsetting
if TYPE_CHECKING:from collections.abc import Sequence;import bascenev1
@dataclass
class PowerupMessage:poweruptype:str;sourcenode:bascenev1.Node|None=None
@dataclass
class PowerupAcceptMessage:0
powerup_distribution=None
def _get_default_powerup_distribution():powerup_setting=getsetting().get('powerupSettings',[]);return[(item['name'],item['count'])for item in powerup_setting]
def get_default_powerup_distribution():
	global powerup_distribution
	if powerup_distribution is None:powerup_distribution=tuple(_get_default_powerup_distribution())
	return powerup_distribution
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._powerup');addition=['get_default_powerup_distribution']
	for name in addition:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])