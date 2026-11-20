# CN7NPE USB CarPlay session and network diagnostics

The v0.1.14 bundle contains Korea Projection **1.7.4.19**, signed wireless mod **2.4.10**, Realtek **1.1.13** and HMG-API core **1.1.0-rc.4**. The local mod numbering is independent of upstream Open-HMG releases. Vehicle CarPlay success remains unverified. These modifications are AGPL-3.0, like the original wireless mod.

## Current v0.1.18: official rc.8 USB rebase

[compile_rc8.sh](compile_rc8.sh) pins official wireless c47c0bb and core rc.7 5732e26 plus the official rc.7 SDK. [patch_rc8.py](patch_rc8.py) ports USB AP readiness, origin/status and handover fences to the upstream bridge while retaining its per-link CpTx sender and re-attach logic. The signed local version is **2.4.11**, based on official **2.2.0-rc.8**; its numbering and author key are local upgrade identities.

The checked target map has 351 older points. Eight newer required declarations/consumers are omitted so the whole mod can load. CP parking also needs two map points absent from that older catalogue. [Compatibility review and limitations](../docs/compatibility-rc7-rc8-usb.md) explains the feature subset, native-testing limits and previous fork-only options not ported. Earlier implementation notes below describe v0.1.14 and remain for history.

## Session ordering and status

Base: [StopDragon/HMG-API b573ac624e284cd7d6e0a7b9fa6c32862c528988](https://github.com/StopDragon/HMG-API/tree/b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa). The build verifies the complete source archive hash.

[patch_hooks.py](patch_hooks.py) retains the USB AP readiness wait: both `sys.kp.aa_ap=1` and the AP address on `rtwlan0` must exist before Bluetooth iAP2 `BT_ATTACHED`. The existing background Handler checks once per second for at most 180 retries. A request token fences old/duplicate SPP events; Bluetooth loss, disabled mod or wired/active CarPlay cancels the wait.

[SessionStatus.java](SessionStatus.java) emits strict, non-identifying records on the real DiPO callbacks: `created`, wireless `started`, `wired` and `finalized`, plus bridge initialization and Bluetooth attach stages. The record contains a PID, `/proc/self/stat` start tick, AP generation, elapsed milliseconds, sequence, state and transport. It contains no credentials, phone identity or packet data. A property write failure leaves the exact record in logcat for the root collector.

A 15-second heartbeat refreshes only the state established by a real wireless session-start callback. Finalization or any newer callback cancels its chain. It retains the original AP generation, so an old session is never relabelled as a new AP session. A missing heartbeat for 60 seconds is unknown, not connected. This also limits stale state if property writes fail and finalization rotates out of logcat.

[usb-carplay-session.sh](../bundle/usb-carplay-session.sh) replaces the old local TCP-7000 counter. It verifies the current boot, AP generation, live PID/start tick, current AP signal and freshness before returning one connected wireless session. Other stages return zero **confirmed** wireless sessions with a separate state/source. A callback start is not an independent check of picture, audio or call quality. The AP service normally polls every 30 seconds; the property path is also read when status is refreshed.

## Network policy and diagnostics

[build_wireless_mod.py](../build_wireless_mod.py) verifies the original 2.4.6 mod and signs 2.4.10 with the existing author identity. Every signed file hash and the P-256 signature are verified. The private key is never published. Native patches and all existing fixed-port rules are preserved.

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
bash projection-source/compile_rc8.sh projection-output
python build_wireless_mod.py --base-mod wireless-carplay-aa-2.2.0-rc.8.zip --previous-mod wireless-2.4.10.zip --hooks projection-output/hooks.jar --key /private/path/existing-author.key --output wireless-2.4.11.zip
python build_usb_bundle.py rtl-v1.1.7.zip kp-v0.1.4.zip hmgapi-1.1.0-rc.7-nemesis-package.zip --diagnostic-modules /path/to/modules --usb-reset-helper /path/to/usb-reset-a3000mini --wireless-mod wireless-2.4.11.zip --station-counter /path/to/ap-station-count --link-diagnostics /path/to/ap-link-diagnostics
python -m unittest discover -s tests -v
```

The USB builder verifies pinned source packages, signed mod identity/hashes, Android ELF architecture and new diagnostic payloads. Upgrade/reinstall guards accept the existing local 2.4.6–2.4.11 identity. The user installs the finished USB ZIP; no build tools are required on the vehicle.

## v0.1.14: confirmed Bluetooth origin and CarPlay-channel handover

The vehicle log from KP 1.7.4.17 / mod 2.4.8 repeatedly reported native session start `transport=0 wireless=false`, then SPP loss, bridge `BT_DETACHED`, component 4 disconnect and finalization about 1–2 seconds later. The `transport == 1` condition was also present in 2.4.9. This evidence identifies a bridge cleanup path; it does not establish why the phone/vehicle originally closed SPP or guarantee that all disconnects are solved.

[patch_handover.py](patch_handover.py) recognizes transport 0 only when there is no actual USB iAP2 connection, the bridge's active Bluetooth request is confirmed by component 4 with the same serial, and the same USB AP generation is ready. Transport 0 is not assigned a universal meaning. Legacy transport 1 behavior is retained; an unknown non-USB origin is `unclassified`, not automatically wired.

After a confirmed wireless start, SPP loss preserves native CarPlay and requests the existing component 5 iAP2 channel. Existing DiPO disconnect filtering keeps the server's component 4 -> 5 switch from finalizing the native session. Duplicate SPP events do not duplicate the request. A queued attach checks the live session token, native owner, address, AP generation, enabled state and actual USB state before dispatch. A send failure clears the pending-client flag, with at most two attempts per native session. No infinite reconnect watchdog or Bluetooth keepalive patch is added.

New-session/USB fences prevent an old queued detach from closing the replacement session. Queued native iAP2 output is also checked against the session token and AP before execution; already executing native calls cannot be cancelled. Incoming packets from an obsolete native owner are ignored. Finalization clears flags and buffered data. Component 5 `connected` is logged as a server callback, not proof that identification, picture or audio works.

The raw transport value is retained in both callback and heartbeat records; a recognized `started,0` is displayed as connected only after the existing boot/PID/AP/freshness checks. Session-status heartbeats resolve the Bridge scheduler before taking the status lock to avoid the reverse lock order with synchronized lifecycle callbacks.

[test_handover.py](test_handover.py) extracts the actual patched Bridge methods and replays the vehicle sequence. It checks component 5 attachment and incoming/outgoing iAP2 delivery, duplicates, ordinary SPP loss, unconfirmed/wired/disabled/changed-AP cases, finalization, old queued jobs, data buffering and bounded send failures. Tests use synthetic identifiers; the private vehicle report is not included in the repository or ZIP.

[Android build and all method tests](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44665053112), source commit `a353c84afb1f8e8b0aa49400938ae68411c32fbe`. hooks.jar SHA-256: `917092cff18ddafbd55a07a7ae5cca2ab0e988a15d86be1d25e3d15bdab55b8e`. Existing ARMv7 mDNS and station helpers, firewall policy, HMG-API core and Realtek package are reused unchanged.
