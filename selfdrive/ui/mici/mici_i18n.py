"""Mici-only translations and text-based font selection."""

from __future__ import annotations

import weakref


_MICI_BUTTONS: list[weakref.ReferenceType] = []

_ZH_CHS = {
  # Settings home
  "toggles": "开关",
  "steering": "转向",
  "cruise": "巡航",
  "visuals": "视觉",
  "navigation": "导航",
  "models": "模型",
  "display": "显示",
  "trips": "行程",
  "vehicle": "车辆",
  "dashcam": "行车记录",
  "network": "网络",
  "device": "设备",
  "software": "软件",
  "developer": "开发者",
  "konn3kt": "konn3kt",
  # Device
  "device ID": "设备 ID",
  "serial": "序列号",
  "reset calibration": "重置校准",
  "reset": "重置",
  "reboot": "重启",
  "power off": "关机",
  "regulatory info": "监管信息",
  "driver\ncamera preview": "驾驶员摄像头\n预览",
  "review\ntraining guide": "查看使用指南",
  "terms &\nconditions": "使用条款",
  "pair in app": "在APP中配对",
  "online": "在线",
  "offline": "离线",
  "Change Language": "更改语言",
  "Select a language": "选择语言",
  # Network
  "tethering": "网络共享",
  "disabled": "已禁用",
  "enabled": "已启用",
  "tethering password": "网络共享密码",
  "enter password...": "输入密码...",
  "IP Address": "IP 地址",
  "Not connected": "未连接",
  "network usage": "网络用量",
  "default": "默认",
  "metered": "按流量计费",
  "unmetered": "不限流量",
  "wi-fi": "wi-fi",
  "eSIM": "eSIM",
  "manage profiles": "管理配置文件",
  "enable roaming": "启用漫游",
  "apn settings": "APN 设置",
  "cellular metered": "使用蜂窝数据\n上传视频",
  "enter APN": "输入 APN",
  "profiles": "配置文件",
  "status": "状态",
  "refresh profiles": "刷新配置文件",
  "add profile": "添加配置文件",
  "scan qr / enter code": "扫描二维码 / 输入代码",
  "provider unknown": "未知运营商",
  "active": "已启用",
  # Software
  "version": "版本",
  "branch": "分支",
  "check for update": "检查更新",
  "download update": "下载更新",
  "install update": "安装更新",
  "update\ninstall mode": "更新安装模式",
  "up to date": "已是最新版本",
  "failed to update": "更新失败",
  "updater failed\nto respond": "更新服务\n未响应",
  "target branch": "目标分支",
  "disable\nupdates": "禁用更新",
  "enable\nupdates": "启用更新",
  "currently on": "当前已开启",
  "currently off": "当前已关闭",
  "uninstall IQ.Pilot": "卸载 IQ.Pilot",
  "uninstall": "卸载",
  # Trips
  "ALL TIME": "全部时间",
  "PAST WEEK": "过去一周",
  "drives": "行程",
  "hours": "小时",
  # Common setting labels
  "disengage on accelerator": "踩油门时解除",
  "lane departure warnings": "车道偏离警告",
  "use metric units": "使用公制单位",
  "Blind Spot Warnings": "盲点警告",
  "Steering Arc": "转向弧线",
  "Road Name": "道路名称",
  "Turn Signals": "转向灯",
  "Acceleration Bar": "加速度条",
  "enable dashcam": "启用行车记录仪",
  "record driver camera": "录制驾驶员摄像头",
  "record microphone audio": "录制麦克风音频",
  "display brightness": "显示亮度",
  "force mici UI": "强制使用 Mici 界面",
  "onroad brightness": "行驶中亮度",
  "brightness delay": "亮度延迟",
  "interactivity": "交互超时",
  "auto": "自动",
  "auto dark": "自动暗屏",
  "off": "关闭",
  "on": "开启",
  "N/A": "不可用",
  # Second-level steering and cruise menus
  "AOL": "自动变道辅助",
  "steering assistance behavior": "转向辅助行为",
  "lane change": "变道",
  "Neural Net FF": "前馈神经网络",
  "iq.dynamic settings": "IQ.Dynamic 设置",
  "speed limit settings": "限速设置",
  "IQ Mode": "IQ 模式",
  "Follow Distance": "跟车距离",
  "Speed Limit": "限速",
  "Experimental Lead MPC": "实验性前车 MPC",
  "Stock ACC": "原厂 ACC",
  "aggressive": "激进",
  "standard": "标准",
  "relaxed": "宽松",
  "stock": "原厂",
  "info": "提示",
  "warning": "警告",
  "control": "控制",
  # Second-level vehicle menus
  "enforce factory long.": "强制原厂纵向控制",
  "hyundai long. tuning": "现代纵向控制调校",
  "dynamic": "动态",
  "predictive": "预测",
  "stop and go (beta)": "启停跟车 (beta)",
  "stop and go manual brake": "启停跟车手动刹车",
  "PQ HCA status 7 mode": "PQ HCA 状态 7 模式",
  "lateral when cruise faulted": "巡航故障时保持横向控制",
  "MQB ACC resume": "MQB ACC 恢复",
  "MQB steering lockout": "MQB 转向锁定",
  "virtual torque blending": "虚拟扭矩融合",
  # Second-level model menus
  "current model": "当前模型",
  "cancel download": "取消下载",
  "redownload model": "重新下载模型",
  "refresh model list": "刷新模型列表",
  "driving model": "驾驶模型",
  "vision model": "视觉模型",
  "policy model": "策略模型",
  "clear model cache": "清除模型缓存",
  "live learning steer delay": "实时学习\n转向延迟",
  "software delay": "软件延迟",
  "use lane turn desires": "使用车道\n转弯意图",
  "lane turn speed": "车道转弯速度",
  "slow": "慢",
  "normal": "正常",
  "fast": "快",
  # Second-level developer menus
  "SSH keys": "SSH 密钥",
  "Not set": "未设置",
  "longitudinal maneuver mode": "纵向机动模式",
  "lateral maneuver mode": "横向机动模式",
  # Third-level steering panels
  "Driver Intervention Handling": "驾驶员干预处理",
  "Availability While Cruise Changes": "巡航变化时保持可用",
  "Brake Response Mode": "刹车响应模式",
  "remain active": "保持激活",
  "standby": "待命",
  "disengage": "解除",
  "Auto Lane Change": "自动变道",
  "Delay with Blind Spot": "盲点检测时延迟",
  "Continuous Changes": "连续变道",
  "nudge": "轻推",
  "nudgeless": "无需轻推",
  # Third-level cruise panels
  "IQ.Dynamic Curves": "IQ.Dynamic 弯道",
  "IQ.Dynamic Slower Lead": "IQ.Dynamic 前车减速",
  "IQ.Dynamic Stopped Lead": "IQ.Dynamic 前车静止",
  "IQ.Dynamic Model Stops": "IQ.Dynamic 模型停车",
  "IQ.Dynamic SLC Fallback": "IQ.Dynamic 限速回退",
  "IQ.Dynamic Low Speed": "IQ.Dynamic 低速",
  "IQ.Dynamic Lead Speed": "IQ.Dynamic 前车速度",
  "Model Stop Time": "模型停车时间",
  "IQ Force Stops": "IQ 强制停车",
  "SLC Policy": "限速策略",
  "SLC Override": "限速覆盖",
  "SLC Confirm Higher": "确认更高限速",
  "SLC Confirm Lower": "确认更低限速",
  "SLC Auto Confirm": "自动确认限速",
  "SLC Fallback IQ.Pilot": "限速回退 IQ.Pilot",
  "SLC Online Filler": "在线限速补全",
  "Lookahead Higher": "前瞻更高限速",
  "Lookahead Lower": "前瞻更低限速",
  "map only": "仅地图",
  "map priority": "地图优先",
  "combined": "合并",
  "manual": "手动",
  "set speed": "设定速度",
  # iqlink BLE (primary one-tap; no secondary panel)
  "cancel navigation": "取消导航",
  "iqlink": "蓝牙",
  "bluetooth switch": "蓝牙",
  "ble bridge": "蓝牙",
  "ble psk": "配对码",
  "connected": "已连接",
  "connecting": "连接中",
  "discovering": "寻找中",
  "disconnected": "未连接",
  "pair failed": "匹配失败",
  "idle": "空闲",
}


def _has_han(text: str) -> bool:
  return any("\u3400" <= c <= "\u4dbf" or "\u4e00" <= c <= "\u9fff" for c in text)


def _is_han_char(c: str) -> bool:
  return "\u3400" <= c <= "\u4dbf" or "\u4e00" <= c <= "\u9fff"


def script_font_runs(text: str) -> list[tuple[str, bool]]:
  """Split into (run, use_noto_sc) so Latin keeps Inter while Han uses Noto."""
  if not text:
    return []
  runs: list[tuple[str, bool]] = []
  buf = text[0]
  han = _is_han_char(text[0])
  for c in text[1:]:
    h = _is_han_char(c)
    if h == han:
      buf += c
    else:
      runs.append((buf, han))
      buf = c
      han = h
  runs.append((buf, han))
  return runs


def text_needs_noto_sc(text: str) -> bool:
  """Use Noto Sans SC for Han text except Traditional Chinese UI (unifont)."""
  if not _has_han(text):
    return False
  from openpilot.system.ui.lib.multilang import multilang
  # Prefer Noto whenever we are rendering Han and are not on zh-CHT.
  # This also covers zh-CHS menu strings if language init briefly lags.
  return multilang.language != "zh-CHT"


def text_needs_unifont(text: str) -> bool:
  """Use unifont for scripts not covered by the current Latin or Noto font."""
  if text_needs_noto_sc(text):
    return False
  return any(
    "\u3400" <= c <= "\u4dbf" or "\u4e00" <= c <= "\u9fff" or "\u3040" <= c <= "\u30ff"
    or "\u0600" <= c <= "\u06ff" or "\u0e00" <= c <= "\u0e7f" or "\uac00" <= c <= "\ud7af"
    for c in text
  )


def sync_mici_language() -> str:
  """Re-read LanguageSetting so mici UI matches the device param."""
  from openpilot.system.ui.lib.multilang import multilang
  if multilang._params is None:
    return multilang.language
  raw = multilang._params.get("LanguageSetting")
  lang = str(raw or "en").removeprefix("main_")
  if lang in multilang.codes and lang != multilang.language:
    multilang.change_language(lang)
  return multilang.language


def mici_tr(msgid: str) -> str:
  """Prefer mici zh-CHS labels, then gettext."""
  from openpilot.system.ui.lib.multilang import multilang, tr
  sync_mici_language()
  if multilang.language == "zh-CHS" and msgid in _ZH_CHS:
    return _ZH_CHS[msgid]
  return tr(msgid)


def mici_profiles_count(count: int) -> str:
  from openpilot.system.ui.lib.multilang import multilang
  return f"{count} 个配置文件" if multilang.language == "zh-CHS" else f"{count} profiles"


def mici_register_button(button) -> None:
  _MICI_BUTTONS.append(weakref.ref(button))


def mici_refresh_all_labels() -> None:
  active_refs = []
  for ref in _MICI_BUTTONS:
    button = ref()
    if button is None:
      continue
    active_refs.append(ref)
    if hasattr(button, "refresh_label"):
      button.refresh_label()
  _MICI_BUTTONS[:] = active_refs
