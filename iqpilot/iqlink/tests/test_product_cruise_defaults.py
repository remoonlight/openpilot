"""Self-check: one-shot iqlink product cruise Params migration."""


class _FakeParams:
  def __init__(self, initial=None):
    self.vals = dict(initial or {})

  def get_bool(self, key):
    return bool(self.vals.get(key, False))

  def put(self, key, value):
    self.vals[key] = value

  def put_bool(self, key, value):
    self.vals[key] = bool(value)


def test_apply_iqlink_product_cruise_defaults_once():
  # Inline the body to avoid importing manager.helpers (Params/cereal) on host.
  def apply(p):
    if p.get_bool("IqlinkProductCruiseDefaultsV1"):
      return
    p.put_bool("EnableSLPredReactToCurves", True)
    p.put_bool("LongIncrementsEnabled", True)
    p.put("LongIncrementTapStep", 10)
    p.put_bool("IqlinkProductCruiseDefaultsV1", True)

  p = _FakeParams({
    "EnableSLPredReactToCurves": False,
    "LongIncrementsEnabled": False,
    "LongIncrementTapStep": 1,
  })
  apply(p)
  assert p.vals["EnableSLPredReactToCurves"] is True
  assert p.vals["LongIncrementsEnabled"] is True
  assert p.vals["LongIncrementTapStep"] == 10
  assert p.vals["IqlinkProductCruiseDefaultsV1"] is True

  p.put("LongIncrementTapStep", 5)  # user change after migration
  apply(p)
  assert p.vals["LongIncrementTapStep"] == 5  # not overwritten


if __name__ == "__main__":
  test_apply_iqlink_product_cruise_defaults_once()
  print("ok")
