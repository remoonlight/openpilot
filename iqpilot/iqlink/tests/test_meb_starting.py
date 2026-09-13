"""MEB ACC_Anfahren / hold release. Isolated from cereal."""
from types import SimpleNamespace
from pathlib import Path

_MEBCAN = (
  Path(__file__).resolve().parents[1]
  / "overlay_beta/artifacts/package_sources/iqdbc/iqdbc/car/volkswagen/mebcan.py"
)


def _load_fns():
  src = _MEBCAN.read_text(encoding="utf-8")
  start = src.index("def compute_meb_long_starting")
  end = src.index("\ndef acc_hold_type")
  ns = {}
  exec(src[start:end], ns)
  return ns["compute_meb_long_starting"], ns["compute_meb_finish_stop"]


compute_meb_long_starting, compute_meb_finish_stop = _load_fns()

V_EGO_STARTING = 0.5
pid = SimpleNamespace(name="pid")
stopping = SimpleNamespace(name="stopping")


def _btn(name, pressed=True):
  return SimpleNamespace(type=SimpleNamespace(name=name), pressed=pressed)


def test_pid_hold_negative_accel_does_not_start():
  assert compute_meb_long_starting(pid, 0.1, V_EGO_STARTING, True, False, False, (), -0.27) is False


def test_pid_hold_positive_accel_starts():
  assert compute_meb_long_starting(pid, 0.1, V_EGO_STARTING, True, False, False, (), 0.3) is True


def test_pid_hold_zero_accel_does_not_start():
  assert compute_meb_long_starting(pid, 0.1, V_EGO_STARTING, True, False, False, (), 0.0) is False


def test_stopping_hold_no_start():
  assert compute_meb_long_starting(stopping, 0.1, V_EGO_STARTING, True, True, False, (), -0.56) is False


def test_resume_button_releases_hold():
  assert compute_meb_long_starting(
    stopping, 0.1, V_EGO_STARTING, True, True, True, (_btn("resumeCruise"),), -0.56,
  ) is True


def test_resume_button_releases_hold_at_zero_accel():
  assert compute_meb_long_starting(
    pid, 0.1, V_EGO_STARTING, True, False, True, (_btn("resumeCruise"),), 0.0,
  ) is True


def test_pid_above_v_ego_starting_no_start():
  assert compute_meb_long_starting(pid, 1.0, V_EGO_STARTING, True, False, False, (), 0.3) is False


def test_pid_creep_finishes_stop():
  assert compute_meb_finish_stop(False, False, 0.4, -0.1, False) is True


def test_pid_creep_does_not_hold_when_starting():
  assert compute_meb_finish_stop(True, False, 0.4, 0.3, False) is False


def test_rolling_does_not_force_hold():
  assert compute_meb_finish_stop(False, False, 3.0, -0.5, False) is False


def test_esp_hold_finishes_stop():
  assert compute_meb_finish_stop(False, False, 0.2, 0.0, True) is True
