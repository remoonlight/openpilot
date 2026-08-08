from openpilot.selfdrive.ui.mici.mici_i18n import script_font_runs


def test_script_font_runs_speed_limit():
  assert script_font_runs("限速100 km/h") == [
    ("限速", True),
    ("100 km/h", False),
  ]


def test_script_font_runs_latin_only():
  assert script_font_runs("speed camera") == [("speed camera", False)]


def test_script_font_runs_han_only():
  assert script_font_runs("测速摄像头") == [("测速摄像头", True)]
