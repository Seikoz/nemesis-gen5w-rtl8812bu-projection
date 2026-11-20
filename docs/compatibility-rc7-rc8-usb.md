# HMG-API rc.7 / Wireless rc.8 RTL8812BU compatibility

Target: CN7NPE KOR 260902, A3000mini 0bda:b812, Realtek 1.1.16 and rtwlan0. This is an off-car source/build/fixture review, not a successful CarPlay vehicle test.

## Resulting package

The official HMG-API 1.1.0-rc.7 NEMESIS package is unchanged. The wireless payload is rebased on official **2.2.0-rc.8**, with local upgrade version **2.4.11** and the existing local author key. The upstream and previous local author UUIDs differ; installing the original upstream ZIP over the existing local mod would fail author/version checks. No private key is shipped.

| Area | Review and integration |
| --- | --- |
| Runtime | Core rc.7 satisfies upstream rc.8's rc.6 minimum; the USB mod requires rc.7. The official SDK builds the hooks for Android API 19. |
| USB AP | Replace framework hotspot startup with Korea Projection's ready signal, non-off AP generation, UP rtwlan0 and 192.168.43.1. Wait up to 180 seconds before Bluetooth iAP2; cancellation checks Bluetooth, ownership, disable and parking. |
| HMG-API Wi-Fi | Remove the built-in hotspot request and SDIO feature requirement from this target's mod metadata. Korea Projection retains ownership of USB hostapd. |
| Car identity | Restrict system/patch-set metadata to CN7NPE KOR 260902; use an explicit USB patch set with stock-independent props/additions and the existing hotspot featurexml change. No US CN7NPE or Korean CN7PE map is substituted. |
| Hooks | The vehicle report checked all 351 rc.4-era points. Original rc.8 declares 49 hooks; 8 are newer than that map and would refuse the whole mod. The target declares the compatible 41 and omits the newer hook consumers. Real HookPlan verifies this distinction. |
| Session | Preserve confirmed transport-0 recognition, SPP-to-CarPlay-channel handover, AP/session identity guards and actual-session status records. Keep upstream rc.8's per-link sender, blocked-send handling and bounded re-attach logic. |
| Network | Keep the prior USB subnet/link-local TCP/UDP policy including IPv6 UDP 6031; add upstream's AA TCP 40515 rule scoped to rtwlan0. Reuse Korea Projection's existing settings-preserving `usb_network allow` helper on upgrades too. |
| AA integration | Retain the previous Korean build's AP-state hooks and bounded ready-status resend alongside the new upstream code. Actual Android Auto operation is not established by these tests. |
| Driver | Entire Realtek 1.1.16 ZIP, kernel modules, EHCI recovery and native diagnostics stay byte-identical to v0.1.17. A new wireless mod does not establish USB 480Mbps recovery. |

## Map-dependent limitations

The following declarations are deliberately omitted for the checked 351-point target map:

- `framework.pp_service.connect_pp`
- `framework.pp_service.send_connect_pp_from_bt`
- `framework.pp_service.disconnect_pp`
- `framework.pp_service.cancel_connection_pp`
- `framework.pp_service.on_wireless_connected`
- `framework.pp_service.on_wireless_disconnected`
- `framework.activity.start_activity_for_result`
- `gpm.receiver_service.on_create`

Consequently this target build does not register the new PPService multi-phone manager, US/Canada popup hook or AA parking consumer. The CarPlay parking consumer is separately guarded by actual map availability of `dipo.carplay.disconnect` and `dipo.carplay.restart_bonjour`, which are also absent from the old 351-point catalogue. It logs that it is unavailable rather than guessing methods. If those points become mapped on the car, the port's parking/wake path uses the same confirmed wireless origin and waits for the USB AP before advertising again. Synthetic tests cover that path; they do not establish that the current vehicle map enables it. The framework hotspot-return broadcast is not proof that a USB hostapd has returned.

The replacement uses upstream's current turn-by-turn implementation. Previous Korean fork-only options such as `tbt_fit` and the star-key popup skip are not ported by this rebase. Existing stored settings remain, but those old options are not the same features in the new mod. New Car Reports can establish which optional features can be enabled in a later target build.

## Validation

- Actual patched Bridge methods: AP wait/cancellation, transport-0/SPP-loss replay, iAP2 data flow, stale work, finalization and re-attach isolation.
- Actual UsbAp and ParkCp decisions: signal/generation/address/UP, park/wake, AP delay, timeout and a second parking event while wake work waits.
- Upstream sender/re-attach/route-guidance/choice tests; upstream patch-engine fixtures. Native recipe tests require private stock libraries and are skipped when those libraries are absent.
- Real rc.7 engine on the final rebased USB metadata: no-SDIO CN7NPE KOR plan/apply/reapply, native support files, actual rtwlan0 rules and byte-identical restore.
- Official/core payload hashes, signed mod author/files, update guards, nested ZIP shell syntax, unchanged driver payload and reproducible final ZIP.

## Pinned sources

- [HMG-API rc.7](https://github.com/Open-HMG/HMG-API/tree/5732e261f544ef780bc0e4a5f7400ccc1b98edaa)
- [Official wireless rc.8](https://github.com/Open-HMG/hmgapi-wireless-cp-aa/tree/c47c0bbf8513e725c9852acb932bdde39e3d7edc)
- [Previous Korean AA integration](https://github.com/StopDragon/HMG-API/tree/b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa)
- [USB rebase](../projection-source/patch_rc8.py), [signed package builder](../build_wireless_mod.py), [build and checks](../projection-source/compile_rc8.sh)
