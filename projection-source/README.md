# CN7NPE USB CarPlay AP readiness fix

The v0.1.11 bundle contains wireless mod **2.4.7**, Korea Projection **1.7.4.16**, and the same Realtek **1.1.13** runtime and HMG-API **1.1.0-rc.4** core as v0.1.10. This modification is licensed under AGPL-3.0, like the upstream wireless mod.

The vehicle report showed Bluetooth SPP/iAP2 starting at 17:15:30 while the USB AP was not ready. The AP and DHCP were ready at 17:16:49, but the recorded station count remained zero. The old USB-specific `ensureHotspot()` logged that it was waiting and returned immediately; `onSppUp()` then sent `BT_ATTACHED` anyway. This identifies an ordering defect, not proof that it is the only cause of the failed connection.

The patched bridge waits for both Korea Projection's `sys.kp.aa_ap=1` signal and the AP address on `rtwlan0` before sending `BT_ATTACHED`. It checks once per second, for up to 180 retries, on its existing background Handler. It cancels if Bluetooth disconnects, the mod is disabled, or wired/active CarPlay takes over. A request token prevents a queued callback from an earlier Bluetooth connection from starting or cancelling a new connection. Repeated SPP notifications do not send duplicate attach requests. Credentials and phone addresses are not added to the new logs.

## Source and build

- Base: [StopDragon/HMG-API commit b573ac624e284cd7d6e0a7b9fa6c32862c528988](https://github.com/StopDragon/HMG-API/tree/b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa).
- [compile_hooks.sh](compile_hooks.sh) verifies the source archive SHA-256, applies [patch_hooks.py](patch_hooks.py), tests the modified methods with [test_ap_wait.py](test_ap_wait.py), and builds Android API 19 DEX hooks using Java 17 and Android SDK tools.
- [Successful build and method tests](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44491762750), source commit `28b0063507d4bfc5aa05318828acf05f9d3a30b1`.
- `hooks.jar` SHA-256: `8e6f21a3929fca04c9e204a035f8fba556232145b7eacb101bbe3685bd773c6c`.
- [build_wireless_mod.py](../build_wireless_mod.py) verifies the original 2.4.6 mod, replaces only its hook payload and version metadata, and signs 2.4.7 with the existing local author key. It verifies the signature and every signed file hash. The private key is not published.
- [build_usb_bundle.py](../build_usb_bundle.py) verifies that signed update and updates the installer's required mod version and checksum. The old author's ownership check accepts 2.4.6 and 2.4.7 for upgrades and reinstalls.

Example build commands on the Android SDK CI host and the packaging host:

```sh
bash projection-source/compile_hooks.sh projection-output
python build_wireless_mod.py --base-mod wireless-2.4.6.zip --hooks projection-output/hooks.jar --key /private/path/existing-author.key --output wireless-2.4.7.zip
python build_usb_bundle.py rtl-v1.1.7.zip kp-v0.1.4.zip hmgapi-1.1.0-rc.4.zip --diagnostic-modules /path/to/modules --usb-reset-helper /path/to/usb-reset-a3000mini --wireless-mod wireless-2.4.7.zip
```

The build and simulated event-order tests do not establish successful CarPlay operation on the vehicle. After installation, reboot fully and check for `USB hotspot ready; starting Bluetooth iAP2`, followed by phone association and CarPlay session creation.
