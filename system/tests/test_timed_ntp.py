"""ponytail: timed wall-clock helpers — NTP decode, HTTP Date, BLE phone ts order."""
from __future__ import annotations

import datetime
import struct
import time
from pathlib import Path

from openpilot.system import timed as timed_mod


def test_calendar_timestamp_and_ntp_packet_decode(tmp_path: Path, monkeypatch):
  t = datetime.datetime(2026, 7, 14, 1, 0, 0)
  assert timed_mod.calendar_timestamp(t) == 1783990800

  seconds = 1783990800 + timed_mod._NTP_DELTA
  packet = struct.pack("!12I", *([0] * 10 + [seconds, 0]))

  class _Sock:
    def __enter__(self):
      return self

    def __exit__(self, *args):
      return False

    def settimeout(self, _t):
      pass

    def sendto(self, _msg, _addr):
      pass

    def recvfrom(self, _n):
      return packet, ("1.2.3.4", 123)

  monkeypatch.setattr(timed_mod.socket, "socket", lambda *a, **k: _Sock())
  got = timed_mod.query_ntp("fake.ntp")
  assert got == t

  monkeypatch.setattr(timed_mod, "_TIME_FILE", str(tmp_path / "ntp_wall_time"))
  timed_mod._persist_time(t)
  assert (tmp_path / "ntp_wall_time").read_text(encoding="utf-8") == "1783990800"


def test_sync_order_global_cn_http_ble(tmp_path: Path, monkeypatch):
  assert timed_mod._parse_http_date("Mon, 27 Jul 2026 14:15:32 GMT") == datetime.datetime(2026, 7, 27, 14, 15, 32)

  calls: list[str] = []

  def fake_ntp(host, timeout=2.0):
    calls.append(f"ntp:{host}")
    return None

  def fake_http(url, timeout=5.0, *, _hops=0):
    calls.append(f"http:{url}")
    return None

  phone_t = datetime.datetime(2026, 7, 27, 14, 20, 0)

  def fake_phone():
    calls.append("ble")
    return phone_t

  set_calls: list[datetime.datetime] = []
  monkeypatch.setattr(timed_mod, "query_ntp", fake_ntp)
  monkeypatch.setattr(timed_mod, "query_http_date", fake_http)
  monkeypatch.setattr(timed_mod, "query_phone_ble_time", fake_phone)
  monkeypatch.setattr(timed_mod, "set_time", lambda t: set_calls.append(t) or True)

  assert timed_mod.sync_ntp() is True
  # global before CN
  g0 = calls.index(f"ntp:{timed_mod._NTP_GLOBAL[0]}")
  c0 = calls.index(f"ntp:{timed_mod._NTP_CN[0]}")
  h0 = next(i for i, c in enumerate(calls) if c.startswith("http:"))
  assert g0 < c0 < h0 < calls.index("ble")
  assert set_calls == [phone_t]


def test_query_phone_ble_time_fresh_shm(tmp_path: Path, monkeypatch):
  p = tmp_path / "phone_ts"
  ts_ms = int(datetime.datetime(2026, 7, 27, 14, 20, 0, tzinfo=datetime.UTC).timestamp() * 1000)
  p.write_text(str(ts_ms), encoding="utf-8")
  monkeypatch.setattr(timed_mod, "_PHONE_TS_FILE", str(p))
  got = timed_mod.query_phone_ble_time()
  assert got == datetime.datetime(2026, 7, 27, 14, 20, 0)

  # stale mtime
  older = time.time() - timed_mod._PHONE_TS_MAX_AGE_S - 10
  import os
  os.utime(p, (older, older))
  assert timed_mod.query_phone_ble_time() is None
