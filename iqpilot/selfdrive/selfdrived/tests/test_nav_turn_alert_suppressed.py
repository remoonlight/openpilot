"""navTurn* must not produce HUD text (转弯限速 suppressed)."""
from cereal import custom
from openpilot.iqpilot.common.atlas_alerts import Tags as ET
from openpilot.iqpilot.selfdrive.selfdrived.events import EVENTS_IQ

EventNameIQ = custom.IQOnroadEvent.EventName


def test_nav_turn_events_have_no_warning_alert():
  assert ET.WARNING not in EVENTS_IQ.get(EventNameIQ.navTurnLeft, {})
  assert ET.WARNING not in EVENTS_IQ.get(EventNameIQ.navTurnRight, {})
