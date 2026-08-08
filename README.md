# IQ.Pilot

English primary · [中文](#中文)

IQ.Pilot is a fork of [openpilot](https://github.com/commaai/openpilot) with IQ.Lvbs enhancements: vehicle support focus (especially Volkswagen Group / MEB), Konn3kt cloud management, and **iqlink** — live navigation parameters from the phone **IQ-link** app over BLE.

Public beta / community: https://discord.iqlvbs.com

## Features

- Stock openpilot driving stack on supported comma-class devices (Comma 3 / 3X / 4, and compatible clones)
- IQ.Lvbs vehicle and UX additions (see branch table below)
- **iqlink**: BLE GATT ingest of road limit, traffic lights, TBT distance, and related live params from IQ-link (no on-car “nav session”)
- Optional upload to **Konn3kt** with user control to disable uploads

Supported cars overview: see `iqdbc_repo/docs/CARS.md` in this tree (or the cars list published with your release branch).

## Requirements

- A modern comma or compatible device
- A [supported car](https://github.com/commaai/openpilot#supported-cars) / IQ.Pilot cars list for your branch
- A [car harness](https://comma.ai/shop/products/car-harness)

Volkswagen Group and Tesla platforms are typically the best-tested with IQ.Pilot; other makes follow stock openpilot support levels.

## Install

### Installer URL

On the device custom software URL:

```text
IQLvbs/release
```

If the device is on AGNOS 13.1 or older, install latest stock openpilot first, then IQ.Pilot.

### SSH install

Enable Developer → SSH, add your GitHub SSH key, then on the device:

```bash
cd .. && rm -rf openpilot && git clone https://github.com/IQLvbs/openpilot.git -b release && cd openpilot && sudo reboot
```

Backup-preserving variant:

```bash
cd .. && mv openpilot openpilot_backup_X && git clone https://github.com/IQLvbs/openpilot.git -b release && cd openpilot && sudo reboot
```

### Branches

| Branch | Status | Notes |
|--------|--------|-------|
| `beta` | Pre-release | Early access; expect bugs |
| `release` | Stable | Current production IQ.Pilot |
| `release-meb` | Stable | Aligned with `release`, tuned for VW MEB / MQBevo (ID.3/4/5, Golf MK8, …) |

## iqlink (phone params)

1. On device: enable **Bluetooth** in settings (green = HMAC linked).
2. On phone: install **IQ-link**, pair once, open **Amap Auto (amapauto)** as the nav source.  
   Download: [https://www.amapauto.com/download](https://www.amapauto.com/download) (`com.autonavi.amapauto`).
3. Partner pushes live parameters over BLE only (Wi‑Fi nav ports are deprecated).

Contract & acceptance:

- [`iqpilot/iqlink/PROTOCOL.md`](iqpilot/iqlink/PROTOCOL.md)
- [`iqpilot/iqlink/ACCEPTANCE.md`](iqpilot/iqlink/ACCEPTANCE.md)

Companion app repo: **iq-partner** (same release staging set).

## Data & privacy

IQ.Pilot can upload to Konn3kt (IQ.Lvbs). Uploads can be disabled in settings. See Konn3kt [Terms](https://konn3kt.com/tos) and [Privacy](https://konn3kt.com/privacy).

## License

Parent license: **IQ.Lvbs License v0.1a** (`LICENSE` / `LICENSE.md`), which also preserves the upstream comma.ai MIT notice for openpilot-derived code. Proprietary components remain subject to the IQ.Lvbs terms.

## Configuration placeholders

See [`.env.example`](.env.example) for optional local/dev overrides (SSH host, paths). Do not commit secrets.

The optional `tools` extra no longer pulls private `git.konn3kt.com` imgui/libusb mirrors. Vendor those yourself if you need them.

---

## 中文

**IQ.Pilot** 是基于 openpilot 的 IQ.Lvbs 发行版：强化车型与体验，并提供 **iqlink**——手机 **IQ-link** 经 BLE 推送限速/灯/TBT 等即时参数（车上无「导航会话」）。

### 安装

设备自定义 URL 填 `IQLvbs/release`；或 SSH 克隆对应 `release` / `release-meb` 分支后重启。

### iqlink

设备打开蓝牙；手机安装 IQ-link并对高德车机版取参；契约见 `iqpilot/iqlink/PROTOCOL.md`。详细说明以英文正文为准。

### 许可

沿用父集 **IQ.Lvbs License v0.1a**，并保留 comma.ai openpilot 的 MIT 声明。
