#!/usr/bin/env python3
"""Tests for network time sync when the system clock is invalid."""
import datetime
import importlib.util
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def load_time_helpers():
  spec = importlib.util.spec_from_file_location("openpilot.common.time_helpers", ROOT / "common" / "time_helpers.py")
  module = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(module)
  return module


def load_network_time(time_helpers_module):
  sys.modules["openpilot"] = type(sys)("openpilot")
  sys.modules["openpilot.common"] = type(sys)("openpilot.common")
  sys.modules["openpilot.common.time_helpers"] = time_helpers_module
  spec = importlib.util.spec_from_file_location("openpilot.common.network_time", ROOT / "common" / "network_time.py")
  module = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(module)
  return module


time_helpers = load_time_helpers()
network_time = load_network_time(time_helpers)


class TestNetworkTimeSync(unittest.TestCase):
  def setUp(self):
    network_time._last_sync = 0.0

  def test_system_time_valid_on_dev_machine(self):
    self.assertTrue(time_helpers.system_time_valid())

  def test_fetch_network_time_parses_date_header(self):
    response = MagicMock()
    response.headers = {"Date": "Sat, 13 Jun 2026 06:00:00 GMT"}
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch.object(network_time.urllib.request, "urlopen", return_value=response):
      remote = network_time.fetch_network_time()

    self.assertEqual(remote, datetime.datetime(2026, 6, 13, 6, 0, 0))

  def test_fetch_network_time_tries_next_url(self):
    response = MagicMock()
    response.headers = {"Date": "Sat, 13 Jun 2026 06:00:00 GMT"}
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)

    with patch.object(network_time.urllib.request, "urlopen", side_effect=[OSError("fail"), response]):
      remote = network_time.fetch_network_time()

    self.assertEqual(remote, datetime.datetime(2026, 6, 13, 6, 0, 0))

  @patch.object(network_time, "set_system_time", return_value=True)
  @patch.object(network_time, "fetch_network_time", return_value=datetime.datetime(2026, 6, 13, 6, 0, 0))
  @patch.object(network_time, "system_time_valid", side_effect=[False, True])
  def test_sync_network_time_sets_clock_when_invalid(self, *_mocks):
    self.assertTrue(network_time.sync_network_time(min_interval=0.0))

  @patch.object(network_time, "fetch_network_time")
  def test_sync_network_time_skips_when_valid(self, mock_fetch):
    with patch.object(network_time, "system_time_valid", return_value=True):
      self.assertTrue(network_time.sync_network_time(min_interval=0.0))
    mock_fetch.assert_not_called()

  @patch.object(network_time, "fetch_network_time", return_value=datetime.datetime(2026, 6, 13, 6, 0, 0))
  @patch.object(network_time, "set_system_time", return_value=True)
  def test_sync_network_time_rate_limited(self, *_mocks):
    with patch.object(network_time, "system_time_valid", return_value=False):
      network_time._last_sync = time.monotonic()
      self.assertFalse(network_time.sync_network_time(min_interval=30.0))

  @patch.object(network_time.subprocess, "run")
  def test_set_system_time_skips_small_diff(self, mock_run):
    now = datetime.datetime.now()
    self.assertTrue(network_time.set_system_time(now))
    mock_run.assert_not_called()

  def test_timed_uses_network_sync(self):
    source = (ROOT / "system" / "timed.py").read_text(encoding="utf-8")
    self.assertIn("sync_network_time", source)
    self.assertNotIn("systemd-timesyncd", source)

  def test_mici_setup_syncs_on_ssl_error(self):
    source = (ROOT / "system" / "ui" / "mici_setup.py").read_text(encoding="utf-8")
    self.assertIn("ssl.SSLCertVerificationError", source)
    self.assertIn("sync_network_time", source)
    self.assertNotIn("systemd-timesyncd", source)

  def test_ssh_key_syncs_on_ssl_error(self):
    source = (ROOT / "selfdrive" / "ui" / "widgets" / "ssh_key.py").read_text(encoding="utf-8")
    self.assertIn("requests.exceptions.SSLError", source)
    self.assertIn("sync_network_time", source)
    self.assertNotIn("systemd-timesyncd", source)


if __name__ == "__main__":
  unittest.main()
