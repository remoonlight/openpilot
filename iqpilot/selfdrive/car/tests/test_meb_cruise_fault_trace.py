"""Ring-buffer dump around Cruise Faulted (no on-road scripts)."""
import json
import os

from openpilot.iqpilot.selfdrive.car.meb_cruise_fault_trace import MebCruiseFaultTrace


def test_trigger_writes_pre_and_post(tmp_path):
  path = tmp_path / "trace.jsonl"
  tr = MebCruiseFaultTrace(path=str(path), pre_n=5, post_n=3, cooldown_s=0.0)

  for i in range(8):
    tr.push({"i": i, "tsk": 3})
  tr.on_flags(cruise_fault_lateral=True, acc_faulted=True)
  # still recording post window
  assert not path.exists()
  for j in range(3):
    tr.push({"i": 100 + j, "tsk": 7})

  assert path.exists()
  row = json.loads(path.read_text(encoding="utf-8").strip())
  assert row["reason"] == "cruiseFaultLateral"
  assert [s["i"] for s in row["pre"]] == [3, 4, 5, 6, 7]
  assert [s["i"] for s in row["post"]] == [100, 101, 102]


def test_cooldown_skips_second_trigger(tmp_path):
  path = tmp_path / "trace.jsonl"
  tr = MebCruiseFaultTrace(path=str(path), pre_n=2, post_n=1, cooldown_s=60.0)
  tr.push({"i": 1})
  tr.push({"i": 2})
  tr.on_flags(True, False)
  tr.push({"i": 3})
  assert path.exists()
  # clear and try again immediately — cooldown blocks
  size = os.path.getsize(path)
  tr.on_flags(False, False)
  tr.on_flags(True, False)
  tr.push({"i": 4})
  assert os.path.getsize(path) == size


def test_acc_faulted_reason(tmp_path):
  path = tmp_path / "trace.jsonl"
  tr = MebCruiseFaultTrace(path=str(path), pre_n=1, post_n=1, cooldown_s=0.0)
  tr.push({"i": 0})
  tr.on_flags(False, True)
  tr.push({"i": 1})
  row = json.loads(path.read_text(encoding="utf-8").strip())
  assert row["reason"] == "accFaulted"
