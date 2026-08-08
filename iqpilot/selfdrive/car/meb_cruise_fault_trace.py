"""Auto ring-buffer around Cruise Faulted — no scripts needed on-road.

On rising edge of cruiseFaultLateralMode (user "Cruise Faulted") or accFaulted,
keeps ~2.5s pre + ~2s post at carState rate and appends one JSON object to
``/data/meb_cruise_fault_trace.jsonl``. Also emits a short cloudlog line.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque

TRACE_PATH = "/data/meb_cruise_fault_trace.jsonl"
PRE_N = 250   # ~2.5s @100Hz
POST_N = 200  # ~2s
COOLDOWN_S = 15.0


class MebCruiseFaultTrace:
  def __init__(self, path: str = TRACE_PATH, pre_n: int = PRE_N, post_n: int = POST_N,
               cooldown_s: float = COOLDOWN_S):
    self.path = path
    self.pre_n = pre_n
    self.post_n = post_n
    self.cooldown_s = cooldown_s
    self._buf: deque[dict] = deque(maxlen=pre_n)
    self._post_left = 0
    self._post: list[dict] = []
    self._pre: list[dict] = []
    self._reason = ""
    self._last_dump_t = 0.0
    self._prev_lateral = False
    self._prev_acc_faulted = False

  def push(self, sample: dict) -> None:
    self._buf.append(sample)
    if self._post_left <= 0:
      return
    self._post.append(sample)
    self._post_left -= 1
    if self._post_left == 0:
      self._flush()

  def on_flags(self, cruise_fault_lateral: bool, acc_faulted: bool) -> None:
    rising_lat = cruise_fault_lateral and not self._prev_lateral
    rising_acc = acc_faulted and not self._prev_acc_faulted
    self._prev_lateral = cruise_fault_lateral
    self._prev_acc_faulted = acc_faulted
    if not (rising_lat or rising_acc) or self._post_left > 0:
      return
    now = time.monotonic()
    if now - self._last_dump_t < self.cooldown_s:
      return
    self._reason = "cruiseFaultLateral" if rising_lat else "accFaulted"
    self._pre = list(self._buf)
    self._post = []
    self._post_left = self.post_n
    self._cloudlog_pre()

  def _payload(self) -> dict:
    return {
      "t_wall": time.time(),
      "t_mono": time.monotonic(),
      "reason": self._reason,
      "pre_n": len(self._pre),
      "post_n": len(self._post),
      "pre": self._pre,
      "post": self._post,
    }

  def _cloudlog_pre(self) -> None:
    try:
      from openpilot.common.swaglog import cloudlog
      tail = self._pre[-5:] if self._pre else []
      cloudlog.warning(
        f"meb_cruise_fault_trace trigger={self._reason} pre={len(self._pre)} "
        f"tail={json.dumps(tail, separators=(',', ':'))}"
      )
    except Exception:
      pass

  def _flush(self) -> None:
    payload = self._payload()
    self._last_dump_t = time.monotonic()
    try:
      parent = os.path.dirname(self.path)
      if parent:
        os.makedirs(parent, exist_ok=True)
      with open(self.path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")
    except Exception:
      pass
    try:
      from openpilot.common.swaglog import cloudlog
      cloudlog.warning(
        f"meb_cruise_fault_trace wrote {self.path} reason={self._reason} "
        f"pre={payload['pre_n']} post={payload['post_n']}"
      )
    except Exception:
      pass
    self._pre = []
    self._post = []
    self._reason = ""


meb_cruise_fault_trace = MebCruiseFaultTrace()
