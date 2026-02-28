# Camera Setup Guide

## Recommended: Reolink RLC-810A (PoE)

**Why PoE:**
- Single cable handles power + data
- No WiFi interference
- More reliable than wireless

**RTSP URL format:**
```
rtsp://admin:PASSWORD@CAMERA_IP:554/h264Preview_01_main    # main stream (4K)
rtsp://admin:PASSWORD@CAMERA_IP:554/h264Preview_01_sub     # sub stream (lower res, faster)
```

Use sub stream for `detect` role, main stream for `record` role to save GPU/bandwidth.

## Recommended Placement

### Home
| Camera | Location | Angle |
|--------|----------|-------|
| #1 | Front door / porch | Cover entrance + driveway |
| #2 | Back yard | Cover yard + rear entry |

### Office
| Camera | Location | Angle |
|--------|----------|-------|
| #3 | Office entrance / hallway | Cover door + corridor |
| #4 | Main office area | Wide angle, interior |

## Network Setup

```
Router
  └── TP-Link PoE Switch (192.168.1.X)
        ├── Camera 1 → 192.168.1.101
        ├── Camera 2 → 192.168.1.102
        ├── Camera 3 → 192.168.1.103
        └── Camera 4 → 192.168.1.104
```

Assign static IPs in your router's DHCP settings (bind by MAC address).

## Detection Zones

Define zones in `frigate/config.yml` to reduce false positives:

```yaml
cameras:
  front_door:
    zones:
      driveway:
        coordinates: 0,1080,960,1080,960,400,0,400   # polygon points
      front_path:
        coordinates: 960,1080,1920,1080,1920,400,960,400
```

Coordinates are pixel positions (x,y) in `width,height` order.
Use Frigate's UI (http://localhost:5000) to draw zones visually.
