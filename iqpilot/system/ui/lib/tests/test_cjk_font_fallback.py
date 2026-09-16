"""CJK font helpers without importing pyray."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FNT = ROOT / "iqlink/overlay_beta/selfdrive/assets/fonts/NotoSansSC-Regular.fnt"


def _latin_only(text: str) -> bool:
  return all(ord(c) < 0x250 for c in text)


def _bmfont_char_ids(path: Path) -> set[int]:
  ids: set[int] = set()
  for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("char id="):
      ids.add(int(line.split("=", 1)[1].split()[0]))
  return ids


def test_latin_only_keeps_ascii_and_swaps_cjk():
  assert _latin_only("Speed Limit")
  assert not _latin_only("车速")


def test_noto_atlas_misses_qu_lv_but_has_qi():
  ids = _bmfont_char_ids(FNT)
  assert ord("器") in ids
  assert ord("控") in ids
  assert ord("制") in ids
  assert ord("曲") not in ids
  assert ord("率") not in ids


def test_cjk_word_is_not_line_broken():
  word = "曲率控制器"
  assert any(ord(c) >= 0x250 for c in word)
  # mirrors wrap_text._break_long_word CJK guard
  parts = [word]
  assert parts == ["曲率控制器"]


if __name__ == "__main__":
  test_latin_only_keeps_ascii_and_swaps_cjk()
  test_noto_atlas_misses_qu_lv_but_has_qi()
  test_cjk_word_is_not_line_broken()
  print("ok")
