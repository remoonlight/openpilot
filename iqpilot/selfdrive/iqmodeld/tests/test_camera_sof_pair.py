from iqpilot.selfdrive.iqmodeld.sof_pair import _SOF_SYNC_NS, sof_pair_action


def test_sof_pair_synced():
  assert sof_pair_action(1_000_000, 1_000_000) == 0
  assert sof_pair_action(1_000_000, 1_000_000 + _SOF_SYNC_NS) == 0


def test_sof_pair_extra_ahead_pulls_main():
  extra = 1_000_000_000
  main = extra - 50_000_000
  assert sof_pair_action(main, extra) == -1


def test_sof_pair_main_ahead_pulls_extra():
  main = 1_000_000_000
  extra = main - 50_000_000
  assert sof_pair_action(main, extra) == 1


if __name__ == "__main__":
  test_sof_pair_synced()
  test_sof_pair_extra_ahead_pulls_main()
  test_sof_pair_main_ahead_pulls_extra()
  print("ok")
