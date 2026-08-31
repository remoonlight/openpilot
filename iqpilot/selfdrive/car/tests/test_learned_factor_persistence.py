import json
from types import SimpleNamespace

from iqpilot.selfdrive.car.card import Car


class DummyParams:
  def __init__(self):
    self.values: dict[str, object] = {}

  def get(self, key: str):
    return self.values.get(key)

  def put_nonblocking(self, key: str, value) -> None:
    self.values[key] = value


class HondaLikeController:
  def __init__(self):
    self.gasfactor = 1.0
    self.windfactor = 1.0


def make_car(controller):
  car = object.__new__(Car)
  car.params = DummyParams()
  car.CI = SimpleNamespace(CC=controller)
  car.CP = SimpleNamespace(carFingerprint="HONDA_CRV_6G")
  return car


class TestLearnedFactorPersistence:
  def test_save_then_seed_round_trip(self):
    car = make_car(HondaLikeController())
    car.CI.CC.gasfactor = 1.37
    car.CI.CC.windfactor = 0.84
    car._save_learned_factors()

    fresh = make_car(HondaLikeController())
    fresh.params.values = car.params.values
    fresh._seed_learned_factors()
    assert fresh.CI.CC.gasfactor == 1.37
    assert fresh.CI.CC.windfactor == 0.84

  def test_factors_keyed_per_fingerprint(self):
    car = make_car(HondaLikeController())
    car.CI.CC.gasfactor = 2.0
    car._save_learned_factors()

    other = make_car(HondaLikeController())
    other.params.values = car.params.values
    other.CP = SimpleNamespace(carFingerprint="HONDA_CIVIC_BOSCH")
    other._seed_learned_factors()
    assert other.CI.CC.gasfactor == 1.0

    other.CI.CC.gasfactor = 0.5
    other._save_learned_factors()
    stored = json.loads(other.params.values["IQLongLearnedFactors"])
    assert stored["HONDA_CRV_6G"]["gasfactor"] == 2.0
    assert stored["HONDA_CIVIC_BOSCH"]["gasfactor"] == 0.5

  def test_seed_ignores_corrupt_or_nonfinite_values(self):
    car = make_car(HondaLikeController())
    car.params.values["IQLongLearnedFactors"] = "not json"
    car._seed_learned_factors()
    assert car.CI.CC.gasfactor == 1.0

    car.params.values["IQLongLearnedFactors"] = json.dumps({"HONDA_CRV_6G": {"gasfactor": float("nan"), "windfactor": "x"}})
    car._seed_learned_factors()
    assert car.CI.CC.gasfactor == 1.0
    assert car.CI.CC.windfactor == 1.0

  def test_noop_for_controllers_without_factors(self):
    car = make_car(SimpleNamespace())
    car._seed_learned_factors()
    car._save_learned_factors()
    assert "IQLongLearnedFactors" not in car.params.values

    car = make_car(None)
    car._seed_learned_factors()
    car._save_learned_factors()
    assert "IQLongLearnedFactors" not in car.params.values
