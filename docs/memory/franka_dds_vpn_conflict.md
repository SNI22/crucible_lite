---
name: franka-dds-vpn-conflict
description: "Fast-DDS announces a locator on every UP interface, including VPNs (wt0 WireGuard, zt* ZeroTier) — persistent fix is a Fast-DDS XML profile whitelisting the wired NIC; bringing the VPN down is the zero-config fallback"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

**Symptom:** `arm_client`'s `wait_until_ready` times out with
`Missing messages on: franka_robot_state_broadcaster/current_pose, ...,
joint_states, ...` even though `fr3-launch` is confirmed running on
`franka-pc` AND `ros2 topic list` shows the `/fr3/...` topics.
Discovery works, data delivery doesn't. `ros2 topic echo` also hangs.

**Cause:** ROS 2 Humble's default Fast-DDS announces a participant
locator for every UP network interface. With a VPN up (wt0 WireGuard
100.75.x, or zt* ZeroTier 10.147.x), the laptop announces the VPN IP as
one of its locators alongside the wired-NIC IP (192.168.1.3). When
`franka-pc` tries to deliver topic data, it may pick the unreachable VPN
locator and the packet goes nowhere. Kernel routing is fine — SSH still
works — but DDS data delivery silently fails.

**Persistent fix (preferred — confirmed working with wt0 up):** Fast-DDS
XML profile that whitelists only the wired NIC. Already installed at
`~/.ros/fastdds_wired_only.xml`:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
        <transport_descriptor>
            <transport_id>wired_only_udp</transport_id>
            <type>UDPv4</type>
            <interfaceWhiteList>
                <address>192.168.1.3</address>
            </interfaceWhiteList>
        </transport_descriptor>
    </transport_descriptors>
    <participant profile_name="participant_profile" is_default_profile="true">
        <rtps>
            <userTransports><transport_id>wired_only_udp</transport_id></userTransports>
            <useBuiltinTransports>false</useBuiltinTransports>
        </rtps>
    </participant>
</profiles>
```

Activated via env var in `~/.bashrc`:
```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=$HOME/.ros/fastdds_wired_only.xml
```

Verification: with VPN up and the env var set, `ros2 topic echo
/fr3/franka/joint_states --once` returns a full message.

**Hardcoded IP caveat:** the whitelist locks in `192.168.1.3` as the
laptop's wired-NIC IP. If the NIC ever gets a different IP, DDS silently
fails. Set a static IP via NetworkManager so `192.168.1.3` is stable.
For sessions without the USB-Ethernet (lab WiFi only), wrap the export
in `~/.bashrc`:
```bash
if ip -4 addr show enx9405bb1e0375 2>/dev/null | grep -q "192.168.1"; then
    export FASTRTPS_DEFAULT_PROFILES_FILE=$HOME/.ros/fastdds_wired_only.xml
fi
```

**Zero-config fallback:** if the XML profile isn't loaded for some
reason and you just want to grind through one session, drop the VPN:
```bash
sudo ip link set wt0 down          # WireGuard
sudo ip link set zt5u4qjhyh down   # ZeroTier
```
(WiFi `wlp195s0` is usually fine to leave up.) Re-enable afterward.

**Related diagnostic — multicast discovery itself:** `franka-pc` has two
NICs (`eno1` 10.69.54.x lab; `enxc8a362c96899` 192.168.1.x USB-Eth).
Fast-DDS multicast announcements from franka-pc are typically reaching
the laptop even without explicit route configuration — but if
`ros2 topic list` returns empty (no `/fr3/*` topics at all), add a
multicast route on franka-pc as a temporary fix:
```bash
ssh -t franka-pc 'sudo ip route add 224.0.0.0/4 dev enxc8a362c96899'
```
(non-persistent across reboots; reversible via `ip route del`.)
