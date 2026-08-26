# iqlink road acceptance

> **English is authoritative.** Chinese section below is a short checklist.  
> Aligns with `PROTOCOL.md` (SSOT). Human checklist only — not imported at runtime.

## Product model (read first)

- No navigation session on the car; IQ-link pushes **live parameters**.
- Device applies **changed** content only; sticky snapshot until next change.
- No snapshot → follow lead / model.
- Nav start/cancel lives only in **Amap Auto**; no car “cancel nav” button; no product “exclusive nav”.
- Legacy names `NavigationActive` / `IqlinkExclusive` are **not** pass/fail criteria.
- **Connected:** device HMAC `LinkState=2` (phone GATT alone is insufficient).

## Functional baseline

- Partner params mainly affect **longitudinal** behavior; lateral only desire for lane-change / exit. Core safety stays with stock logic.
- **Limit HUD vs control:** BLE sends raw value; execution = base + offset, usual floor **≥60 km/h** (except red/yellow approach). Do not invent limits.
- **Green wave / SDI:** out of scope — do not accept.
- **TBT / curves:** no TBT distance speed cap (`speedTarget` stays at road limit; curves via IQ.Dynamic); lateral desire still in-window. `0 < nGoPosDist ≤ 150` must not send `send_lc` / `send_turn`.
- **Arrive / reverse park:** must not spam exit-maneuver HUD (Chinese “导航：准备驶出匝道” / English `Navigation: Exit Maneuver`); a real highway exit may still prompt once. Limit/light snapshot stays after arrive.
- **Lights:** red/yellow → aggressive decel toward stop; lead has priority; no fake green. Explicit remainS 0 or 1 + aligned clocks may release; omitted remainS keeps red stop.
- **Sticky / change-driven:** identical packets do not refresh snapshot; long silence may warn but must **not** clear snapshot. Clearing leftover bits only when BT toggle is off.
- **Cruise UI:** default max set **120 km/h**; wheel step **±10 km/h**.

## Known limits (accepted)

- Amap Auto may report `LIMITED_SPEED` as `-1` / floor `30` in cities; do not fabricate substitutes; do not use camera speed as road limit.
- Lane B is a **gate only** (`straight` suppresses auto lane change) — no HUD / precise lane pick.
- BLE: steady state should stay HMAC-connected; SoftBus flaps may keep advertising without demoting immediately. Cold start reconnect is typically seconds to tens of seconds.

## Connect & operate (BLE)

1. Device: Settings → **Bluetooth** (default on). Green = HMAC `LinkState=2`. PSK fixed `999999` (hidden in UI).
2. Phone: install **IQ-link**; system BT pair once + in-app “Scan & pair” once (no PSK entry). Push on by default.
3. Data source: **Amap Auto (amapauto)** standard broadcast → Partner → BLE. Accessibility scraping is deprecated.
4. Do **not** rely on hotspot / Wi‑Fi 7705/7706/7713.

## Hard fail (any one fails the run)

- Collision risk / improper disengage / **model should stop but did not** / stop-moment **Cruise Faulted**.
- Aggressive lane change into occupied adjacent lane.
- Red/yellow approach without clear aggressive slowing when expected; Partner must yield to lead when present.

## Evidence

- Prefer **rlog + on-device** fields (`iqNavState` speed / TBT / light). Split across trips is OK.
- Virtual / desk injection is useful for bring-up but does **not** count as full road Done.

## Progress signals (pick one per road trip)

1. Raw limit on HUD + execution floor 60 (e.g. city 40 reported as 40, control ≥60 except light approach).
2. TBT distance slowdown or stricter curve vs bare limit.
3. Red/yellow aggressive decel with recovery after green.

## Explicitly out of product

- Car “cancel navigation” / “nav exclusive”
- Treating “stop pushing” as “cancel one navigation”
- Green-wave / SDI camera slowing
- Accessibility / phone minimap as primary source
- Smart lane pick / lane-change HUD beyond straight gate

## Related

- Transport contract (SSOT): `PROTOCOL.md`
- Phone app: companion repo **iq-partner**

---

## 中文清单

1. 车上无导航会话；已连 = 设备绿灯 `LinkState=2`。  
2. 限速原值上报、控车常 ≥60；红黄应猛减速；无绿波/SDI。  
3. 粘限速：同内容不清快照；关蓝牙开关才清遗留位。  
4. 硬失败：该停未停 / Cruise Faulted / 占道仍变道。  
5. 证据以 rlog + `iqNavState` 为准；细节以英文正文为准。
