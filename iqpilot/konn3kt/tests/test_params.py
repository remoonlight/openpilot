from openpilot.common.params import Params, ParamKeyType
from openpilot.iqpilot.konn3kt.common.params import (
  _encode_param_bytes,
  apply_longitudinal_control_mode,
  get_longitudinal_control_mode_index,
  param_from_base64,
  param_to_bytes,
)


def test_encode_bool_param_uses_disk_format():
  assert _encode_param_bytes(True, ParamKeyType.BOOL) == b"1"
  assert _encode_param_bytes(False, ParamKeyType.BOOL) == b"0"


def test_param_to_bytes_bool_matches_get_bool():
  params = Params()
  params.put_bool("SshEnabled", True)
  assert param_to_bytes("SshEnabled", params) == b"1"
  params.put_bool("SshEnabled", False)
  assert param_to_bytes("SshEnabled", params) == b"0"


def test_longitudinal_control_mode_wire_encoding():
  params = Params()
  params.put_bool("AlphaLongitudinalEnabled", False)
  assert param_to_bytes("LongitudinalControlMode", params) == b"0"

  apply_longitudinal_control_mode(3, params)
  assert get_longitudinal_control_mode_index(params) == 3
  assert param_to_bytes("LongitudinalControlMode", params) == b"3"

  apply_longitudinal_control_mode(2, params)
  assert param_to_bytes("LongitudinalControlMode", params) == b"2"


def test_param_from_base64_longitudinal_control_mode():
  params = Params()
  params.put_bool("AlphaLongitudinalEnabled", False)
  param_from_base64("LongitudinalControlMode", "Mw==")  # base64("3")
  assert get_longitudinal_control_mode_index(params) == 3
  assert params.get_bool("AlphaLongitudinalEnabled")
  assert params.get_bool("ExperimentalMode")
  assert not params.get_bool("IQDynamicMode")
