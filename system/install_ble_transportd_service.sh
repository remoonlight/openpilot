#!/usr/bin/bash
set -e

SERVICE_FILE="/data/openpilot/system/ble-transportd.service"
SERVICE_NAME="ble-transportd.service"
SERVICE_OVERRIDE="/etc/systemd/system/${SERVICE_NAME}"
SERVICE_BAKED="/lib/systemd/system/${SERVICE_NAME}"

# Kept outside *.d path — gitignore has `*.d` which would drop service.d/.
DROPIN_SRC="/data/openpilot/system/ble-transportd-dropins/bluez-ready.conf"
DROPIN_DST="/etc/systemd/system/${SERVICE_NAME}.d/bluez-ready.conf"

echo "Installing BLE transportd systemd service..."

if [ -f "$SERVICE_BAKED" ] && grep -q "/usr/libexec/iqpilot/iqpilot_bundle_runner" "$SERVICE_BAKED"; then
    echo "Using IQ.OS baked ${SERVICE_NAME}; removing stale full-unit override if present..."
    sudo mount -o remount,rw /
    sudo rm -f "$SERVICE_OVERRIDE"
    # Drop-in only — never rewrite /usr/lib unit (rootfs integrity signed).
    if [ -f "$DROPIN_SRC" ]; then
      sudo mkdir -p "$(dirname "$DROPIN_DST")"
      sudo cp "$DROPIN_SRC" "$DROPIN_DST"
      echo "Installed drop-in $DROPIN_DST"
    fi
    sudo systemctl daemon-reload
    sudo mount -o remount,ro /
else
    if [ ! -f "$SERVICE_FILE" ]; then
        echo "ERROR: Service file not found at $SERVICE_FILE"
        exit 1
    fi

    echo "IQ.OS baked unit unavailable; installing fallback override into /etc/systemd/system..."
    sudo cp "$SERVICE_FILE" "$SERVICE_OVERRIDE"
    sudo systemctl daemon-reload
fi

echo "Enabling $SERVICE_NAME to start at boot..."
# -n: never prompt for password (launch must not hang on TTY ask-password).
if ! sudo -n systemctl enable "$SERVICE_NAME" 2>/dev/null; then
  echo "WARN: cannot enable $SERVICE_NAME without sudo password; leaving as-is"
fi

echo "Starting $SERVICE_NAME..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
  if sudo -n systemctl restart "$SERVICE_NAME" 2>/dev/null; then
    echo "Restarted $SERVICE_NAME"
  else
    echo "WARN: $SERVICE_NAME already active; skip restart (no passwordless sudo)"
  fi
else
  if ! sudo -n systemctl restart "$SERVICE_NAME" 2>/dev/null; then
    echo "ERROR: cannot start $SERVICE_NAME without sudo password"
    exit 1
  fi
fi

echo ""
echo "Service status:"
systemctl status "$SERVICE_NAME" --no-pager || true

echo ""
echo "Useful commands:"
echo "  sudo systemctl status ble-transportd    - Check service status"
echo "  sudo systemctl restart ble-transportd   - Restart service"
echo "  sudo systemctl stop ble-transportd      - Stop service"
echo "  sudo journalctl -u ble-transportd -f    - View live logs"
