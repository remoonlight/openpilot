import datetime
import email.utils
import ssl
import subprocess
import time
import urllib.request

from openpilot.common.time_helpers import min_date, system_time_valid

TIME_URLS = (
  "https://openpilot.comma.ai",
  "https://www.google.com",
  "https://cloudflare.com",
)

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_last_sync = 0.0


def fetch_network_time(timeout: float = 5.0) -> datetime.datetime | None:
  for url in TIME_URLS:
    try:
      req = urllib.request.Request(url, method="HEAD")
      with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        date_hdr = resp.headers.get("Date")
        if not date_hdr:
          continue
        remote = email.utils.parsedate_to_datetime(date_hdr)
        if remote.tzinfo is not None:
          remote = remote.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return remote
    except Exception:
      continue
  return None


def set_system_time(new_time: datetime.datetime) -> bool:
  if new_time < min_date():
    return False

  diff = datetime.datetime.now() - new_time
  if abs(diff) < datetime.timedelta(seconds=10):
    return True

  try:
    subprocess.run(f"TZ=UTC date -s '{new_time:%Y-%m-%d %H:%M:%S}'", shell=True, check=True)
    return True
  except subprocess.CalledProcessError:
    return False


def sync_network_time(min_interval: float = 30.0, *, force: bool = False) -> bool:
  global _last_sync

  if system_time_valid() and not force:
    return True

  now = time.monotonic()
  if now - _last_sync < min_interval:
    return system_time_valid()

  _last_sync = now
  remote = fetch_network_time()
  if remote is None:
    return False

  if not set_system_time(remote):
    return False

  return system_time_valid()
