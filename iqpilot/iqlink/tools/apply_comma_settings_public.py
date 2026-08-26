#!/usr/bin/env python3
"""Write selected keys from comma_settings_public.json into device Params.

Skips identity / git / updater keys. Run on the device:

  python3 apply_comma_settings_public.py /tmp/comma_settings_public.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKIP = {
  "DongleId", "HardwareSerial", "IMEI",
  "GitBranch", "GitCommit", "GitCommitDate", "GitRemote", "Version",
  "UpdaterAvailableBranches", "UpdaterInstallMode",
  "HasAcceptedTerms", "CompletedTrainingVersion",
}


def params_dir() -> Path:
  p = Path("/data/params/d")
  if p.is_dir():
    return p
  raise SystemExit("params dir not found: /data/params/d")


def encode(value) -> bytes:
  if isinstance(value, bool):
    return b"1" if value else b"0"
  if isinstance(value, (dict, list)):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
  if isinstance(value, (int, float)):
    return str(value).encode("utf-8")
  return str(value).encode("utf-8")


def main() -> int:
  src = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/comma_settings_public.json")
  data = json.loads(src.read_text(encoding="utf-8"))
  settings = data.get("settings") or data
  dest = params_dir()
  ok = skip = 0
  for key, value in settings.items():
    if key in SKIP:
      skip += 1
      continue
    (dest / key).write_bytes(encode(value))
    ok += 1
  print(f"wrote {ok} keys to {dest}, skipped {skip}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
