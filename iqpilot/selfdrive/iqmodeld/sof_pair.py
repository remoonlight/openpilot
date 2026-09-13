_SOF_SYNC_NS = 10_000_000
_SOF_PAIR_MAX_STEPS = 8


def sof_pair_action(main_sof: int, extra_sof: int, max_skew_ns: int = _SOF_SYNC_NS) -> int:
  # 0 = paired, -1 = extra ahead so pull main, +1 = main ahead so pull extra.
  delta = main_sof - extra_sof
  if abs(delta) <= max_skew_ns:
    return 0
  return -1 if delta < 0 else 1
