# 아반떼 N 260902 USB 합본 설치

대상은 2024년식 아반떼 N 페이스리프트 CN7NPE KOR `V039.001.260902`, TCC803x, ipTIME A3000mini(`0bda:b812`)입니다. NEMESIS Manager **1.16.7 이상**의 USB Package Store를 사용합니다.

- Korea Projection CN7NPE USB Test **1.7.4.16** 및 무선 모드 **2.4.7**
- Realtek RTL8812BU USB Driver **1.1.13**
- HMG-API 본체 **1.1.0-rc.4**, NEMESIS 패키지 버전 **1.0.99.4**. [공식 릴리스](https://github.com/Open-HMG/HMG-API/releases/tag/v1.1.0-rc.4)

## 설치 및 업데이트

1. 합본 ZIP을 FAT32 USB 메모리 최상위에 풉니다. `NEMESIS.data`와 `packages` 폴더가 루트에 있어야 합니다. `packages` 안의 ZIP 세 개는 압축 상태로 둡니다.
2. 주차 상태에서 USB 메모리를 내비게이션 데이터 USB 포트에 꽂습니다. **NEMESIS → Package Store → USB → Korea Projection CN7NPE USB Test**를 선택하고 **Install** 또는 **Update**를 누릅니다.
3. 설치 계획을 승인합니다. HMG-API rc.4와 Realtek 1.1.13이 필요한 경우 NEMESIS가 먼저 설치하거나 업데이트합니다. 기존 CN7NPE USB 테스트판 `1.7.4.1`~`1.7.4.15`는 업데이트할 수 있습니다.
4. USB 메모리를 빼고 A3000mini를 꽂습니다. HMG-API 무선 모드가 재부팅을 요청하면 재부팅합니다. Korea Projection에 **USB Wi-Fi AP ready (rtwlan0)**가 표시되면 iPhone의 Wi-Fi와 Bluetooth를 켜고 페어링합니다.

HMG-API가 응답하지 않으면 내비게이션을 재부팅하고 같은 USB에서 Korea Projection 설치를 다시 선택합니다. 다른 Korea Projection 패키지나 별도로 설치한 무선 모드가 있다면 기존 패키지의 제거 순서를 확인하세요. 합본을 제거할 때는 Korea Projection을 먼저 제거합니다. [Korea Projection 이식 소스와 제거 안내](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb)

A3000mini가 외부 OHCI 포트에서 12Mbps로 잡히면, 대상 장치와 비어 있는 EHCI 단일 포트를 확인해 해당 포트의 EHCI 소유권 복귀를 부팅당 최대 두 번 요청합니다. 실제 속도가 480Mbps로 바뀌었는지 확인한 뒤 AP를 시작합니다. 관련 제어 파일이 없거나 전환에 실패하면 `speed.log`에 이유를 기록합니다. 드라이버 업데이트 뒤에는 A3000mini를 꽂은 채 내비를 완전히 재부팅해 새 모듈과 옵션을 적용합니다.

v0.1.11의 무선 모드는 AP 준비 신호와 `rtwlan0`의 AP 주소를 모두 확인한 뒤 Bluetooth iAP2를 시작합니다. 먼저 연결된 iPhone은 최대 약 3분간 AP를 기다립니다. 대기가 끝나도 AP가 준비되지 않았다면 준비 완료 후 iPhone Bluetooth를 껐다 켜 재연결합니다. A3000mini를 연결한 뒤 Korea Projection이 무선 모드를 **2.4.7로 업데이트한 것을 확인하고** 내비게이션을 완전히 재부팅합니다. 첫 재부팅 뒤에 모드 업데이트 안내가 나왔다면 업데이트를 마친 뒤 다시 재부팅해야 새 훅이 적용됩니다.

## 부팅과 재장착 기록 보내기

1. A3000mini를 꽂은 채 내비게이션을 완전히 재부팅하고 약 2분 기다립니다. 첫 시도에는 Realtek Launch를 누르지 않습니다.
2. 대기 문구나 AP 시작 오류가 계속되면 같은 부팅에서 동글을 한 번 재장착합니다. 필요하면 Realtek Launch를 한 번 누르고 Korea Projection 상태를 확인합니다.
3. 재부팅하기 전에 동글을 빼고 USB 메모리를 연결합니다. **NEMESIS → My Packages → Korea Projection CN7NPE USB Test → Launch → 제보 파일 만들기**를 선택합니다. `KoreaProjection-report`의 `3-log.txt`와 함께 생성된 `1-report.md`, `2-car-report.json`을 확인합니다.

`3-log.txt`의 `speed.log`에는 EHCI 복구 요청과 실제 480Mbps 확인 결과가 들어갑니다. `usb-ap-up-boot.log`와 `usb-ap-up-replug.log`는 같은 부팅의 첫 USB 장치와 USB 장치 번호가 바뀐 뒤의 UP 시도를 기록합니다. 자동 USB 복구에 따른 재열거도 장치 번호가 바뀔 수 있습니다. 각 파일에서 부팅 ID, USB 포트·장치 번호, USB 속도(`usb_speed_mbps`), UP 종료 코드, 전후 커널 로그를 확인할 수 있습니다. `12`는 full-speed, `480`은 high-speed 연결 기록입니다. `usb-hostapd-permissions-*.log`에는 실제 프로세스의 UID·권한·SELinux 컨텍스트가 들어가며, 프로세스가 먼저 종료되면 읽지 못했음을 표시합니다. `usb-hostapd-logcat-*.log`에는 해당 프로세스의 종료 코드와 AP 시작·단말 접속·실패 로그가 들어갑니다. 제보를 위해 동글을 빼고 USB 메모리로 바꾼 뒤에는 현재 상태가 AP lost로 표시될 수 있으므로, 같은 부팅에서 앞서 기록한 UP·AP 시작 결과를 함께 확인합니다.

ARM 모듈과 USB 패키지 구조를 검증했습니다. 실차에서 부팅 인식과 무선 카플레이 연결을 확인하는 진단판입니다.

[합본 변경 이력](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/cn7npe-usb-bundle-v0.1.11/CHANGELOG.md) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md#53-install-on-the-unit)
