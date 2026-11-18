# NEMESIS RTL8812BU USB 드라이버

현대·기아 Android 기반 표준형 Gen5W 헤드유닛에서 Realtek RTL8812BU USB 무선랜 동글을 인식시키는 NEMESIS 패키지입니다.

## 설치 전 확인

- 차량에서 **NEMESIS Manager**가 열려야 합니다.
- 대상은 Telechips `tcc803x` / `tcc897x`와 커널 `3.18.24-tcc`입니다. 패키지가 설치 및 실행 시 플랫폼과 커널을 확인합니다.
- ipTIME A3000mini는 RTL8812BU를 사용합니다. 이 패키지에서 확인한 모듈의 USB ID에는 `0bda:b812`와 `0bda:b82c`가 포함됩니다.
- 2024 아반떼 N 페이스리프트 `CN7NPE.KOR.S5W_M.V039.001.260902`의 v1.1.2 실차 로그에서 ipTIME A3000mini(`0bda:b812`)가 `rtl88x2bu`에 자동 연결됐고 `rtwlan0`이 생성됐습니다. 이 시험에서 `manual_bind=not attempted`는 자동 연결이 끝나 수동 재시도가 필요 없었다는 뜻입니다. [버전별 변경사항](CHANGELOG.md)

이미 **USB WiFi Hotspot Enabler**(`usbwifi.hotspot`)를 사용 중이면 같은 모듈을 공유하므로 두 패키지 중 하나를 선택하세요.

## 설치 방법

### 1. 설치 ZIP 다운로드

최신 배포 릴리스의 **Assets**에서 `NEMESIS-RTL8812BU-Gen5W-USB-v*.zip`을 내려받습니다. 이 파일을 바로 USB에 풀어 설치할 수 있습니다. [최신 배포 릴리스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/latest)

### 2. 설치 USB 준비하기

내려받은 설치 ZIP을 FAT32 USB 메모리의 최상위에 풉니다. 아래와 같이 `NEMESIS.data`가 첫 화면에 보여야 합니다.

```text
USB/
├── NEMESIS.data
└── packages/
    └── realtek.88x2bu.zip
```

`packages/realtek.88x2bu.zip`은 압축 상태로 둡니다. Windows에서 파일 확장자를 표시해 `NEMESIS.data` 이름이 정확한지 확인하세요.

### 3. 차량에 설치하고 동글 인식 확인하기

1. 주차 상태에서 내비게이션이 완전히 켜지면 설치 USB를 차량의 데이터 USB 포트에 꽂습니다.
2. NEMESIS 설치 팝업에서 승인하고 설치 완료를 기다립니다.
3. USB 메모리를 빼고 같은 포트에 RTL8812BU 동글을 꽂습니다.
4. **NEMESIS Manager → My Packages → Realtek RTL8812BU USB Driver → Launch**를 누릅니다.
5. `RTL8812BU ready: rtwlan0 (0bda:b812)`처럼 표시되면 동글이 Wi-Fi 인터페이스로 등록된 것입니다. 인터페이스 번호와 USB ID는 장치에 따라 달라질 수 있습니다.

### 아반떼 N 260902에서 부팅 인식 테스트

1. 테스트 릴리스의 USB ZIP을 위와 같은 방법으로 풀고 **Realtek RTL8812BU USB Driver v1.1.7** 업데이트를 승인합니다. 기존 Korea Projection USB 테스트판 `1.7.4.5`와 번들 HMG-API를 그대로 사용합니다. [v1.1.7 테스트 릴리스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/v1.1.7)
2. 설치 USB를 빼고 A3000mini를 꽂은 채 내비게이션을 완전히 재부팅합니다.
3. 약 2분 동안 동글을 장착한 상태로 두고 **Realtek Launch**를 누르지 않습니다. Korea Projection에서 `rtwlan0` 대기 문구가 사라지는지 확인합니다.

이 테스트판은 NEMESIS 서비스가 시작될 때 모듈을 로드하고 Android 부팅 완료 후에도 재시도합니다. 모듈이 올라갔는데도 A3000mini가 USB 드라이버에 연결되지 않으면, 장치 식별과 상태를 확인한 뒤 그 동글에만 USB 리셋을 부팅당 한 번 요청합니다.

### Korea Projection 호환성

Korea Projection 1.7.x는 내장 Wi-Fi를 확인한 뒤 무선 모드를 설치합니다. USB 동글이 `rtwlan0`으로 등록된 차에서도 1.7.x는 Wi-Fi 부품 없음으로 표시할 수 있습니다. v1.1.3부터는 이 조합에서 **Launch** 결과와 `launch.log`에 USB 드라이버 인식 여부와 Korea Projection 지원 상태를 구분해 표시합니다. 무선 CarPlay·Android Auto에는 Korea Projection의 USB 지원과 해당 차량 검증이 필요합니다. [Korea Projection의 USB 동글 지원 계획](https://github.com/StopDragon/korea-projection#usb-wi-fi-동글-180-준비-중)

1.7.4를 USB로 이식하려면 핫스팟 스크립트의 인터페이스 선택, 내장 Wi-Fi를 확인하는 설치 조건, 번들 HMG-API 무선 모드의 `wlan0` 검사까지 함께 수정해야 합니다. 그 뒤 차량에서 USB 동글의 AP 시작, iPhone 연결 및 CarPlay 세션을 검증해야 합니다. [Korea Projection 핫스팟 소스](https://github.com/StopDragon/korea-projection/blob/v1.7.4/nemesis-pkg/korea.projection/svc/hotspot.sh) · [HMG-API 무선 모드 소스](https://github.com/StopDragon/HMG-API/blob/korea-build/mods/wireless-carplay-aa/src/hmgapi/mods/wireless/Wireless.java)

이전 버전이 설치되어 있으면 같은 방법으로 새 USB를 넣고 업데이트를 승인합니다. **My Packages**에서 배포 버전을 확인한 뒤 **Launch**를 누릅니다.

## 문제 해결

| 표시되는 증상 | 확인할 항목 |
| --- | --- |
| 설치 팝업이 뜨지 않음 | NEMESIS Manager가 열리는지, USB의 포맷과 파일 구조가 위와 같은지 확인합니다. |
| `Unsupported Gen5W platform` 또는 `Unsupported kernel` | 화면에 표시된 플랫폼 또는 커널 값을 확인합니다. 이 경우 드라이버를 로드하지 않습니다. |
| `Plug in a supported dongle and press Launch again` | 모듈이 메모리에 올라갔습니다. 동글을 데이터 USB 포트에 직접 꽂고 다시 Launch합니다. 계속 표시되면 Windows 장치 관리자의 **속성 → 자세히 → 하드웨어 ID**에서 `VID_`와 `PID_`를 확인합니다. |
| `88x2bu failed to load` | 모듈을 로드하는 단계에서 실패했습니다. 아래 방법으로 로그를 복사합니다. |
| `88x2bu loaded, no Wi-Fi interface` | 모듈을 올린 상태에서 동글을 뺐다가 다시 꽂아 한 번 더 Launch합니다. 같은 메시지가 뜨면 아래 방법으로 로그를 복사합니다. `manual_bind` 항목에서 연결 재시도 결과를 볼 수 있습니다. |

Launch를 실행한 뒤 동글 대신 USB 메모리를 꽂고 **NEMESIS Manager → Logs → Copy to USB**를 누릅니다. USB에 생성된 `NEMESIS-logs/realtek.88x2bu/launch.log`에 플랫폼, USB 드라이버 연결 상태, 네트워크 인터페이스와 실패 관련 커널 메시지가 기록됩니다.

동글을 꽂고 부팅할 때만 실패하면 같은 방법으로 `NEMESIS-logs/realtek.88x2bu/boot.log`와 `preload.log`를 복사합니다. 복구를 실행한 시도에는 `usb_device_reset` 및 `boot_reconfigure` 결과가 기록됩니다.

## 제거

**NEMESIS Manager → My Packages → Realtek RTL8812BU USB Driver → Uninstall**을 누릅니다. 모듈이 사용 중이라는 메시지가 나오면 동글을 빼고 다시 시도합니다.

## 개발용 패키지 재생성

배포 릴리스에는 USB 설치 ZIP 한 개를 첨부합니다. 개발용 패키지를 재생성하려면 Android API 19 ARMv7용 USB 리셋 도구를 빌드하고 Python 3.9 이상에서 패키징합니다. 원본 모듈 ZIP을 이미 받은 경우 `--upstream`으로 경로를 지정할 수 있습니다. [USB 리셋 도구의 Android NDK 빌드 설정](.github/workflows/build-a3000mini-reset.yml)

```sh
python build_package.py --usb-reset-helper ./out/usb-reset-a3000mini
```

## 원본

커널 모듈은 GRT47 릴리스에서 가져옵니다. 빌더는 ARM ELF 형식, vermagic과 USB ID를 확인한 뒤 원본 모듈을 그대로 패키징합니다.

- [GPL-2.0 드라이버 대응 소스와 빌드 설정](driver-source/README.md)
- [GRT47 v2.0.7 릴리스](https://github.com/GRT47/HKG_5W_USB_Wlan/releases/tag/v2.0.7)
- [GRT47 커널 모듈 빌드 스크립트](https://github.com/GRT47/HKG_5W_USB_Wlan/tree/v2.0.7/package_usbwifi_hotspot/kernel_build)
- [Realtek 드라이버 소스 저장소](https://github.com/cilynx/rtl88x2bu)
- [NEMESIS 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
- [ipTIME A3000mini 제품 사양](https://iptime.co.kr/products/557?pd=1)
