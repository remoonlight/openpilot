# IQ.Pilot IQ-link

## English

### Bluetooth for IQ-link
This repository adds Bluetooth Low Energy support on the comma device so it can pair with the IQ-link phone app. After installation, turn on the **Bluetooth** tile in Settings and pair your phone. Navigation still runs on the phone; the device receives speed limits, turns, and related guidance. IQ.Pilot is driver assistance, not self-driving: stay attentive and ready to take over.

### Install
1. Restore stock openpilot at [flash.comma.ai](https://flash.comma.ai).
2. Finish stock setup, connect Wi-Fi, and enter this custom software URL:

   `https://installer.iqlvbs.com/beta`

3. Wait until the device finishes downloading, reboots, and shows the normal home screen.
4. If the ~1 GB IQ.Lvbs download fails, use the [Gigafile package](https://105.gigafile.nu/1022-i1e58aa3443a357555c7f25a9f6a0e737) (`IQ.OS-4.9.7.zip`, SHA256 `4c068f424ebf1ed761c305a259eb47e9a1355b394a9b77106e6c17d6e9a68612`). Ask in [Discord](https://discord.iqlvbs.com) before manually flashing it.
5. When `beta` is running, open Developer settings and enable ADB or SSH only if Cursor will help deploy the overlay from this repository.
6. From this repository root, apply the tracked IQ-link overlay:

   `python iqpilot/iqlink/tools/deploy_iqlink_overlay.py iq@DEVICE_IP`

7. Apply only the keys you need from the [public settings example](iqpilot/iqlink/comma_settings_public.json), reboot if prompted, then pair IQ-link from the Bluetooth tile.

### Recommended comma settings
[`comma_settings_public.json`](iqpilot/iqlink/comma_settings_public.json) is the **suggested snapshot from this comma** (VW ID.3 2024–25 / IQ-link). After overlay, apply it so IQ-link, language, and related toggles match that device. Same make/year: apply the file. Other cars: copy only the keys you mean to change (skip VIN/fingerprint/identity). Then reboot.

```powershell
scp iqpilot/iqlink/comma_settings_public.json iqpilot/iqlink/tools/apply_comma_settings_public.py iq@DEVICE_IP:/tmp/
ssh iq@DEVICE_IP "python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json"
```

Details and troubleshooting: [IQ-link device guide](iqpilot/iqlink/README.md).

## 中文

### 给 IQ-link 用的蓝牙功能
本仓库会在 comma 设备上增加低功耗蓝牙，用来和手机上的 IQ-link 程序配对。安装完成后，在设备“设置”里打开 **蓝牙** 卡片，再按提示连接手机。导航仍在手机上进行，车机接收限速、转向等导航信息。IQ.Pilot 是驾驶辅助，不是自动驾驶；请始终看路，并随时准备接管车辆。

### 安装方法
1. 打开 [flash.comma.ai](https://flash.comma.ai)，先把设备恢复为原厂 openpilot。
2. 完成原厂设置、连上 Wi-Fi，在“自定义软件地址”填写：

   `https://installer.iqlvbs.com/beta`

3. 等待设备下载完成、自动重启，并进入正常首页。
4. 如果 IQ.Lvbs 约 1 GB 的下载失败，可改用 [Gigafile 文件](https://105.gigafile.nu/1022-i1e58aa3443a357555c7f25a9f6a0e737)（`IQ.OS-4.9.7.zip`，SHA256 `4c068f424ebf1ed761c305a259eb47e9a1355b394a9b77106e6c17d6e9a68612`）。手动刷机前请到 [Discord](https://discord.iqlvbs.com) 求助，不要自行猜测。
5. 确认设备已是 `beta` 后，只有需要 Cursor 辅助部署时，才在“开发者设置”里开启 ADB 或 SSH。
6. 在本仓库根目录执行，把本 Git 的 IQ-link 程序套用到车机：

   `python iqpilot/iqlink/tools/deploy_iqlink_overlay.py iq@设备IP`

7. 建议套用[公开设置示例](iqpilot/iqlink/comma_settings_public.json)（本 comma 的建议配置），必要时重启，再从 **蓝牙** 卡片配对 IQ-link 程序。

### 建议套用本 comma 的设置
[`comma_settings_public.json`](iqpilot/iqlink/comma_settings_public.json) 是这台 comma 上脱敏后的**建议配置**（大众 ID.3 2024–25 / IQ-link）。overlay 之后套用，语言、IQ-link 和相关开关会与该车一致。同车型可整份写入；其他车只拷你要改的键，不要改身份/VIN/指纹。写完重启一次。

```powershell
scp iqpilot/iqlink/comma_settings_public.json iqpilot/iqlink/tools/apply_comma_settings_public.py iq@设备IP:/tmp/
ssh iq@设备IP "python3 /tmp/apply_comma_settings_public.py /tmp/comma_settings_public.json"
```

更完整的步骤与排障见 [IQ-link 车机说明](iqpilot/iqlink/README.md)。

## Support and legal

Confirm vehicle support and get help in [Discord](https://discord.iqlvbs.com). Use is subject to this repository's license, the [Terms of Service](https://konn3kt.com/tos), and the [Privacy Policy](https://konn3kt.com/privacy).
