#!/usr/bin/env python3
import datetime
import email.utils
import http.client
import os
import socket
import struct
import subprocess
import time
from typing import NoReturn
from urllib.parse import urlparse

import cereal.messaging as messaging
from openpilot.common.time_helpers import min_date, system_time_valid
from openpilot.common.swaglog import cloudlog
from openpilot.common.params import Params
from openpilot.common.gps import get_gps_location_service

# Survives reboot; / is ro and RTC on mici is often stuck at epoch.
_TIME_FILE = "/data/ntp_wall_time"
_PHONE_TS_FILE = "/dev/shm/iqlink_phone_ts_ms"  # written by iqlink after HMAC-ok envelope
_NTP_DELTA = 2208988800  # 1970-01-01 as NTP seconds
# Order: global NTP → CN NTP → carrier HTTP Date → BLE phone ts (iqlink).
_NTP_GLOBAL = (
  "ntp.ubuntu.com",
  "time.cloudflare.com",
  "time.apple.com",
)
_NTP_CN = (
  "ntp.aliyun.com",
  "ntp.tencent.com",
  "ntp.ntsc.ac.cn",
)
# WWAN often blocks UDP/123; CT portal Date still works. No HTTPS redirects (LTE TLS flaky).
_HTTP_TIME_URLS = (
  "http://a.189.cn/",
  "http://www.baidu.com/",
  "http://captive.apple.com/hotspot-detect.html",
)
_PLAUSIBLE_TS_MS_MIN = 1_704_067_200_000  # 2024-01-01 UTC
_PLAUSIBLE_TS_MS_MAX = 1_893_456_000_000  # 2030-01-01 UTC
_PHONE_TS_MAX_AGE_S = 180.0  # ignore stale shm if phone stopped publishing
_NTP_TIMEOUT_S = 2.0
_HTTP_TIMEOUT_S = 5.0
_NTP_RETRY_INVALID_S = 5.0
_NTP_RETRY_VALID_S = 30 * 60.0


def calendar_timestamp(naive_utc: datetime.datetime) -> int:
  # ponytail: naive wall times in timed are treated as UTC (matches `TZ=UTC date -s`).
  return int((naive_utc - datetime.datetime(1970, 1, 1)).total_seconds())


def _persist_time(new_time: datetime.datetime) -> None:
  try:
    tmp = _TIME_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
      f.write(str(calendar_timestamp(new_time)))
      f.flush()
      os.fsync(f.fileno())
    os.replace(tmp, _TIME_FILE)
  except OSError:
    pass


def set_time(new_time: datetime.datetime) -> bool:
  diff = datetime.datetime.now() - new_time
  if abs(diff) < datetime.timedelta(seconds=10):
    cloudlog.debug(f"Time diff too small: {diff}")
    _persist_time(new_time)
    return False

  cloudlog.warning(f"timed: setting time to {new_time} (was off by {diff})")
  try:
    subprocess.run(f"TZ=UTC date -s '{new_time}'", shell=True, check=True)
  except subprocess.CalledProcessError:
    cloudlog.exception("timed.failed_setting_time")
    return False
  _persist_time(new_time)
  return True


def restore_persisted_time() -> bool:
  if system_time_valid():
    return False
  try:
    with open(_TIME_FILE, encoding="utf-8") as f:
      ts = int(f.read().strip())
  except (OSError, ValueError):
    return False
  restored = datetime.datetime.fromtimestamp(ts, datetime.UTC).replace(tzinfo=None)
  if restored < min_date():
    return False
  cloudlog.warning(f"timed: restoring persisted wall time {restored}")
  return set_time(restored)


def query_ntp(host: str, timeout: float = _NTP_TIMEOUT_S) -> datetime.datetime | None:
  msg = b"\x1b" + 47 * b"\0"
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
      sock.settimeout(timeout)
      sock.sendto(msg, (host, 123))
      data, _ = sock.recvfrom(512)
  except OSError as e:
    cloudlog.debug(f"timed: NTP {host} failed: {e}")
    return None
  if len(data) < 48:
    return None
  seconds = struct.unpack("!12I", data[:48])[10] - _NTP_DELTA
  if seconds <= 0:
    return None
  return datetime.datetime.fromtimestamp(seconds, datetime.UTC).replace(tzinfo=None)


def _parse_http_date(value: str | None) -> datetime.datetime | None:
  if not value:
    return None
  try:
    dt = email.utils.parsedate_to_datetime(value)
  except (TypeError, ValueError, IndexError):
    return None
  if dt.tzinfo is not None:
    dt = dt.astimezone(datetime.UTC).replace(tzinfo=None)
  return dt


def query_http_date(url: str, timeout: float = _HTTP_TIMEOUT_S, *, _hops: int = 0) -> datetime.datetime | None:
  """Read Date from HTTP; at most two hops, HTTP only (WWAN TLS often broken)."""
  u = urlparse(url)
  if u.scheme != "http" or not u.hostname:
    return None
  path = u.path or "/"
  if u.query:
    path = f"{path}?{u.query}"
  conn: http.client.HTTPConnection | None = None
  try:
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    conn.request("GET", path, headers={"User-Agent": "openpilot-timed/1.0", "Connection": "close"})
    resp = conn.getresponse()
    dt = _parse_http_date(resp.getheader("Date"))
    loc = resp.getheader("Location") if 300 <= resp.status < 400 else None
    resp.read()
    if dt is not None:
      return dt
    if loc and loc.startswith("http://") and _hops < 2:
      return query_http_date(loc, timeout=timeout, _hops=_hops + 1)
    return None
  except OSError as e:
    cloudlog.debug(f"timed: HTTP Date {url} failed: {e}")
    return None
  finally:
    if conn is not None:
      conn.close()


def query_phone_ble_time() -> datetime.datetime | None:
  """IQ-link envelope ts (ms) published to shm after HMAC verify."""
  try:
    age = time.time() - os.path.getmtime(_PHONE_TS_FILE)
    if age > _PHONE_TS_MAX_AGE_S:
      return None
    with open(_PHONE_TS_FILE, encoding="utf-8") as f:
      ts_ms = int(f.read().strip())
  except (OSError, ValueError):
    return None
  if not (_PLAUSIBLE_TS_MS_MIN <= ts_ms <= _PLAUSIBLE_TS_MS_MAX):
    return None
  dt = datetime.datetime.fromtimestamp(ts_ms / 1000.0, datetime.UTC).replace(tzinfo=None)
  if dt < min_date():
    return None
  return dt


def _try_ntp_hosts(hosts: tuple[str, ...], label: str) -> bool:
  for host in hosts:
    ntp_time = query_ntp(host)
    if ntp_time is None or ntp_time < min_date():
      continue
    cloudlog.warning(f"timed: {label} NTP from {host} -> {ntp_time}")
    set_time(ntp_time)
    return True
  return False


def sync_ntp() -> bool:
  """Wall-clock sync: global NTP → CN NTP → carrier HTTP → BLE phone ts."""
  if _try_ntp_hosts(_NTP_GLOBAL, "global"):
    return True
  if _try_ntp_hosts(_NTP_CN, "CN"):
    return True

  for url in _HTTP_TIME_URLS:
    http_time = query_http_date(url)
    if http_time is None or http_time < min_date():
      continue
    cloudlog.warning(f"timed: HTTP Date from {url} -> {http_time}")
    set_time(http_time)
    return True

  phone_time = query_phone_ble_time()
  if phone_time is not None:
    cloudlog.warning(f"timed: BLE phone ts -> {phone_time}")
    set_time(phone_time)
    return True
  return False


def main() -> NoReturn:
  """
    timed responsibilities:
    - restore last-known wall time after reboot (RTC often broken on mici)
    - wall sync: global NTP → CN NTP → carrier HTTP Date → BLE phone ts
    - GPS time when a fix is available
    - publish clocks for the rest of the stack
  """

  params = Params()
  gps_location_service = get_gps_location_service(params)

  restore_persisted_time()
  sync_ntp()
  last_ntp_mono = time.monotonic()

  pm = messaging.PubMaster(['clocks'])
  sm = messaging.SubMaster([gps_location_service])
  while True:
    sm.update(1000)

    msg = messaging.new_message('clocks')
    msg.valid = system_time_valid()
    msg.clocks.wallTimeNanos = time.time_ns()
    pm.send('clocks', msg)

    interval = _NTP_RETRY_INVALID_S if not system_time_valid() else _NTP_RETRY_VALID_S
    if time.monotonic() - last_ntp_mono >= interval:
      sync_ntp()
      last_ntp_mono = time.monotonic()

    gps = sm[gps_location_service]
    gps_time = datetime.datetime.fromtimestamp(gps.unixTimestampMillis / 1000.)
    if not sm.updated[gps_location_service] or (time.monotonic() - sm.logMonoTime[gps_location_service] / 1e9) > 2.0:
      continue
    if not gps.hasFix:
      continue
    if gps_time < min_date():
      continue

    set_time(gps_time)
    time.sleep(10)

if __name__ == "__main__":
  main()
