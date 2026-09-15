"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos/
"""

from iqpilot.selfdrive.ui.mici.widgets.stock_button import BigButton, BigParamControl
from iqpilot.selfdrive.ui.mici.layouts.settings.iq_widgets import FollowDistanceSelector, MappedParamToggle, IQModeSelector, SafeParamControl
from iqpilot.selfdrive.ui.ui_state import ui_state
from iqpilot.system.ui.lib.application import gui_app
from iqpilot.system.ui.widgets.scroller import NavScroller
from iqpilot.system.ui.lib.multilang import tr

MS_TO_MPH = 2.23694
_SPEED_MPH = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
_SPEED_OPTIONS = [f"{s} mph" for s in _SPEED_MPH]
_SPEED_VALUES = [round(s / MS_TO_MPH, 2) for s in _SPEED_MPH]

_LEAD_SPEED_MPH = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85]
_LEAD_SPEED_OPTIONS = [f"{s} mph" for s in _LEAD_SPEED_MPH]
_LEAD_SPEED_VALUES = [round(s / MS_TO_MPH, 2) for s in _LEAD_SPEED_MPH]

_STOP_TIME_OPTIONS = ["1.0s", "1.5s", "2.0s", "2.5s", "3.0s", "3.5s", "4.0s", "4.5s", "5.0s", "5.5s", "6.0s"]
_STOP_TIME_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]


def _pin_map_speed_limit_off():
  # Map/SLC is off; IQ-link BLE + APK own the road limit.
  p = ui_state.params
  p.put("IQSpeedAssistMode", 0)
  p.put_bool("SpeedLimitController", False)
  p.put_bool("ShowSpeedLimits", False)


class DynamicSettingsPanel(NavScroller):
  def __init__(self):
    super().__init__()
    self._items = [
      BigParamControl(tr("IQ.Dynamic Curves"), "IQDynamicConditionalCurves"),
      BigParamControl(tr("IQ.Dynamic Slower Lead"), "IQDynamicConditionalSlowerLead"),
      BigParamControl(tr("IQ.Dynamic Stopped Lead"), "IQDynamicConditionalStoppedLead"),
      BigParamControl(tr("IQ.Dynamic Model Stops"), "IQDynamicConditionalModelStops"),
      BigParamControl(tr("IQ.Dynamic SLC Fallback"), "IQDynamicConditionalSLCFallback"),
      MappedParamToggle(tr("IQ.Dynamic Low Speed"), "IQDynamicConditionalSpeed", _SPEED_OPTIONS, _SPEED_VALUES),
      MappedParamToggle(tr("IQ.Dynamic Lead Speed"), "IQDynamicConditionalLeadSpeed", _LEAD_SPEED_OPTIONS, _LEAD_SPEED_VALUES),
      MappedParamToggle(tr("Model Stop Time"), "IQDynamicModelStopTime", _STOP_TIME_OPTIONS, _STOP_TIME_VALUES),
      BigParamControl(tr("IQ Force Stops"), "IQForceStops"),
    ]
    self._scroller.add_widgets(self._items)

  def show_event(self):
    super().show_event()
    for w in self._items:
      w.refresh()


class CruiseLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()
    _pin_map_speed_limit_off()

    self._dynamic_panel = DynamicSettingsPanel()

    self._follow_dist = FollowDistanceSelector()
    self._mode = IQModeSelector(self._follow_dist.refresh)
    self._dynamic_settings = BigButton(tr("iq.dynamic settings"))
    self._dynamic_settings.set_click_callback(lambda: gui_app.push_widget(self._dynamic_panel))
    self._dynamic_settings.set_visible(self._mode.is_dynamic)
    self._new_lead_mpc = SafeParamControl(tr("Experimental Lead MPC"), "newLeadMpc", default_on=True)

    self._main = [self._mode, self._dynamic_settings, self._follow_dist, self._new_lead_mpc]
    self._scroller.add_widgets(self._main)

  def _refresh(self):
    _pin_map_speed_limit_off()
    self._mode.refresh()
    self._follow_dist.refresh()
    self._new_lead_mpc.refresh()

  def show_event(self):
    super().show_event()
    self._refresh()
