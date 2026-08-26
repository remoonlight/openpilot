"""mici settings: primary「蓝牙」one-tap toggle + status color (no secondary panel).

Params: IqlinkEnabled, IqlinkBleLinkState, IqlinkBleConnected,
IqlinkBlePeerConnected, IqlinkBlePairFailed.

Lamp: see iqpilot.selfdrive.ui.lib.iqlink_status
PSK is fixed and not shown on the primary tile.
"""

from __future__ import annotations

import pyray as rl

from iqpilot.common.params import Params, UnknownKeyName
from iqpilot.selfdrive.ui.lib.iqlink_status import iqlink_hmac_up, iqlink_status_color
from iqpilot.selfdrive.ui.mici.widgets.stock_button import BigButton
from iqpilot.system.ui.lib.application import gui_app, MousePos
from iqpilot.system.ui.lib.multilang import multilang, tr as mici_tr

def mici_register_button(_button):
  pass


def iqlink_tile_label() -> str:
  """Settings tile is Bluetooth; zh catalog may not include the iqlink msgid."""
  text = mici_tr("Bluetooth")
  lang = str(getattr(multilang, "language", "") or "")
  if lang.startswith("zh") and text == "Bluetooth":
    return "蓝牙"
  return text


class IqlinkBigButton(BigButton):
  """Primary settings tile: tap toggles IqlinkEnabled; corner lamp = link status."""

  def __init__(self):
    super().__init__(
      iqlink_tile_label(),
      "",
      gui_app.texture("icons/iq/bluetooth.png", 56, 56, keep_aspect_ratio=True),
    )
    self._params = Params()
    mici_register_button(self)

  def _get_label_font_size(self):
    # CJK at 64px clips inside the scissor + icon; Latin "iqlink" can stay larger.
    return 52 if any("\u4e00" <= c <= "\u9fff" for c in self.text) else 64

  def refresh_label(self):
    label = iqlink_tile_label()
    if self.text != label:
      self.set_text(label)
    self._label.set_font_size(self._get_label_font_size())
    value = self._value_text()
    if self.value != value:
      self.set_value(value)

  def _bridge_on(self) -> bool:
    try:
      return self._params.get_bool("IqlinkEnabled")
    except UnknownKeyName:
      return False

  def _link_state(self) -> int:
    try:
      return int(self._params.get("IqlinkBleLinkState") or 0)
    except (UnknownKeyName, TypeError, ValueError):
      try:
        return 2 if self._params.get_bool("IqlinkBleConnected") else 0
      except UnknownKeyName:
        return 0

  def _link_up(self) -> bool:
    return iqlink_hmac_up(self._params)

  def _status_color(self) -> rl.Color:
    return iqlink_status_color(self._params)

  def _value_key(self) -> str:
    if self._link_up():
      return "connected"
    if self._bridge_on() and self._link_state() == 1:
      return "connecting"
    if self._bridge_on():
      return "disconnected"
    return ""

  def _value_text(self) -> str:
    key = self._value_key()
    return mici_tr(key) if key else ""

  def _update_state(self):
    super()._update_state()
    self.refresh_label()

  def _render(self, _):
    super()._render(_)
    rl.draw_circle(int(self._rect.x + 30), int(self._rect.y + 30), 9, self._status_color())

  def _handle_mouse_release(self, mouse_pos: MousePos):
    super()._handle_mouse_release(mouse_pos)
    try:
      new_val = not self._bridge_on()
      self._params.put_bool("IqlinkEnabled", new_val)
      if new_val:
        try:
          self._params.put_bool("IqlinkBlePairFailed", False)
        except UnknownKeyName:
          pass
    except UnknownKeyName:
      pass
    self.set_value(self._value_text())
