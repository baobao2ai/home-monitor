# WiFi Hotspot Setup (No Router Environment)

Used when the machine and camera are physically close but no private WiFi exists.
The machine shares its ethernet internet connection (`eno2`) through a WiFi hotspot (`wlp0s20f3`).

## Hardware

- WiFi adapter: `wlp0s20f3` (supports AP mode ✅)
- Internet uplink: `eno2` (ethernet)

## Setup Commands

### 1. Create hotspot (run once)
```bash
sudo nmcli device wifi hotspot ifname wlp0s20f3 ssid "home-monitor" password "frigatesetup" band bg
```

### 2. Enable internet sharing (NAT)
```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eno2 -j MASQUERADE
sudo iptables -A FORWARD -i wlp0s20f3 -o eno2 -j ACCEPT
sudo iptables -A FORWARD -i eno2 -o wlp0s20f3 -m state --state RELATED,ESTABLISHED -j ACCEPT
echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-hotspot.conf
```

### 3. Find camera IP after it connects
```bash
arp -n | grep wlp0s20f3
# or
ip neigh show dev wlp0s20f3
```

## Network Layout

```
Internet
   │
  eno2 (ethernet)
   │
  [Machine / Frigate host]
   │
  wlp0s20f3 (hotspot: 10.42.0.1)
   │
  SSID: home-monitor / pw: frigatesetup
   │
  Wyze Cam v4 (10.42.0.x)
```

## Camera Credentials

- SSID: `home-monitor`
- Password: `frigatesetup`
- Machine IP on hotspot: `10.42.0.1`

## Status

- [x] Hotspot created via nmcli
- [ ] NAT/internet sharing enabled
- [ ] Wyze cam connected and set up via app
- [ ] Camera IP confirmed
- [ ] RTSP enabled on camera
- [ ] Frigate config updated with camera RTSP URL
