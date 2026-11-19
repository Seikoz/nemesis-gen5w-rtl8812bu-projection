# CN7NPE USB CarPlay session and network diagnostics

The v0.1.13 bundle contains Korea Projection **1.7.4.18**, signed wireless mod **2.4.9**, Realtek **1.1.13** and HMG-API core **1.1.0-rc.4**. The local mod numbering is independent of upstream Open-HMG releases. Vehicle CarPlay success remains unverified. These modifications are AGPL-3.0, like the original wireless mod.

## Session ordering and status

Base: [StopDragon/HMG-API b573ac624e284cd7d6e0a7b9fa6c32862c528988](https://github.com/StopDragon/HMG-API/tree/b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa). The build verifies the complete source archive hash.

[patch_hooks.py](patch_hooks.py) retains the USB AP readiness wait: both `sys.kp.aa_ap=1` and the AP address on `rtwlan0` must exist before Bluetooth iAP2 `BT_ATTACHED`. The existing background Handler checks once per second for at most 180 retries. A request token fences old/duplicate SPP events; Bluetooth loss, disabled mod or wired/active CarPlay cancels the wait.

[SessionStatus.java](SessionStatus.java) emits strict, non-identifying records on the real DiPO callbacks: `created`, wireless `started`, `wired` and `finalized`, plus bridge initialization and Bluetooth attach stages. The record contains a PID, `/proc/self/stat` start tick, AP generation, elapsed milliseconds, sequence, state and transport. It contains no credentials, phone identity or packet data. A property write failure leaves the exact record in logcat for the root collector.

A 15-second heartbeat refreshes only the state established by a real wireless session-start callback. Finalization or any newer callback cancels its chain. It retains the original AP generation, so an old session is never relabelled as a new AP session. A missing heartbeat for 60 seconds is unknown, not connected. This also limits stale state if property writes fail and finalization rotates out of logcat.

[usb-carplay-session.sh](../bundle/usb-carplay-session.sh) replaces the old local TCP-7000 counter. It verifies the current boot, AP generation, live PID/start tick, current AP signal and freshness before returning one connected wireless session. Other stages return zero **confirmed** wireless sessions with a separate state/source. A callback start is not an independent check of picture, audio or call quality. The AP service normally polls every 30 seconds; the property path is also read when status is refreshed.

## Network policy and diagnostics

[build_wireless_mod.py](../build_wireless_mod.py) verifies the original 2.4.6 mod and signs 2.4.9 with the existing author identity. Every signed file hash and the P-256 signature are verified. The private key is never published. Native patches and all existing fixed-port rules are preserved.

- Dynamic TCP: input/output, `rtwlan0` only, peers `192.168.43.0/24` or `fe80::/10`, either source or destination port 1024–65535 (v0.1.12).
- New UDP: IPv6 input/output, `rtwlan0` only, peers `fe80::/10`, either source or destination port 6031. Other UDP, external ranges and interfaces are not opened by these additions.
- [usb-mod-plan.sh](../bundle/usb-mod-plan.sh) applies only an owned wireless-mod plan; foreign, unknown, disabled or restoration changes require the existing review flow.

[usb-connection-diagnostics.sh](../bundle/usb-connection-diagnostics.sh) saves first/latest snapshots during AP, station or session transitions, with at most two further waiting samples per stable state. It reads IPv4/IPv6 filter rules in kernel order, counters, HMG-API jump positions, scoped UDP6031 rule counts, the generated network plan, socket states and interface/multicast information. It never changes firewall rules or resets counters. Presence and counters do not prove end-to-end connectivity.

[ap_link_diagnostics.c](ap_link_diagnostics.c) performs a read-only, 1.2-second IPv4/IPv6 mDNS probe bound to `rtwlan0`, requesting `_airplay._tcp.local` and `_carplay-ctrl._tcp.local`. It uses ephemeral sockets with legacy-unicast replies; it never occupies port 5353 or starts/replaces an mDNS daemon. It prints service types and SRV ports, never instance/host names or TXT content. Input sizes, compression traversal, packet counts, printed record counts and total receive time are bounded. No reply is inconclusive: multicast-only responses, firewall policy or timing can hide service discovery.

`3-log.txt` automatically includes `usb-carplay-events.log`, `usb-cp-capture.log`, `usb-connection-first.log` and `usb-connection-latest.log`, in addition to the existing driver/AP logs. Records from older boots are marked unavailable. Unplugging the dongle to insert a report USB does not erase the same-boot first/latest snapshots.

## Station counts

[ap_station_count.c](ap_station_count.c) uses read-only STA-FIRST/STA-NEXT queries with a one-second deadline. [usb-stations.sh](../bundle/usb-stations.sh) falls back to Realtek `all_sta_info`, requiring association state and a positive AID and excluding self, multicast, pending and duplicate entries. The fallback counts associated peers, not necessarily WPA-authorized peers. Failed queries are unknown rather than zero. Wi-Fi station counts are displayed separately from CarPlay session state.

## Build and verification

[compile_hooks.sh](compile_hooks.sh) runs the shell/policy regressions, [test_ap_wait.py](test_ap_wait.py) on the modified real Bridge methods and [test_session_status.py](test_session_status.py) on the actual record writer, then compiles Android API 19 DEX. The latter tests property-denied fallback, start ticks, heartbeat generation retention and finalization cancellation. [test_mdns.py](test_mdns.py) exercises the actual DNS decoder with compressed, truncated and cyclic packets and checks that private content is omitted. GitHub Actions builds the ARMv7 PIE helpers against API 19.

```sh
bash projection-source/compile_hooks.sh projection-output
python build_wireless_mod.py --base-mod wireless-2.4.6.zip --hooks projection-output/hooks.jar --key /private/path/existing-author.key --output wireless-2.4.9.zip
python build_usb_bundle.py rtl-v1.1.7.zip kp-v0.1.4.zip hmgapi-1.1.0-rc.4.zip --diagnostic-modules /path/to/modules --usb-reset-helper /path/to/usb-reset-a3000mini --wireless-mod wireless-2.4.9.zip --station-counter /path/to/ap-station-count --link-diagnostics /path/to/ap-link-diagnostics
python -m unittest discover -s tests -v
```

The USB builder verifies pinned source packages, signed mod identity/hashes, Android ELF architecture and new diagnostic payloads. Upgrade/reinstall guards accept the existing local 2.4.6–2.4.9 identity. The user installs the finished USB ZIP; no build tools are required on the vehicle.
