from openpilot.selfdrive.ui.mici.mici_i18n import _ZH_CHS, mici_tr, text_needs_noto_sc, text_needs_unifont
from openpilot.system.ui.lib.multilang import multilang


def test_mici_settings_strings_include_chinese():
  assert _ZH_CHS["device"] == "设备"
  assert _ZH_CHS["konn3kt"] == "konn3kt"
  assert _ZH_CHS["AOL"] == "自动变道辅助"
  assert _ZH_CHS["Change Language"] == "更改语言"
  assert _ZH_CHS["force mici UI"] == "强制使用 Mici 界面"
  assert _ZH_CHS["current model"] == "当前模型"
  assert any("\u4e00" <= char <= "\u9fff" for char in _ZH_CHS.values())


def test_simplified_chinese_does_not_replace_latin_font():
  original_language = multilang._language
  try:
    multilang._language = "zh-CHS"
    assert text_needs_noto_sc("设置")
    assert not text_needs_unifont("设置")
    assert not text_needs_noto_sc("Version 1.0")
    assert not text_needs_unifont("Version 1.0")
    multilang._language = "en"
    # Han glyphs still use Noto so language-picker names are not blank.
    assert text_needs_noto_sc("中文（简体）")
  finally:
    multilang._language = original_language


def test_mici_tr_only_maps_known_menu_titles():
  original_language = multilang._language
  try:
    multilang._language = "zh-CHS"
    assert mici_tr("device") == "设备"
    assert mici_tr("steering assistance behavior") == "转向辅助行为"
    assert mici_tr("IQ.Dynamic Curves") == "IQ.Dynamic 弯道"
    assert mici_tr("Availability While Cruise Changes") == "巡航变化时保持可用"
    assert mici_tr("Auto Lane Change") == "自动变道"
    assert mici_tr("SLC Policy") == "限速策略"
    # Dialog / confirmation copy stays English when unmapped.
    assert mici_tr("slide to\nclear cache") == "slide to\nclear cache"
  finally:
    multilang._language = original_language
