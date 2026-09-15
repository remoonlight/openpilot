# IQ-link Device Guide

## English

### Bluetooth for IQ-link
IQ-link uses Bluetooth Low Energy to pair the comma with the IQ-link phone app. Navigation stays on the phone; the device shows guidance such as speed limits and turns. IQ.Pilot is driver assistance, not self-driving.

### Before you install
You need a compatible comma device, the correct harness, Wi-Fi, and a phone with the IQ-link app. Confirm vehicle support in [Discord](https://discord.iqlvbs.com) before installing.

### Installation
1. Restore stock openpilot at [flash.comma.ai](https://flash.comma.ai).
2. Finish stock setup, connect Wi-Fi, and enter `https://installer.iqlvbs.com/release-candidate-4` as the custom software URL to install the required `beta` device base.
3. Wait for download and reboot. The home screen date and time should look normal.
4. If the ~1 GB download fails, retry Wi-Fi once, then use the [Gigafile package](https://105.gigafile.nu/1022-i1e58aa3443a357555c7f25a9f6a0e737) (`IQ.OS-4.9.7.zip`, SHA256 `4c068f424ebf1ed761c305a259eb47e9a1355b394a9b77106e6c17d6e9a68612`). Ask in Discord before manual flashing.
5. With the `beta` device base running, enable ADB or SSH in Developer settings only when Cursor will deploy the overlay.
6. From this repository root:

   `python iqpilot/iqlink/tools/deploy_iqlink_overlay.py iq@DEVICE_IP`

   The tool requires Git root `/data/iqpilot` and asserts that its checked-out branch is `beta`. It backs up touched files under `/data/iqlink-overlay-backup-*`.

   Branch names serve different purposes: this source repository is maintained on `iq-link`; the public settings snapshot records that device's `GitBranch` as `iqlink`; deployment is allowed only to the `beta` base asserted by the script. The snapshot is evidence, not a deploy target.
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
Problem-specific keys (smooth steer, long increment, map speed-limit off): [`SETTINGS.md`](./SETTINGS.md).
[`comma_settings_public.json`](./comma_settings_public.json) is the **recommended snapshot from this comma** (redacted VW ID.3 2024–25 / IQ-link), not a dump for every car. Same platform: apply the file after overlay. Other cars: copy only the keys you intend to change. Helpers: [`tools/apply_comma_settings_public.py`](./tools/apply_comma_settings_public.py), [`tools/export_comma_settings_public.py`](./tools/export_comma_settings_public.py). Reboot after writing.

The JSON is the complete settings snapshot; it is intentionally not duplicated here. `IqlinkExclusive`, `NavigateOnIQPilot`, `Nav*`, `Osm*`, `OfflineOSMaps`, and `OfflineRouting*` are lazy/legacy keys: the overlay keeps `navd` and `mapd` off and pins offline maps off at boot, so they do not enable a navigation session, OSM routing, or offline tiles. Planning and process notes stay in the local `docs/` folder and are not uploaded to git.

From the repository root:

```powershell
scp iqpilot/iqlink/comma_settings_public.json iqpilot/iqlink/tools/apply_comma_settings_public.py iq@DEVICE_IP:/tmp/
ssh iq@DEVICE_IP "python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json"
```

On the device if the files are already in `/tmp/`:

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
2. 完成原厂设置、连上 Wi-Fi，在“自定义软件地址”填写 `https://installer.iqlvbs.com/release-candidate-4`，安装所需的 `beta` 设备底座。
3. 等待下载和重启完成，首页日期与时间应显示正常。
4. 若约 1 GB 文件下载失败，先重试 Wi-Fi；仍失败可使用 [Gigafile 文件](https://105.gigafile.nu/1022-i1e58aa3443a357555c7f25a9f6a0e737)（`IQ.OS-4.9.7.zip`，SHA256 `4c068f424ebf1ed761c305a259eb47e9a1355b394a9b77106e6c17d6e9a68612`）。手动刷机前请先到 Discord 求助。
5. 确认设备已运行 `beta` 底座后，仅在 Cursor 辅助部署时开启 ADB 或 SSH。
6. 在本仓库根目录执行：

   `python iqpilot/iqlink/tools/deploy_iqlink_overlay.py iq@设备IP`

   工具要求 Git 根目录为 `/data/iqpilot`，并断言其检出分支为 `beta`；改动文件会备份到 `/data/iqlink-overlay-backup-*`。

   三个分支名用途不同：本源码仓维护分支是 `iq-link`；公开设置快照里的设备 `GitBranch` 是 `iqlink`；部署脚本只允许断言为 `beta` 的设备底座。快照仅是采样证据，不是部署目标。
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
按问题对照的键（平滑转向、纵向步进、地图限速关闭）见 [`SETTINGS.md`](./SETTINGS.md)。
[`comma_settings_public.json`](./comma_settings_public.json) 是这台 comma 上脱敏后的**建议配置**（大众 ID.3 2024–25 / IQ-link），不是所有车的通用备份。同平台 overlay 后建议整份套用；其他车只写入你要改的键。脚本：[`tools/apply_comma_settings_public.py`](./tools/apply_comma_settings_public.py)、[`tools/export_comma_settings_public.py`](./tools/export_comma_settings_public.py)。写完重启一次。

完整设置只保留在 JSON，不在本页重复内嵌。快照中的 `IqlinkExclusive`、`NavigateOnIQPilot`、`Nav*`、`Osm*`、`OfflineOSMaps`、`OfflineRouting*` 是惰性/遗留键：overlay 关闭 `navd`、`mapd`，开机强制关掉离线地图，它们不会开启车上导航会话、OSM 路由或离线底图。规划与过程文档只放本仓库本地 `docs/`，不上传 git。

在本仓库根目录：

```powershell
scp iqpilot/iqlink/comma_settings_public.json iqpilot/iqlink/tools/apply_comma_settings_public.py iq@设备IP:/tmp/
ssh iq@设备IP "python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json"
```

文件已在车机 `/tmp/` 时：

```sh
python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json
```

### 维护者导出

```powershell
scp iqpilot/iqlink/tools/export_comma_settings_public.py iq@10.10.10.205:/tmp/
ssh iq@10.10.10.205 '/usr/local/venv/bin/python /tmp/export_comma_settings_public.py'
```

---

## Settings / 配置

See the complete, redacted snapshot: [comma_settings_public.json](./comma_settings_public.json).

完整脱敏快照见：[comma_settings_public.json](./comma_settings_public.json)。
