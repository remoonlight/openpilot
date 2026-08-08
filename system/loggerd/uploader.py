#!/usr/bin/env python3
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.iqpilot._proprietary_loader import load_private_module
from openpilot.system.loggerd.route_upload import (
  get_route_base,
  mark_route_uploaded,
  sanitize_athenad_upload_queue,
  should_defer_route_upload,
  should_skip_route_upload,
)

_private = load_private_module(__name__, "iqpilot_private.konn3kt.uploaderd.iquploaderd")


def _patch_iquploader(cls) -> None:
  original_list = cls.list_upload_files

  def list_upload_files(self, metered: bool):
    offroad = Params().get_bool("IsOffroad")
    route_state: dict[str, str] = {}

    for name, key, fn in original_list(self, metered):
      logdir = key.split("/", 1)[0]
      route_base = get_route_base(logdir)
      if route_base is None:
        yield name, key, fn
        continue

      state = route_state.get(route_base)
      if state is None:
        if should_defer_route_upload(route_base, offroad, self.root):
          state = "defer"
        elif should_skip_route_upload(route_base, offroad, self.root):
          cloudlog.event("uploader_route_skipped", route=route_base)
          mark_route_uploaded(route_base, self.root)
          state = "skip"
        else:
          state = "ok"
        route_state[route_base] = state

      if state == "ok":
        yield name, key, fn

  cls.list_upload_files = list_upload_files


_patch_iquploader(IQUploader)
sanitize_athenad_upload_queue()

_original_main = main


def main(exit_event=None):
  sanitize_athenad_upload_queue()
  return _original_main(exit_event)


if __name__ == "__main__":
  main()
