# NEMESIS RTL8812BU USB 드라이버

현대·기아 Android 기반 표준형 Gen5W 헤드유닛에서 Realtek RTL8812BU USB 무선랜 동글을 인식시키는 NEMESIS 패키지입니다.

## 설치 전 확인

- 차량에서 **NEMESIS Manager**가 열려야 합니다.
- 대상은 Telechips `tcc803x` / `tcc897x`와 커널 `3.18.24-tcc`입니다. 패키지가 설치 및 실행 시 플랫폼과 커널을 확인합니다.
- ipTIME A3000mini는 RTL8812BU를 사용합니다. 이 패키지에서 확인한 모듈의 USB ID에는 `0bda:b812`와 `0bda:b82c`가 포함됩니다.
- 2024 아반떼 N 페이스리프트 `CN7NPE.KOR.S5W_M.V039.001.260902`에서 v1.1.1은 모듈을 등록하고 ipTIME A3000mini의 USB ID `0bda:b812`를 읽었습니다. USB 인터페이스는 `unbound`로 남았습니다. v1.1.2의 실차 결과는 아직 확인 전입니다. [버전별 변경사항](CHANGELOG.md)

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

헤드유닛을 완전히 재부팅한 뒤에는 **Launch**를 다시 누릅니다. 이 패키지를 적용한 뒤 Wi-Fi 네트워크 연결이나 무선 CarPlay를 사용하려면 해당 기능을 별도로 구성합니다.

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

## 제거

**NEMESIS Manager → My Packages → Realtek RTL8812BU USB Driver → Uninstall**을 누릅니다. 모듈이 사용 중이라는 메시지가 나오면 동글을 빼고 다시 시도합니다.

## 개발용 패키지 재생성

배포 릴리스에는 USB 설치 ZIP 한 개를 첨부합니다. 패키지를 개발하거나 검증할 때는 Python 3.9 이상에서 `python build_package.py`를 실행합니다. 원본 릴리스 ZIP을 이미 받은 경우 파일 경로를 지정할 수 있습니다.

```sh
python build_package.py --upstream ./HKG_5W_USBWifi_Hotspot.zip
```

## 원본

커널 모듈은 GRT47 릴리스에서 가져옵니다. 빌더는 ARM ELF 형식, vermagic과 USB ID를 확인한 뒤 원본 모듈을 그대로 패키징합니다.

- [GPL-2.0 드라이버 대응 소스와 빌드 설정](driver-source/README.md)
- [GRT47 v2.0.7 릴리스](https://github.com/GRT47/HKG_5W_USB_Wlan/releases/tag/v2.0.7)
- [GRT47 커널 모듈 빌드 스크립트](https://github.com/GRT47/HKG_5W_USB_Wlan/tree/v2.0.7/package_usbwifi_hotspot/kernel_build)
- [Realtek 드라이버 소스 저장소](https://github.com/cilynx/rtl88x2bu)
- [NEMESIS 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
- [ipTIME A3000mini 제품 사양](https://iptime.co.kr/products/557?pd=1)
