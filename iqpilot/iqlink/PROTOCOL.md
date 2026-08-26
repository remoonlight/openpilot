# iqlink ↔ IQ-link (BLE-only)

> **English is authoritative.** Chinese section below is a summary.  
> Field mapping lives in `protocol.py`. This file is the product contract (SSOT).

## Product model

openpilot / IQ.Pilot has **no navigation session**. The car does not own “start/cancel navigation”.

| Side | Role |
|------|------|
| Amap Auto (amapauto) | Whether the user is navigating lives only in that APK |
| IQ-link (phone) | Pushes **live parameters** (road limit, lights, TBT distance, …) over BLE; does **not** clear parameters when navigation stops |
| Device | Applies parameters only when content **changes**; otherwise keeps the last execution snapshot. If none → follow lead / model |

Notes:

- Do not model the device as nav on/off.
- There is **no** “cancel navigation” product control on the car.
- Legacy param names such as `NavigationActive` / `IqlinkExclusive` are implementation leftovers — not product features.
- **Connected (product / QA):** phone ↔ device can communicate = device HMAC `LinkState=2`. Phone GATT “connected” alone is not enough.
- **Cereal on beta:** Gaode `trafficLight` / `trafficLightRemainS` are `IQNavState` **@62 / @63**. Konn3kt `beta` already uses @49–@61 for Mapbox traffic metadata. The release-based local tree still uses @49/@50.

## TBT icons (Gaode NEW_ICON → device bucket)

- Phone remaps icon `2→1`, `3→2`; `1` and `4–25` pass through.
- Device still uses Carrot sets in `protocol.py` (member values not reordered; unknown → `none`):
  - `_TURN_LEFT` = {1, 12, 16, 17, 18}
  - `_TURN_RIGHT` = {2, 13, 19, 20, 21}
  - `_LC_LEFT` = {3, 7, 9, 22, 23}
  - `_LC_RIGHT` = {4, 8, 10, 24, 25}
  - `_ROUNDABOUT` = {5, 14, 15}
  - `_EXIT` = {6, 11}
- **lc\* → `ManeuverType.fork`**, true `_EXIT` → `exit`; the two no longer collapse.
- True exit has no left/right, so it does not fire navExit HUD by itself.
- `0 < nGoPosDist ≤ 150` → publish `arrive`, **only** stop `send_lc` / `send_turn`; do not clear `NavigationActive` / the execution snapshot (R1).
- HUD `navExit*` is gated in selfdrived (gear / remain / dedup).

## Transport

**Live parameters use BLE GATT only.** Device Wi‑Fi STA (internet / SSH) is unrelated to Partner push.

Deprecated (do not use as fallback): UDP 7705 / 7706, TCP 7713.

## Longitudinal behavior (summary)

- **Change-driven:** identical `data` payloads do not refresh the execution snapshot (link heartbeat may still update).
- **Sticky limit (R1):** keep last limit / lights / TBT until the next change. Timeouts do **not** clear the snapshot.
- **TBT distance:** no TBT speed cap. Turns / LC / exits keep road-limit `speedTarget`; curve slowdown is IQ.Dynamic. Lateral desire still fires in-window.
- **Green wave / SDI:** not in scope (no phone uplink; device ignores).
- **Road limit:** BLE reports raw `nRoadLimitSpeed` for HUD; execution = raw + device offset with a **usual floor of 60 km/h**. Invalid limit → do not invent; no snapshot → follow lead / model.
- **Traffic lights:** red/yellow aggressive decel toward stop (`accelTarget≈-2`); yellow near-distance treated like red; lead has priority; no fake green. Explicit `trafficLightRemainS` of **0 or 1** plus envelope clock aligned (`|now-ts|≤120s`) releases nav red-stop (`accelTarget≥0`). Omitted remainS keeps red stop until green. Never fake green.
- **Lane B (gate only):** `KEY_TYPE=13012` → `laneRecommend`; `straight` suppresses auto lane-change desire. No lane-change HUD.
- **Cruise UI:** product max set speed `V_CRUISE_PRODUCT_MAX_KPH=120`.

## BLE GATT

Do **not** use setup UUIDs `73f2c700-…` (Konn3kt setup only).

| Role | UUID | Flags |
|------|------|-------|
| Service | `73f2c710-5e40-4d0d-8b7f-fde61f729100` | primary |
| Param write | `73f2c711-5e40-4d0d-8b7f-fde61f729100` | write, write-without-response |
| Status notify | `73f2c712-5e40-4d0d-8b7f-fde61f729100` | notify (`{"ok":true,"t":<device_ms>}`) |

### Params (UI)

| Key | Meaning |
|-----|---------|
| `IqlinkEnabled` | Bluetooth toggle (product default on) |
| `IqlinkBlePsk` | Fixed 6-digit pair code `999999` (not shown in settings) |
| `IqlinkBleDiscovering` | Discovery window (legacy name; not for showing PSK) |
| `IqlinkBleLinkState` | `0` off / `1` connecting / `2` HMAC connected |
| `IqlinkBleConnected` | Mirror of `LinkState==2` |
| `IqlinkBlePeerConnected` | SoftBus Device1 Connected (status only; **not** green) |
| `IqlinkBlePairFailed` | Transient failure; device retries |

Top-level BT light: off=red; waiting/retry=yellow; **HMAC LinkState=2 only=green**.

### Envelope (UTF-8 JSON)

Prefer one ATT write after MTU negotiation. If fragmented, reassemble the same bytes then parse:

```json
{"v":1,"seq":123,"ts":1720000000000,"data":{...carrot fields...},"hmac":"<32 lowercase hex chars>"}
```

- `data`: flat Carrot dict with at least `nRoadLimitSpeed` (or `rgdata` wrapper).
- HMAC-SHA256 truncated to 32 hex:

```text
HMAC-SHA256(psk_utf8_bytes, f"{seq}:{ts}:".encode() + canonical_json(data)).hexdigest()[:32]
canonical_json = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",",":"), allow_nan=False)
```

### Reject

- Missing / invalid PSK
- Bad HMAC
- `|now_ms - ts| > 120000`
- Seq replay within window 128

### PSK

- Params key `IqlinkBlePsk` (STRING), exactly 6 digits, fixed to `999999`
- Never log the full PSK (mask in cloudlog)

---

## 中文摘要

- **产品**：车上无导航会话；IQ-link只推即时参数；停导不清参；已连 = 设备 `LinkState=2`。
- **传输**：仅 BLE GATT；7705/7706/7713 已废弃。
- **纵向**：变更驱动 + 粘限速；限速原值上报、执行侧常保底 60；红黄猛减速；remainS 0/1 且时钟对齐可放行；省略 remainS 保持红停；无绿波/SDI；车道 B 仅直行门控；无 TBT 压速。
- **TBT**：lc* → fork，真出口 → exit；到站 150m 内只停横向 desire，HUD 出口提示另做档位/剩余距离门控。
- **PSK**：固定 `999999`，设置页不显示。
- **契约细节以上方英文为准**；字段以实现 `protocol.py` 为准。
