# Gen5W RTL8812BU wireless projection source

USB bundle v0.1.41 ships Wireless Mode **2.4.29** for CN7PE and CN7NPE and **2.4.30** for CN7HEVPE. Both are based on Open-HMG Wireless Mode **2.2.0-rc.8**. The bundle includes HMG-API core **1.1.0-rc.8**. The local wireless mod versions identify upgrades signed by this project. The wireless mod and its changes are licensed under [AGPL-3.0](../bundle/licenses/HMG-API-AGPL-3.0.txt).

## USB access point and session state

- Korea Projection prepares the Realtek driver and starts the access point on `rtwlan0` after verifying USB high-speed operation. [The wireless bridge patch](patch_rc8.py) waits for the access point readiness signal and the interface address before starting Bluetooth iAP2.
- [SessionStatus.java](SessionStatus.java) records the DiPO start and end callbacks. [The shell status reader](../bundle/usb-carplay-session.sh) checks the current boot, AP generation, process identity and record age. The Wi-Fi station count is measured separately.
- [The CN7NPE audio carrier](cn7npe-carrier/UsbWifiCarrier.java) runs inside Wireless Mode. [Its recipe](cn7npe-carrier/recipes/usb-wifi-name.recipe) applies to the matching CarPlay library on supported CN7NPE firmware.
- Cluster and HUD turn-by-turn is off by default. The settings schema and runtime fallbacks use the same default. HMG-API honors an explicitly saved user choice.
- [Connection diagnostics](../bundle/usb-connection-diagnostics.sh) capture firewall rules, socket state and AP transitions. [The mDNS probe](ap_link_diagnostics.c) queries CarPlay service types on the AP interface and reports service types and ports. [The installation guide](../bundle/INSTALL-KO.md) lists the report files and export steps.

## Build and verification

Use Linux with Python 3, JDK 17 and an Android SDK with a platform and D8 build tools. Set `JAVA_HOME_17_X64` to the JDK path and `ANDROID_HOME` to the SDK path. Use an output path without spaces. [compile_rc8.sh](compile_rc8.sh) verifies the pinned upstream archives and runs the AP readiness, iAP2, HUD, session state and audio carrier tests before generating Android API 19 hooks.

```sh
bash projection-source/compile_rc8.sh projection-output
python3 -m unittest discover -s tests -v
```

To sign the wireless mods, obtain the [official 2.2.0-rc.8 mod ZIP](https://github.com/Open-HMG/HMG-API/releases/download/v1.1.0-rc.7/wireless-carplay-aa-2.2.0-rc.8.zip) and extract the signed prior mod `hmgapi/wireless-carplay-aa.zip` from `packages/korea.projection.zip` inside the [v0.1.17 installer](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/cn7npe-usb-bundle-v0.1.17). The signing script checks both inputs by SHA-256. Use the existing release author key to produce an upgrade that installed copies will accept.

```sh
python3 build_wireless_mod.py --base-mod wireless-carplay-aa-2.2.0-rc.8.zip \
  --previous-mod wireless-2.4.10.zip --hooks projection-output/hooks.jar \
  --key /path/to/author.key --output wireless-avante.zip
python3 build_wireless_mod.py --hybrid --previous-mod wireless-avante.zip \
  --hooks projection-output/hooks-hybrid.jar --key /path/to/author.key \
  --output wireless-hybrid.zip
python3 build_usb_bundle.py --help
```

[build_usb_bundle.py](../build_usb_bundle.py) packages the signed mods with the pinned Realtek and Korea Projection base ZIPs, the official HMG-API core package and the ARMv7 helpers. The prebuilt USB install ZIP is available from [GitHub Releases](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/latest).

## Compatibility and history

- The [CN7HEVPE test fixture](fixtures/cn7hevpe-kor-260902-wireless-points.txt) records the relevant hook names from the verified KOR 260902 map. The package test checks that the hybrid declarations fit this fixture and that the unmodified upstream declarations are refused.
- [Vehicle map compatibility review](../docs/compatibility-rc7-rc8-usb.md)
- [Version history and vehicle results](../CHANGELOG.md)
- [v0.1.14 session and handover source](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.14/projection-source)
- [v0.1.35 standalone audio test source](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.35/projection-source/cn7npe-carrier)
