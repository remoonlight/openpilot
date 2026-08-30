"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos/
"""
from __future__ import annotations

import hashlib
import json
import os

MODELS_BASE_URLS = (
  "https://git.konn3kt.com/teal/IQModels/raw/branch/main",
  "https://gitlvb.teallvbs.xyz/teal/IQModels/raw/branch/main",
)
CHUNK = 4 * 1024 * 1024
HTTP_TIMEOUT_S = 60.0
STREAM_RETRIES = 6


def _requests_auth():
  import importlib
  for mod in ("iqpilot_private.models.git_auth", "iqpilot.models_private_src.git_auth",
              "iqpilot.selfdrive.iqmodeld.models.git_auth"):
    try:
      return importlib.import_module(mod).get_requests_auth()
    except Exception:
      continue
  return None


def _lfs_endpoint(base_url: str) -> str:
  return base_url.split("/raw/", 1)[0] + ".git/info/lfs"


def _resolve_oid(session, base_url: str, oid: str, size: int, auth):
  import requests
  batch = session.post(f"{_lfs_endpoint(base_url)}/objects/batch",
                       data=json.dumps({"operation": "download", "transfers": ["basic"],
                                        "objects": [{"oid": oid, "size": size}]}),
                       headers={"Content-Type": "application/vnd.git-lfs+json",
                                "Accept": "application/vnd.git-lfs+json"},
                       auth=auth, timeout=HTTP_TIMEOUT_S)
  batch.raise_for_status()
  entry = batch.json()["objects"][0]
  if "actions" not in entry:
    raise requests.RequestException(f"LFS object unavailable: {entry.get('error', oid)}")
  action = entry["actions"]["download"]
  return action["href"], action.get("header", {})


def download_lfs_bundle(objects: list, dst: str, sha256: str, size: int, progress_cb=None) -> str:
  import requests
  auth = _requests_auth()
  session = requests.Session()
  os.makedirs(os.path.dirname(dst), exist_ok=True)
  tmp = dst + ".part"
  total = int(size) or sum(int(o["size"]) for o in objects)
  last_error: Exception | None = None
  for base_url in MODELS_BASE_URLS:
    for attempt in range(STREAM_RETRIES):
      try:
        digest = hashlib.sha256()
        got = 0
        with open(tmp, "wb") as f:
          for obj in objects:
            href, headers = _resolve_oid(session, base_url, obj["oid"], int(obj["size"]), auth)
            obj_auth = None if headers.get("Authorization") else auth
            with session.get(href, headers=headers, stream=True, timeout=120, auth=obj_auth) as r:
              r.raise_for_status()
              for chunk in r.iter_content(CHUNK):
                f.write(chunk)
                digest.update(chunk)
                got += len(chunk)
                if progress_cb is not None and total:
                  progress_cb(min(1.0, got / total))
        if total and got != total:
          raise RuntimeError(f"size mismatch: {got}/{total} bytes")
        if sha256 and digest.hexdigest() != sha256:
          raise RuntimeError("sha256 mismatch")
        os.replace(tmp, dst)
        return dst
      except Exception as e:
        last_error = e
        try:
          os.remove(tmp)
        except OSError:
          pass
  raise RuntimeError(f"model bundle download failed: {last_error}")
