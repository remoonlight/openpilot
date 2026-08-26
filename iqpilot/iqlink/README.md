# IQ-link Device Guide

## English

### Bluetooth for IQ-link
IQ-link uses Bluetooth Low Energy to pair the comma with the IQ-link phone app. Navigation stays on the phone; the device shows guidance such as speed limits and turns. IQ.Pilot is driver assistance, not self-driving.

### Before you install
You need a compatible comma device, the correct harness, Wi-Fi, and a phone with the IQ-link app. Confirm vehicle support in [Discord](https://discord.iqlvbs.com) before installing.

### Installation
1. Restore stock openpilot at [flash.comma.ai](https://flash.comma.ai).
2. Finish stock setup, connect Wi-Fi, and enter `https://installer.iqlvbs.com/beta` as the custom software URL (IQ.Pilot 1.0c on IQ.OS 4.9.7, branch `beta`).
3. Wait for download and reboot. The home screen date and time should look normal.
4. If the ~1 GB download fails, retry Wi-Fi once, then use the [Gigafile package](https://105.gigafile.nu/1022-i1e58aa3443a357555c7f25a9f6a0e737) (`IQ.OS-4.9.7.zip`, SHA256 `4c068f424ebf1ed761c305a259eb47e9a1355b394a9b77106e6c17d6e9a68612`). Ask in Discord before manual flashing.
5. With `beta` running, enable ADB or SSH in Developer settings only when Cursor will deploy the overlay.
6. From this repository root:

   `python iqpilot/iqlink/tools/deploy_iqlink_overlay.py iq@DEVICE_IP`

   The tool requires Git root `/data/iqpilot` and branch `beta`. It backs up touched files under `/data/iqlink-overlay-backup-*`.
7. Apply only needed keys from [`comma_settings_public.json`](./comma_settings_public.json), reboot if needed, then pair IQ-link from the **Bluetooth** tile.

### Pair your phone
1. Connect Wi-Fi and confirm the clock on the home screen.
2. Pair the device at [app.konn3kt.com](https://app.konn3kt.com).
3. Open Settings on the device and turn on **Bluetooth**.
4. Pair when prompted. A green indicator means the phone is linked.

### Troubleshooting
| Problem | What to do |
|---|---|
| Download fails | Check Wi-Fi, retry once, then ask [Discord](https://discord.iqlvbs.com). |
| Konn3kt offline | Fix Wi-Fi and confirm device time. |
| No green Bluetooth light | Toggle **Bluetooth** off and on, then pair again. |

### Settings and overlay tool
[`comma_settings_public.json`](./comma_settings_public.json) is a redacted **VW ID.3 2024–25 / IQ-link** example, not a universal dump. Apply helpers: [`tools/apply_comma_settings_public.py`](./tools/apply_comma_settings_public.py), [`tools/export_comma_settings_public.py`](./tools/export_comma_settings_public.py).

On the device after copying the JSON and apply script:

```sh
python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json
```

## 中文

### 蓝牙功能说明
IQ-link 用低功耗蓝牙把 comma 与手机上的 IQ-link 程序连起来。导航仍在手机端进行，车机显示限速、转向等引导信息。IQ.Pilot 是驾驶辅助，不是自动驾驶。

### 安装前准备
需要兼容的 comma 设备、对应线束、Wi-Fi，以及安装了 IQ-link 程序的手机。安装前请在 [Discord](https://discord.iqlvbs.com) 确认车型是否支持。

### 安装步骤
1. 打开 [flash.comma.ai](https://flash.comma.ai)，恢复原厂 openpilot。
2. 完成原厂设置、连上 Wi-Fi，在“自定义软件地址”填写 `https://installer.iqlvbs.com/beta`（IQ.Pilot 1.0c，IQ.OS 4.9.7，分支 `beta`）。
3. 等待下载和重启完成，首页日期与时间应显示正常。
4. 若约 1 GB 文件下载失败，先重试 Wi-Fi；仍失败可使用 [Gigafile 文件](https://105.gigafile.nu/1022-i1e58aa3443a357555c7f25a9f6a0e737)（`IQ.OS-4.9.7.zip`，SHA256 `4c068f424ebf1ed761c305a259eb47e9a1355b394a9b77106e6c17d6e9a68612`）。手动刷机前请先到 Discord 求助。
5. 确认已是 `beta` 后，仅在 Cursor 辅助部署时开启 ADB 或 SSH。
6. 在本仓库根目录执行：

   `python iqpilot/iqlink/tools/deploy_iqlink_overlay.py iq@设备IP`

   工具要求 Git 根目录为 `/data/iqpilot`、分支为 `beta`，并会把改动文件备份到 `/data/iqlink-overlay-backup-*`。
7. 按需写入 [`comma_settings_public.json`](./comma_settings_public.json) 中的设置，必要时重启，再从 **蓝牙** 卡片配对 IQ-link。

### 连接手机
1. 连上 Wi-Fi，确认首页时间正确。
2. 在 [app.konn3kt.com](https://app.konn3kt.com) 完成设备配对。
3. 在车机“设置”中打开 **蓝牙**。
4. 按提示配对手机；绿灯表示已连接。

### 常见问题
| 情况 | 处理办法 |
|---|---|
| 下载失败 | 检查 Wi-Fi 并重试一次；仍失败到 [Discord](https://discord.iqlvbs.com) 求助。 |
| Konn3kt 离线 | 检查 Wi-Fi 与设备时间。 |
| 蓝牙无绿灯 | 关闭再开启 **蓝牙** 卡片，重新配对手机。 |

### 设置与部署工具
[`comma_settings_public.json`](./comma_settings_public.json) 是 **大众 ID.3 2024–25 / IQ-link** 脱敏示例，不能整份套用到其他车辆。写入脚本：[`tools/apply_comma_settings_public.py`](./tools/apply_comma_settings_public.py)、[`tools/export_comma_settings_public.py`](./tools/export_comma_settings_public.py)。

将车机上的 JSON 与脚本放到 `/tmp/` 后执行：

```sh
python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json
```

### 维护者导出

```powershell
scp iqpilot/iqlink/tools/export_comma_settings_public.py iq@10.10.10.205:/tmp/
ssh iq@10.10.10.205 '/usr/local/venv/bin/python /tmp/export_comma_settings_public.py'
```

---

## Settings / 配置 (JSON)

```json
{
  "meta": {
    "generated_cst": "2026-08-17 17:32:24",
    "source": "comma /data/params/d",
    "purpose": "GitHub-safe openpilot/IQ settings snapshot (account/device identity redacted)",
    "settings_count": 188,
    "excluded_count": 35,
    "redaction": [
      "DongleId / HardwareSerial / IMEI",
      "GithubUsername / GithubSshKeys / GitRemote",
      "WiFi / Hotspot SSID & passwords / BLE PSK",
      "Mapbox / API tokens & caches",
      "NavDestination / NavigationDestination / GPS / routes",
      "CalibrationParams / CarParams* / VIN / fingerprints",
      "GsmApn / cellular metering",
      "Live IqlinkBle* link state",
      "Uptime / route counts / update timestamps",
      "Personal updater branches (cursor/cloud-agent*)"
    ],
    "note": "0/1 are kept as integers (device stores BOOL and INT enums the same way). Restore is manual: copy only the keys you intend to change.",
    "docs": "iqpilot/iqlink/README.md"
  },
  "settings": {
    "AdbEnabled": 1,
    "AllowLateralWhenLongUnavailable": 1,
    "AlphaLongitudinalEnabled": 1,
    "AmbientTrackDots": 1,
    "AolEnabled": 1,
    "AolMainCruiseAllowed": 1,
    "AolSteeringMode": 1,
    "AolUnifiedEngagementMode": 1,
    "AutoLaneChangeBsmDelay": 0,
    "AutoLaneChangeTimer": 1,
    "BlindSpot": 0,
    "Brightness": 0,
    "CameraOffset": 0.0,
    "CarPlatformBundle": {
      "platform": "VOLKSWAGEN_ID3_MK2",
      "make": "Volkswagen",
      "brand": "volkswagen",
      "model": "ID.3",
      "year": [
        "2024",
        "2025"
      ],
      "package": "Adaptive Cruise Control (ACC) & Lane Assist",
      "name": "Volkswagen ID.3 2024-25"
    },
    "ChevronInfo": 0,
    "IQLeadReadouts": 0,
    "CompletedTrainingVersion": "0.2.0",
    "ConstructionZoneAssist": 0,
    "ConstructionZoneSpeed": 60,
    "DashcamEnabled": 1,
    "DeveloperUI": 0,
    "DeviceBootMode": 0,
    "DisableUpdates": 1,
    "DisengageOnAccelerator": 0,
    "EnableCurvatureController": 0,
    "EnableEsimProvisioning": 1,
    "EnableLongComfortMode": 0,
    "EnableSLPredReactToCurves": 0,
    "EnableSLPredReactToSL": 0,
    "EnableSpeedLimitControl": 0,
    "EnableSpeedLimitPredicative": 0,
    "ExperimentalMode": 1,
    "FlockCameraAlerts": 0,
    "ForceRHDForBSM": 0,
    "ForceSmallUI": 0,
    "GitBranch": "iqlink",
    "GitCommit": "879df50256e69e112c2aa91ca30387a97546609e",
    "GitCommitDate": "'1785935590 2026-08-05 21:13:10 +0800'",
    "GreenLightAlert": 0,
    "HasAcceptedTerms": 2,
    "HomePanelWidget": "changelog",
    "HyundaiLongitudinalTuning": 0,
    "IQAlertSilence": 0,
    "IQBlinkerMinLateralSpeed": 20,
    "IQBlinkerPauseLateral": 0,
    "IQCustomStopDistance": 0,
    "IQDevUIInfo": 0,
    "IQDynamicBlendStockRadar": 0,
    "IQDynamicConditionalCurves": 1,
    "IQDynamicConditionalLeadSpeed": 24.0,
    "IQDynamicConditionalModelStops": 1,
    "IQDynamicConditionalSLCFallback": 1,
    "IQDynamicConditionalSlowerLead": 1,
    "IQDynamicConditionalSpeed": 18.0,
    "IQDynamicConditionalStoppedLead": 1,
    "IQDynamicMinimumForceStopLength": 0.0,
    "IQDynamicMode": 0,
    "IQDynamicModelStopTime": 2.5,
    "IQE2ESetSpeedMode": 0,
    "IQE2ESetSpeedMph": 65,
    "IQE2ESetSpeedUseCurrent": 0,
    "IQExpandedStatus": 0,
    "IQForceStops": 1,
    "IQLaneTurnDesire": 1,
    "IQLaneTurnValue": 19.0,
    "IQSpeedAssistMode": 1,
    "IQSpeedAssistOffsetType": 0,
    "IQSpeedAssistPolicy": 3,
    "IQSpeedAssistValueOffset": 0,
    "InteractivityTimeout": 0,
    "IqlinkAggressiveLaneChange": 1,
    "IqlinkCancelTimeoutS": 5,
    "IqlinkEnabled": 1,
    "IqlinkExclusive": 1,
    "IqlinkLinkWarn": 0,
    "IqlinkProductCruiseDefaultsV1": 1,
    "IqlinkWarnTimeoutS": 3,
    "IsDevelopmentBranch": 0,
    "IsMetric": 1,
    "IsReleaseBranch": 0,
    "IsReleaseIqBranch": 0,
    "IsRhdDetected": 0,
    "IsTestedBranch": 0,
    "Konn3ktAllowOffroadExternalCanTx": 0,
    "Konn3ktBleTransportEnabled": 1,
    "Konn3ktLibdatachannelWebRTC": 0,
    "LagdToggle": 1,
    "LagdToggleDelay": 0.2,
    "LagdValueCache": 0.5,
    "LaneChangeBsd": 0,
    "LaneChangeContinuous": 1,
    "LaneChangeDelay": 0.0,
    "LaneChangeNeedTorque": 0,
    "LanguageSetting": "zh-CHS",
    "LatSmoothSec": 13,
    "LeadDepartAlert": 0,
    "LongIncrementHoldStep": 5,
    "LongIncrementTapStep": 10,
    "LongIncrementsEnabled": 1,
    "LongitudinalPersonality": 0,
    "MapCurveSpeedController": 0,
    "MapSpeedLookaheadHigher": 5.0,
    "MapSpeedLookaheadLower": 5.0,
    "MaxTimeOffroad": 1800,
    "ModelLatSmoothSec": 0,
    "ModelSmoothingEnabled": 0,
    "NavExitLaneChange": 1,
    "NavOfflineFallback": 1,
    "NavOnlineTargets": 1,
    "NavPreferOfflineSources": 0,
    "NavigateOnIQPilot": 1,
    "NavigationEnabled": 0,
    "NavigationRecalculateRoutes": 0,
    "NetworkMetered": 0,
    "NeuralNetworkFeedForward": 0,
    "NightMode": 0,
    "OBrightness": 0,
    "OBrightnessDelay": 0,
    "OBrightnessManual": 0,
    "OSMapsHeadingUp": 1,
    "OSMapsStyleMode": 0,
    "OfflineOSMaps": 0,
    "OfflineRoutingEnabled": 1,
    "OfflineRoutingHost": "http://127.0.0.1:8002",
    "OfflineRoutingOnly": 0,
    "OnScreenNavigation": 0,
    "OnlineOSMaps": 1,
    "OnroadScreenOffBrightness": 0,
    "OnroadScreenOffTimer": 15,
    "OnroadUploads": 1,
    "OpenpilotEnabledToggle": 1,
    "OsmStateName": "All",
    "PlanplusControl": 1.0,
    "RainbowMode": 0,
    "RecordAudioFeedback": 0,
    "RecordFront": 0,
    "RedLightCameraAlerts": 0,
    "RoadNameToggle": 0,
    "RocketFuel": 0,
    "SLCAutoConfirm": 0,
    "SLCDataCollection": 0,
    "SLCFallbackExperimentalMode": 1,
    "SLCFallbackPreviousSpeedLimit": 1,
    "SLCFallbackSetSpeed": 0,
    "SLCOnlineFiller": 0,
    "SLCOverrideMethod": 0,
    "SLCPolicy": 2,
    "SLCSetSpeedToLimit": 0,
    "ScreenRecording": 0,
    "ShowBSMIndicators": 0,
    "ShowRealTimeAcceleration": 0,
    "ShowRoadName": 0,
    "ShowSpeedLimits": 0,
    "ShowSteeringArc": 0,
    "ShowTurnSignals": 0,
    "SpeedCameraAlerts": 0,
    "SpeedCameraSafetyFactor": 1.0,
    "SpeedCameraSlowdown": 0,
    "SpeedLimitConfirmationHigher": 1,
    "SpeedLimitConfirmationLower": 0,
    "SpeedLimitController": 0,
    "SshEnabled": 1,
    "StandstillTimer": 0,
    "SubaruStopAndGo": 0,
    "SubaruStopAndGoManualParkingBrake": 0,
    "TeslaCoopSteering": 0,
    "TorqueBar": 1,
    "ToyotaEnforceStockLongitudinal": 0,
    "ToyotaSnGHack": 0,
    "UIAccentColor": "#00FFF5",
    "UbloxAvailable": 1,
    "UpdaterAvailableBranches": "iqlink,release-meb",
    "UpdaterInstallMode": "download_and_install",
    "UsbStorageEnabled": 1,
    "Version": "IQ.Pilot 1.0c",
    "VisionCurveSpeedController": 0,
    "VisionVehicleTracks": 0,
    "eBrakeActive": 0,
    "iqMqbAccResume": 0,
    "iqMqbSteeringLockout": 0,
    "newLeadMpc": 1,
    "speed_limit_offset1": 0.0,
    "speed_limit_offset2": 0.0,
    "speed_limit_offset3": 0.0,
    "speed_limit_offset4": 0.0,
    "speed_limit_offset5": 0.0,
    "speed_limit_offset6": 0.0,
    "speed_limit_offset7": 0.0
  }
}
```
