# NEMESIS RTL8812BU USB 드라이버

현대·기아 Android 기반 표준형 Gen5W 헤드유닛에서 Realtek RTL8812BU USB 무선랜을 인식시키는 NEMESIS 패키지입니다. ipTIME A3000mini는 RTL8812BU를 사용합니다.

- 대상 플랫폼은 Telechips `tcc803x` 및 `tcc897x`, 커널은 `3.18.24-tcc`입니다.
- 실차 시험 대상은 2024 아반떼 N 페이스리프트, `CN7NPE.KOR.S5W_M.V039.001.260902`, ipTIME A3000mini입니다. NEMESIS가 설치된 상태에서 드라이버 인식 확인을 앞두고 있습니다.
- 드라이버는 **Launch**를 눌렀을 때 수동으로 로드됩니다. 완전히 재부팅한 뒤 다시 실행하세요. Wi-Fi 연결 설정 및 무선 CarPlay 활성화는 별도로 진행합니다.

## 빌드

Python 3.9 이상에서 실행합니다. 외부 Python 패키지는 필요 없습니다.

```sh
python build_package.py
```

빌드 결과는 `dist/NEMESIS-RTL8812BU-Gen5W-USB.zip`에 저장됩니다. 빌더는 GRT47의 v2.0.7 릴리스에서 원본 ZIP을 내려받아 SHA-256을 확인한 뒤, 플랫폼별 모듈 두 개를 추출합니다. 내려받은 원본 ZIP이 있으면 오프라인으로 빌드할 수 있습니다.

```sh
python build_package.py --upstream ./HKG_5W_USBWifi_Hotspot.zip
```

## USB로 설치하고 확인하기

1. 생성된 ZIP을 FAT32 USB 메모리의 최상위에 풉니다. `NEMESIS.data`와 `packages/realtek.88x2bu.zip`이 있어야 합니다.
2. NEMESIS가 설치된 헤드유닛에 메모리를 꽂고 설치 팝업에서 승인합니다.
3. 메모리를 빼고 무선랜 동글을 꽂습니다. **NEMESIS Manager → My Packages → Realtek RTL8812BU USB Driver → Launch**를 누릅니다.
4. `RTL8812BU ready: rtwlan0` 메시지가 표시되면 동글이 Wi-Fi 인터페이스로 등록된 것입니다. USB ID도 함께 표시됩니다.

제거하려면 같은 패키지 화면에서 **Uninstall**을 누릅니다. 이 패키지가 해당 부팅에서 직접 로드한 모듈만 언로드합니다. `usbwifi.hotspot`과는 같은 모듈을 사용하므로 함께 설치할 수 없습니다.

## 원본

모듈은 GRT47 릴리스에서 가져오며, Git 저장소에는 NEMESIS 설치 스크립트와 빌더를 담았습니다. 빌더는 원본 배포 파일의 ELF 형식, vermagic, USB ID를 검사한 뒤 모듈을 그대로 패키징합니다.

- [GRT47 v2.0.7 릴리스](https://github.com/GRT47/HKG_5W_USB_Wlan/releases/tag/v2.0.7)
- [GRT47 커널 모듈 빌드 스크립트](https://github.com/GRT47/HKG_5W_USB_Wlan/tree/v2.0.7/package_usbwifi_hotspot/kernel_build)
- [Realtek 드라이버 소스 저장소](https://github.com/cilynx/rtl88x2bu)
- [NEMESIS 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
- [ipTIME A3000mini 제품 사양](https://iptime.co.kr/products/557?pd=1)
