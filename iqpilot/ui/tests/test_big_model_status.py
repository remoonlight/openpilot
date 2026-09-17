"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos/

The BIG (tici/tizi) and SMALL (mici) onroad source indicators share one
resolver (comma PR #38492 states, backend-aware label). Pin its truth table.
"""
from iqpilot.ui.onroad.big_model_status import SourceState, resolve_source, source_text


class _FakeParams:
  def __init__(self, **flags):
    self._flags = flags

  def get_bool(self, key: str) -> bool:
    return bool(self._flags.get(key, False))

  def get(self, key: str):
    return self._flags.get(key)


def _resolve(engaged=False, **flags):
  return resolve_source(_FakeParams(**flags), engaged)


def test_no_backend_enabled_is_hidden():
  assert _resolve() == ("", SourceState.HIDDEN)


def test_emac_label_is_mac():
  label, _ = _resolve(IQEmacEnabled=True, MacModelReachable=True, MacModelActive=True)
  assert label == "MAC"


def test_egpu_label_is_gpu():
  label, _ = _resolve(IQEgpuEnabled=True, UsbGpuPresent=True, UsbGpuActive=True)
  assert label == "GPU"


def test_dock_wins_when_both_enabled():
  label, _ = _resolve(IQEmacEnabled=True, IQEgpuEnabled=True,
                      MacModelReachable=True, UsbGpuPresent=True)
  assert label == "GPU"


def test_emac_when_dock_absent():
  label, state = _resolve(IQEmacEnabled=True, IQEgpuEnabled=True, MacModelReachable=True)
  assert label == "MAC"
  assert state == SourceState.LOADING


def test_egpu_states_mirror_emac():
  assert _resolve(IQEgpuEnabled=True)[1] == SourceState.HIDDEN                        # not present
  assert _resolve(IQEgpuEnabled=True, UsbGpuPresent=True)[1] == SourceState.LOADING
  assert _resolve(IQEgpuEnabled=True, UsbGpuPresent=True, UsbGpuActive=True)[1] == SourceState.ACTIVE
  assert _resolve(IQEgpuEnabled=True, UsbGpuPresent=True, UsbGpuFailed=True)[1] == SourceState.FAILED
  assert _resolve(engaged=True, IQEgpuEnabled=True, UsbGpuPresent=True,
                  UsbGpuFailed=True)[1] == SourceState.CROSSED


def test_emac_states():
  assert _resolve(IQEmacEnabled=True)[1] == SourceState.HIDDEN                       # unreachable
  assert _resolve(IQEmacEnabled=True, MacModelReachable=True)[1] == SourceState.LOADING
  assert _resolve(IQEmacEnabled=True, MacModelReachable=True, MacModelActive=True)[1] == SourceState.ACTIVE
  assert _resolve(IQEmacEnabled=True, MacModelReachable=True, MacModelFailed=True)[1] == SourceState.FAILED
  # engaged on small because big failed -> crossed
  assert _resolve(engaged=True, IQEmacEnabled=True, MacModelReachable=True,
                  MacModelFailed=True)[1] == SourceState.CROSSED
  # active always wins over a stale failed flag
  assert _resolve(IQEmacEnabled=True, MacModelReachable=True,
                  MacModelActive=True, MacModelFailed=True)[1] == SourceState.ACTIVE


def test_failed_but_disconnected_is_hidden():
  # unplugged mid-drive: nothing to show, not a red/orange "failed"
  assert _resolve(IQEmacEnabled=True, MacModelReachable=False, MacModelFailed=True)[1] == SourceState.HIDDEN


def test_disabled_dock_falls_back_to_emac():
  label, _ = _resolve(IQEmacEnabled=True, IQEgpuDisabled=True, UsbGpuPresent=True, MacModelReachable=True)
  assert label == "MAC"


def test_gpu_loading_appends_percent():
  p = _FakeParams(UsbGpuSetupProgress="0.552")
  assert source_text("GPU", SourceState.LOADING, p) == "GPU 55%"
  assert source_text("GPU", SourceState.ACTIVE, p) == "GPU"
  assert source_text("MAC", SourceState.LOADING, p) == "MAC"
