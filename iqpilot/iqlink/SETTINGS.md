# IQ-link settings for known issues

Device Params on this comma (VW ID.3 2024–25 / IQ-link). These are **problem-specific keys**, not a full backup. Full snapshot: [`comma_settings_public.json`](./comma_settings_public.json). Apply with [`tools/apply_comma_settings_public.py`](./tools/apply_comma_settings_public.py), then reboot.

## English

### Low-speed left-right weave (MEB)

| Key | Value | Where |
|---|---|---|
| `EnableSmoothSteer` | `1` | Settings → Vehicle → **Smooth Steering** |
| `EnableCurvatureController` | `0` | leave **Curvature Controller** off |

`EnableSmoothSteer` is **not** in `comma_settings_public.json` yet (default in `params_keys.h` is `"0"`). Set it on the device. The snapshot already has `EnableCurvatureController=0` and `LatSmoothSec=13`.

### Longitudinal speed increment (ACC buttons)

| Key | Value | Meaning |
|---|---|---|
| `LongIncrementsEnabled` | `1` | tap/hold speed steps on |
| `LongIncrementTapStep` | `10` | tap step; with `IsMetric=1` this is km/h |
| `LongIncrementHoldStep` | `5` | hold step |
| `IsMetric` | `1` | this car uses km/h |

These four keys are already in `comma_settings_public.json`. Re-apply that file if the device lost them.

### Map speed-limit assist (off)

Road limit comes from IQ-link BLE + APK. Map/SLC must stay off so it does not fight that path.

| Key | Value | Meaning |
|---|---|---|
| `IQSpeedAssistMode` | `0` | off (no map info/warn/control) |
| `SpeedLimitController` | `0` | do not move cruise from map/dashboard limits |
| `ShowSpeedLimits` | `0` | no map-limit HUD |

The Cruise menu no longer exposes Speed Limit / speed limit settings.

### IQ-link timeout behavior

| Key | Meaning |
|---|---|
| `IqlinkWarnTimeoutS` | After this no-write interval, the bridge raises a link warning and the planner suppresses IQ-link longitudinal navigation. It does not clear the execution snapshot. |
| `IqlinkCancelTimeoutS` | Legacy name only: it no longer clears navigation parameters and currently has no timeout action. Sticky parameters remain until changed content or Bluetooth is turned off. |

---

## 中文

设备 Params（大众 ID.3 2024–25 / IQ-link）。下面只记**按问题对照的键**，不是整机备份。完整快照见 [`comma_settings_public.json`](./comma_settings_public.json)，用 [`tools/apply_comma_settings_public.py`](./tools/apply_comma_settings_public.py) 写入后重启。

### 低速左右摇摆（MEB）

| 键 | 值 | 位置 |
|---|---|---|
| `EnableSmoothSteer` | `1` | 设置 → 车辆 → **Smooth Steering** |
| `EnableCurvatureController` | `0` | **Curvature Controller** 保持关闭 |

`EnableSmoothSteer` **还不在** `comma_settings_public.json` 里（`params_keys.h` 默认 `"0"`），需要在车机上打开。快照里已有 `EnableCurvatureController=0`、`LatSmoothSec=13`。

### 纵向调速步进（ACC 按键）

| 键 | 值 | 含义 |
|---|---|---|
| `LongIncrementsEnabled` | `1` | 打开点按/长按调速步进 |
| `LongIncrementTapStep` | `10` | 点按步进；`IsMetric=1` 时为 km/h |
| `LongIncrementHoldStep` | `5` | 长按步进 |
| `IsMetric` | `1` | 本车用公里 |

这四项已在 `comma_settings_public.json`。设备丢了就重新套用该文件。

### 地图限速辅助（关）

路限由 IQ-link 蓝牙 + 手机程序提供。地图/SLC 必须关掉，避免跟这条路径抢控速。

| 键 | 值 | 含义 |
|---|---|---|
| `IQSpeedAssistMode` | `0` | 关（不显示、不警告、不改巡航） |
| `SpeedLimitController` | `0` | 不用地图/仪表限速改巡航 |
| `ShowSpeedLimits` | `0` | 不显示地图限速 HUD |

Cruise 菜单不再出现 Speed Limit / speed limit settings。

### IQ-link 超时行为

| 键 | 含义 |
|---|---|
| `IqlinkWarnTimeoutS` | 超过该无写包时长，bridge 会告警，规划器会屏蔽 IQ-link 导航纵向；不会清执行快照。 |
| `IqlinkCancelTimeoutS` | 仅为遗留名称：不再清导航参数，当前也没有超时动作；粘性参数会保留到内容变化或关闭蓝牙。 |
