#!/usr/bin/env python3
"""Deploy the tracked IQ-link overlay to an IQ.Pilot beta device.

The device root is intentionally fixed to /data/iqpilot.  The script refuses
other roots, creates a timestamped backup on the device, and only then extracts
the overlay.  It requires the host's ssh and scp commands.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEVICE_ROOT = "/data/iqpilot"
FILES = (
  ("iqpilot/iqlink", "iqpilot/iqlink"),
  ("iqpilot/iqlink/overlay_beta/system/manager/process_config.py", "iqpilot/system/manager/process_config.py"),
  ("iqpilot/iqlink/overlay_beta/common/params_keys.h", "iqpilot/common/params_keys.h"),
  ("iqpilot/iqlink/overlay_beta/cereal/custom.capnp", "iqpilot/cereal/custom.capnp"),
  ("iqpilot/iqlink/overlay_beta/selfdrive/controls/lib/iq_longitudinal_planner.py",
   "iqpilot/selfdrive/controls/lib/iq_longitudinal_planner.py"),
  ("selfdrive/ui/lib/iqlink_status.py", "iqpilot/selfdrive/ui/lib/iqlink_status.py"),
  ("selfdrive/ui/mici/layouts/settings/iqlink.py", "iqpilot/selfdrive/ui/mici/layouts/settings/iqlink.py"),
  ("selfdrive/assets/icons/iq/bluetooth.png", "iqpilot/selfdrive/assets/icons/iq/bluetooth.png"),
  ("selfdrive/assets/icons/iq/bluetooth.png", "iqpilot/selfdrive/assets/icons_mici/iq/bluetooth.png"),
)


def package(output: Path) -> list[str]:
  members: list[str] = []
  with tarfile.open(output, "w:gz", format=tarfile.GNU_FORMAT) as archive:
    for source_rel, device_rel in FILES:
      source = ROOT / source_rel
      if not source.exists():
        raise SystemExit(f"missing tracked overlay source: {source_rel}")
      paths = (source,) if source.is_file() else tuple(
        p for p in source.rglob("*")
        if p.is_file() and "overlay_beta" not in p.relative_to(source).parts and "__pycache__" not in p.parts
      )
      for path in paths:
        suffix = "" if source.is_file() else f"/{path.relative_to(source).as_posix()}"
        member = f"{device_rel}{suffix}"
        data = path.read_bytes().replace(b"\r\n", b"\n") if path.suffix in {".py", ".h", ".capnp"} else path.read_bytes()
        info = tarfile.TarInfo(member)
        info.size, info.mode = len(data), 0o644
        archive.addfile(info, io.BytesIO(data))
        members.append(member)
  return members


REMOTE_APPLY = r"""set -eu
root=/data/iqpilot
package=/tmp/iqlink-overlay.tgz
[ "$(git -C "$root" branch --show-current)" = beta ] || { echo "expected beta at $root" >&2; exit 1; }
[ -f "$root/iqpilot/system/manager/process_config.py" ] || { echo "not an IQ.Pilot release-candidate root: $root" >&2; exit 1; }
stage="$(mktemp -d)"
backup="/data/iqlink-overlay-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup"
tar -xzf "$package" -C "$stage"
(cd "$stage" && find . -type f -print) | while IFS= read -r file; do
  relative="${file#./}"
  echo "$relative" >> "$backup/files.txt"
  target="$root/$relative"
  if [ -e "$target" ]; then
    mkdir -p "$backup/$(dirname "$relative")"
    cp -p "$target" "$backup/$relative"
  else
    echo "$relative" >> "$backup/new-files.txt"
  fi
done
if ! tar -xzf "$package" -C "$root"; then
  while IFS= read -r relative; do
    if [ -e "$backup/$relative" ]; then
      cp -p "$backup/$relative" "$root/$relative"
    else
      rm -f "$root/$relative"
    fi
  done < "$backup/files.txt"
  echo "overlay extraction failed; restored $backup" >&2
  exit 1
fi
rm -rf "$stage" "$package"
echo "IQ-link overlay installed. Backup: $backup"
echo "Rollback: copy backup files back under $root, then remove paths in $backup/new-files.txt"
"""


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("host", nargs="?", default="", help="SSH target, for example iq@10.10.10.205")
  parser.add_argument("--dry-run", action="store_true", help="create and verify the package without connecting")
  args = parser.parse_args()
  with tempfile.TemporaryDirectory() as temp_dir:
    package_path = Path(temp_dir) / "iqlink-overlay.tgz"
    members = package(package_path)
    print(f"packed {len(members)} files for {DEVICE_ROOT}")
    if args.dry_run:
      return 0
    if not args.host:
      raise SystemExit("host is required unless --dry-run")
    subprocess.run(["scp", str(package_path), f"{args.host}:/tmp/iqlink-overlay.tgz"], check=True)
    subprocess.run(["ssh", args.host, "sh -s"], input=REMOTE_APPLY, text=True, check=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
