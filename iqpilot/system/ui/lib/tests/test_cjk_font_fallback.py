"""Mirrors iqpilot.system.ui.lib.application._latin_only (avoid importing pyray)."""


def _latin_only(text: str) -> bool:
  return all(ord(c) < 0x250 for c in text)


def test_latin_only_keeps_ascii_and_swaps_cjk():
  assert _latin_only("Speed Limit")
  assert _latin_only("ACC")
  assert not _latin_only("车速")
  assert not _latin_only("限速 80")


if __name__ == "__main__":
  test_latin_only_keeps_ascii_and_swaps_cjk()
  print("ok")
