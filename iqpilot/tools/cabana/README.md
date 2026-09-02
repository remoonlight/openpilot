# Cabana

Cabana is IQ.Pilot's desktop CAN analysis tool. It uses ImGui and GLFW on macOS and Linux without Qt.

Run it through the project command:

```bash
iq cabana
```

Cabana can open a local route, a Konn3kt route, a Panda, SocketCAN on Linux, local msgq, or a remote ZMQ stream.

```bash
iq cabana "dongle_id|2026-09-02--12-00-00"
iq cabana --panda
iq cabana --msgq
iq cabana --zmq 192.168.1.10
iq cabana --bridge 192.168.1.10
```

The executable is built on demand by `iqpilot/tools/cabana/cabana`. IQ.Pilot prebuilt device checkouts intentionally omit desktop analysis tools.
