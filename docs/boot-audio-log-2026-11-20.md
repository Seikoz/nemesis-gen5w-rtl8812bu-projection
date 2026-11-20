# 2026-11-20: boot readiness and audio apply analysis

Vehicle: CN7NPE KOR 260902, A3000mini. Report: Korea Projection 1.7.4.23 / bundle v0.1.18. The owner removed the dongle at 17:53 and reinserted it around 17:53:10. Phone identities and the original private report are not published here.

| Observation | Evidence | Meaning |
| --- | --- | --- |
| Initial enumeration | OHCI `3-1`, speed 12 | Boot starts at full-speed. |
| Automatic EHCI transition | Kernel uptime 21.66/21.81: EHCI `4-1`, high-speed, 0bda:b812; `speed.log`: `Verified usb=4-1 speed_after=480` | This occurred before manual removal. The second external-host restart stage was not needed in this boot. |
| 17:51:48 | Realtek Launch says USB Wi-Fi not ready at 480Mbps | This readiness check covers interface and driver readiness as well as speed; it is not an independent measurement of USB speed. |
| 17:51:50 | Permission/setup waiting and wireless-mod waiting begin | In the shipped main function these steps occur after `usb_wifi_ready`: rtwlan0, Realtek proc entry, actual 480Mbps and USB driver binding passed. The service then waits for HMG-API setup. |
| Manual operation | USB disconnect at uptime 94.14, high-speed reconnection at 104.84 | The interval matches the owner's 17:53 / 17:53:10 account. It must not be attributed to an automatic disconnect. |
| 17:53:31–17:54:03 | Verified local map reused, wireless-mod readiness passes, hostapd/DHCP become ready | Manual replug happened during HMG-API setup waiting. This test cannot prove that replug was necessary for AP startup. |
| 17:54:43 | Actual CarPlay start, confirmed Bluetooth origin, raw transport 0 | A wireless session started, consistent with the owner's visible CarPlay connection. |
| After 17:54:45 | Component 5 connects, but native iAP2 sends repeatedly return 19 and identification retries fail | A component callback is not proof of completed iAP2 identification or working audio. The return value is not assigned an undocumented errno meaning. |

## Confirmed software defects and correction

The saved plan includes new `libcarplayidentity.so` and `libcarplaylog.so` files plus an updated `libleafiaaac.so`. The v0.1.18 automatic plan filter refuses rc.7's owned event notifications, `home Wi-Fi  off` and informational `network  no cellular` lines. This is a reproducible filter defect. The report has no corresponding successful `mod-apply.txt`; the saved plan alone cannot establish whether an owner subsequently applied changes elsewhere.

v0.1.19 accepts those specific rc.7 informational formats while continuing to reject foreign changes, errors, restores and unknown formats. It rechecks an already installed 2.4.11 too. Before AP startup, pending audio support changes trigger a scoped apply only when the owned, unpinned mod's complete installed files match the bundle and all planned changes belong to that mod. The engine applies that owned plan, including its other pending patches/settings; unrelated plans are refused. The plan is read again after network setup. Success requires a reboot before AP startup; failures or interrupted attempts are not retried within the same boot. Other plans require manual review.

The report also contains bare `printf: not found` failures in session aggregation. v0.1.19 uses the packaged BusyBox printf applet for those calls. This corrects a status collection failure, not an audio codec by itself. The separate Realtek `awk: not found` diagnostic limitation remains outside this Korea Projection-only update; the actual 480Mbps verification is still present.

## What remains unproven

- Whether the dongle reaches AP readiness without any manual operation after applying the support files and rebooting. This report's manual replug preempts that observation.
- Whether applying the pending files resolves the owner's Melon playback on the phone. Audio format patches were logged as applied, but detailed audio setup/focus logs at the connection time are not retained.
- The precise native meaning of return value 19 and whether iAP2 failure is the cause of phone-side media playback or a separate symptom.

Test the v0.1.19 apply/reboot flow first. For any remaining audio failure, record the connection and Melon playback interval with HMG-API Record a problem and collect the Korea Projection report in the same boot.
