"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos/
"""

import math
import time

import pyray as rl

from iqpilot.common.params import Params
from iqpilot.ui.onroad.big_model_status import SourceState, draw_source_label, resolve_source
from iqpilot.selfdrive.ui import UI_BORDER_SIZE
from iqpilot.selfdrive.ui.onroad.driver_state import BTN_SIZE
from iqpilot.selfdrive.ui.ui_state import ui_state
from iqpilot.system.ui.lib.application import FontWeight, gui_app
from iqpilot.system.ui.lib.text_measure import measure_text_cached
from iqpilot.system.ui.widgets import Widget

_POLL_S = 1.0
_FONT_SIZE = 70
_ICON_H = 76
_ICONS = {"MAC": ("mac", 62 / 46), "GPU": ("egpu", 1.0)}
_GREY = rl.Color(165, 165, 170, 235)


class EmacStatusRenderer(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._font = gui_app.font(FontWeight.SEMI_BOLD)
    self._last_poll = 0.0
    self._label = ""
    self._state = SourceState.HIDDEN
    self._icons: dict[str, dict[str, rl.Texture]] = {}

  def _icon_set(self, label: str) -> dict[str, rl.Texture] | None:
    spec = _ICONS.get(label)
    if spec is None:
      return None
    if label not in self._icons:
      base, aspect = spec
      w = int(_ICON_H * aspect)
      self._icons[label] = {
        "base": gui_app.texture(f"icons_mici/{base}.png", w, _ICON_H),
        "green": gui_app.texture(f"icons_mici/{base}_green.png", w, _ICON_H),
        "orange": gui_app.texture(f"icons_mici/{base}_orange.png", int(w * 1.26), _ICON_H),
      }
    return self._icons[label]

  def update(self):
    now = time.monotonic()
    if now - self._last_poll < _POLL_S:
      return
    self._last_poll = now
    self._label, self._state = resolve_source(self._params, ui_state.engaged)

  def _render(self, rect: rl.Rectangle):
    if self._state == SourceState.HIDDEN:
      return
    icons = self._icon_set(self._label)
    if icons is None:
      size = measure_text_cached(self._font, self._label, _FONT_SIZE)
      x = rect.x + UI_BORDER_SIZE + BTN_SIZE // 2 - size.x / 2
      y = rect.y + rect.height / 2 - size.y / 2
      draw_source_label(self._font, self._label, self._state, rl.Vector2(x, y), _FONT_SIZE)
      return
    if self._state == SourceState.ACTIVE:
      tex, tint = icons["green"], rl.Color(255, 255, 255, 255)
    elif self._state == SourceState.FAILED:
      tex, tint = icons["orange"], rl.Color(255, 255, 255, 255)
    elif self._state == SourceState.CROSSED:
      tex, tint = icons["base"], rl.Color(255, 255, 255, 165)
    else:
      pulse = 0.35 + 0.65 * (0.5 - 0.5 * math.cos(rl.get_time() * 6.0))
      tex, tint = icons["base"], rl.Color(_GREY.r, _GREY.g, _GREY.b, int(_GREY.a * pulse))
    x = int(rect.x + UI_BORDER_SIZE + BTN_SIZE // 2 - tex.width / 2)
    y = int(rect.y + rect.height / 2 - tex.height / 2)
    rl.draw_texture(tex, x, y, tint)
    if self._state == SourceState.CROSSED:
      cy = y + tex.height // 2
      rl.draw_line_ex(rl.Vector2(x - 4, cy), rl.Vector2(x + tex.width + 4, cy), 4, rl.Color(255, 255, 255, 165))
