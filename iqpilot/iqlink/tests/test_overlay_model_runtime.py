"""Overlay archive must ship iqmodeld SOF pairing and native process groups."""
from collections import Counter
import importlib.util
import tarfile
import tempfile
from pathlib import Path

_DEPLOY = Path(__file__).resolve().parents[1] / "tools" / "deploy_iqlink_overlay.py"
MODEL_RUNTIME = (
  "iqpilot/selfdrive/iqmodeld/daemon.py",
  "iqpilot/selfdrive/iqmodeld/sof_pair.py",
  "iqpilot/system/manager/process.py",
)
PROCESS_CONFIG = "iqpilot/system/manager/process_config.py"
BIG_MODEL_BACKENDS = (
  "modeld_selector",
  "maciqmodeld",
  "iqegpumodeld",
  "egpu_prefetch",
)
OVERLAY_PROCESS_CONFIG = (
  Path(__file__).resolve().parents[1] / "overlay_beta" / "system" / "manager" / "process_config.py"
)


def _load_deploy():
  spec = importlib.util.spec_from_file_location("deploy_iqlink_overlay", _DEPLOY)
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


def _normalize(path: Path) -> bytes:
  data = path.read_bytes()
  if path.suffix in {".py", ".h", ".capnp"}:
    return data.replace(b"\r\n", b"\n")
  return data


def test_overlay_archive_ships_model_runtime_once():
  deploy = _load_deploy()
  with tempfile.TemporaryDirectory() as tmp:
    archive_path = Path(tmp) / "iqlink-overlay.tgz"
    members = deploy.package(archive_path)
    counts = Counter(members)
    with tarfile.open(archive_path, "r:gz") as archive:
      names = archive.getnames()
      payloads = {}
      for rel in MODEL_RUNTIME:
        assert counts[rel] == 1, rel
        assert names.count(rel) == 1, rel
        info = archive.getmember(rel)
        payload = archive.extractfile(info).read()
        payloads[rel] = payload
        assert payload == _normalize(deploy.ROOT / rel)
        mode = info.mode & 0o777
        if rel == "iqpilot/selfdrive/iqmodeld/daemon.py":
          assert mode == 0o755, rel
        else:
          assert mode == 0o644, rel
  assert b"sof_pair_action" in payloads["iqpilot/selfdrive/iqmodeld/daemon.py"]
  assert b"from iqpilot.selfdrive.iqmodeld.sof_pair import" in payloads["iqpilot/selfdrive/iqmodeld/daemon.py"]
  assert b"def sof_pair_action" in payloads["iqpilot/selfdrive/iqmodeld/sof_pair.py"]
  assert b"os.killpg" in payloads["iqpilot/system/manager/process.py"]
  assert b"process group" in payloads["iqpilot/system/manager/process.py"]


def test_overlay_process_config_keeps_big_model_backends_and_iqlinkd():
  src = OVERLAY_PROCESS_CONFIG.read_text(encoding="utf-8")
  for name in BIG_MODEL_BACKENDS:
    assert f'"{name}"' in src, name
  assert "def big_model_enabled" in src
  assert 'PythonProcess("iqlinkd"' in src


def test_overlay_archive_ships_process_config_backends_once():
  deploy = _load_deploy()
  with tempfile.TemporaryDirectory() as tmp:
    archive_path = Path(tmp) / "iqlink-overlay.tgz"
    members = deploy.package(archive_path)
    assert Counter(members)[PROCESS_CONFIG] == 1
    with tarfile.open(archive_path, "r:gz") as archive:
      info = archive.getmember(PROCESS_CONFIG)
      payload = archive.extractfile(info).read()
  assert payload == _normalize(OVERLAY_PROCESS_CONFIG)
  for name in BIG_MODEL_BACKENDS:
    assert f'"{name}"'.encode() in payload, name
  assert b"def big_model_enabled" in payload
  assert b'PythonProcess("iqlinkd"' in payload
