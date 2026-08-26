"""Overlay manager: first-JIT watchdog window and bundle heal predicates."""
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1] / "overlay_beta"


def _load_watchdog():
  src = (ROOT / "system/manager/manager.py").read_text(encoding="utf-8")
  start = src.index("MODELD_WATCHDOG_TIMEOUT")
  end = src.index("\ndef manager_init")
  ns = {"cloudlog": SimpleNamespace(error=lambda *a, **k: None)}
  exec(src[start:end], ns)
  return ns


def _load_heal_pred():
  src = (ROOT / "system/manager/helpers.py").read_text(encoding="utf-8")
  start = src.index("def _model_download_in_progress")
  end = src.index("\ndef heal_active_model_bundle")
  ns = {"Params": object}
  exec(src[start:end], ns)
  return ns["_model_download_in_progress"]


class _Proc:
  def __init__(self):
    self.restarts = 0
    self.proc = SimpleNamespace(is_alive=lambda: True)

  def restart(self):
    self.restarts += 1


def test_first_publish_timeout_is_45s():
  ns = _load_watchdog()
  assert ns["MODELD_FIRST_PUBLISH_TIMEOUT"] == 45.0
  proc = _Proc()
  deadline = ns["update_modeld_watchdog"](
    None, True, False, proc, 10.0, timeout=ns["MODELD_FIRST_PUBLISH_TIMEOUT"]
  )
  assert deadline == 10.0 + 45.0
  assert proc.restarts == 0
  assert ns["update_modeld_watchdog"](deadline, True, False, proc, 10.0 + 44.0,
                                      timeout=ns["MODELD_FIRST_PUBLISH_TIMEOUT"]) == deadline
  ns["update_modeld_watchdog"](deadline, True, False, proc, 10.0 + 45.0,
                              timeout=ns["MODELD_FIRST_PUBLISH_TIMEOUT"])
  assert proc.restarts == 1


def test_default_timeout_stays_30s_for_stock_call():
  ns = _load_watchdog()
  proc = _Proc()
  deadline = ns["update_modeld_watchdog"](None, True, False, proc, 10.0)
  assert deadline == 10.0 + ns["MODELD_WATCHDOG_TIMEOUT"]


def test_download_index_minus_one_is_idle():
  fn = _load_heal_pred()
  assert fn(SimpleNamespace(get=lambda k: "-1")) is False
  assert fn(SimpleNamespace(get=lambda k: -1)) is False
  assert fn(SimpleNamespace(get=lambda k: None)) is False
  assert fn(SimpleNamespace(get=lambda k: "81")) is True
