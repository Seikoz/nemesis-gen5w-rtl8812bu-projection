# NEMESIS RTL8812BU USB 드라이버

현대·기아 Android 기반 표준형 Gen5W 헤드유닛에서 Realtek RTL8812BU USB 무선랜 동글을 인식시키는 NEMESIS 패키지입니다.

## 설치 전 확인

- 차량에서 **NEMESIS Manager**가 열려야 합니다.
- 대상은 Telechips `tcc803x` / `tcc897x`와 커널 `3.18.24-tcc`입니다. 패키지가 설치 및 실행 시 플랫폼과 커널을 확인합니다.
- ipTIME A3000mini는 RTL8812BU를 사용합니다. 이 패키지에서 확인한 모듈의 USB ID에는 `0bda:b812`와 `0bda:b82c`가 포함됩니다.
- 2024 아반떼 N 페이스리프트 `CN7NPE.KOR.S5W_M.V039.001.260902`와 ipTIME A3000mini 조합은 실차 시험 대상입니다. 패키지 빌드와 설치 스크립트는 PC에서 검증했으며, 실차에서의 드라이버 로드 결과는 아직 확인 전입니다.

이미 **USB WiFi Hotspot Enabler**(`usbwifi.hotspot`)를 사용 중이면 같은 모듈을 공유하므로 두 패키지 중 하나를 선택하세요.

## 설치 방법

### 1. PC에서 설치 ZIP 만들기

GitHub의 **Code → Download ZIP**으로 저장소를 내려받고, PC에서 압축을 풉니다. Python 3.9 이상이 설치된 PC에서 `build_package.py`가 보이는 폴더를 열고 다음 명령을 실행합니다.

```sh
python build_package.py
```

Windows에서 `python` 명령으로 실행되지 않으면 `py -3 build_package.py`를 사용하세요. 빌드는 원본 릴리스 ZIP을 내려받아 SHA-256을 검증하고, 플랫폼별 모듈을 추출해 `dist/NEMESIS-RTL8812BU-Gen5W-USB.zip`을 생성합니다.

### 2. 설치 USB 준비하기

생성된 **`NEMESIS-RTL8812BU-Gen5W-USB.zip`**을 FAT32 USB 메모리의 최상위에 풉니다. 아래와 같이 `NEMESIS.data`가 첫 화면에 보여야 합니다.

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

헤드유닛을 완전히 재부팅한 뒤에는 **Launch**를 다시 누릅니다. 이 패키지를 적용한 뒤 Wi-Fi 네트워크 연결이나 무선 CarPlay를 사용하려면 해당 기능을 별도로 구성합니다.

## 문제 해결

| 표시되는 증상 | 확인할 항목 |
| --- | --- |
| 설치 팝업이 뜨지 않음 | NEMESIS Manager가 열리는지, USB의 포맷과 파일 구조가 위와 같은지 확인합니다. |
| `Unsupported Gen5W platform` 또는 `Unsupported kernel` | 화면에 표시된 플랫폼 또는 커널 값을 확인합니다. 이 경우 드라이버를 로드하지 않습니다. |
| `Plug in an RTL8812BU dongle with a supported USB ID` | 동글을 데이터 USB 포트에 직접 꽂고 다시 Launch합니다. 계속 표시되면 Windows 장치 관리자의 **속성 → 자세히 → 하드웨어 ID**에서 `VID_`와 `PID_`를 확인합니다. |
| `88x2bu failed to load` 또는 `no USB Wi-Fi interface appeared` | Launch에 나온 메시지 전체와 내비 SW 버전, 동글의 USB ID를 기록합니다. 첫 메시지는 모듈 로드 실패, 두 번째는 모듈 로드 후 인터페이스 등록 실패입니다. |

## 제거

**NEMESIS Manager → My Packages → Realtek RTL8812BU USB Driver → Uninstall**을 누릅니다. 모듈이 사용 중이라는 메시지가 나오면 동글을 빼고 다시 시도합니다.

## 오프라인 빌드

[GRT47 v2.0.7 릴리스](https://github.com/GRT47/HKG_5W_USB_Wlan/releases/tag/v2.0.7)의 `HKG_5W_USBWifi_Hotspot.zip`이 PC에 있으면 그 파일을 지정해 인터넷 연결 없이 빌드할 수 있습니다.

```sh
python build_package.py --upstream ./HKG_5W_USBWifi_Hotspot.zip
```

## 원본

커널 모듈은 GRT47 릴리스에서 가져옵니다. 빌더는 ARM ELF 형식, vermagic과 USB ID를 확인한 뒤 원본 모듈을 그대로 패키징합니다.

- [GRT47 v2.0.7 릴리스](https://github.com/GRT47/HKG_5W_USB_Wlan/releases/tag/v2.0.7)
- [GRT47 커널 모듈 빌드 스크립트](https://github.com/GRT47/HKG_5W_USB_Wlan/tree/v2.0.7/package_usbwifi_hotspot/kernel_build)
- [Realtek 드라이버 소스 저장소](https://github.com/cilynx/rtl88x2bu)
- [NEMESIS 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
- [ipTIME A3000mini 제품 사양](https://iptime.co.kr/products/557?pd=1)
