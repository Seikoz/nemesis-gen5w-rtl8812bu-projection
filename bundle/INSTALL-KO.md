# 아반떼 N 260902 USB 합본 설치

2024년식 아반떼 N 페이스리프트 CN7NPE KOR `V039.001.260902`, TCC803x, ipTIME A3000mini(`0bda:b812`)용 테스트판입니다. NEMESIS Manager **1.16.7 이상**의 USB Package Store를 사용합니다.

- HMG-API 본체 **1.1.0-rc.4** (NEMESIS 패키지 버전 **1.0.99.4**), 공식 빌드 `31d781b`. [공식 릴리스](https://github.com/Open-HMG/HMG-API/releases/tag/v1.1.0-rc.4) · [AGPL-3.0 대응 소스](https://github.com/Open-HMG/HMG-API/tree/v1.1.0-rc.4)
- Realtek RTL8812BU USB Driver **1.1.9**. [기반 드라이버 릴리스와 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/v1.1.7)
- Korea Projection CN7NPE USB Test **1.7.4.9** 및 번들 무선 모드 **2.4.6**. [기반 Korea Projection 릴리스와 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/kp-usb-test-v0.1.4)

## 설치 순서

1. 내려받은 합본 ZIP을 FAT32 USB 메모리 최상위에 풉니다. 최상위에 `NEMESIS.data`와 `packages` 폴더가 있어야 합니다. `packages` 안의 ZIP 세 개는 압축된 상태로 둡니다.
2. 주차 상태에서 메모리를 차량 데이터 USB 포트에 꽂습니다. **NEMESIS → Package Store → USB**에서 **Korea Projection CN7NPE USB Test**를 열고 **Install** 또는 **Update**를 누릅니다.
3. 설치 계획을 승인합니다. HMG-API와 Realtek이 둘 다 필요하면 NEMESIS가 같은 USB에서 **HMG-API → Realtek → Korea Projection** 순으로 설치합니다. HMG-API rc.4 이상과 Realtek 1.1.9 이상은 각각 요구 버전을 충족합니다. 기존 CN7NPE USB 테스트판 `1.7.4.1`부터 `1.7.4.8`까지는 업데이트할 수 있습니다. 다른 Korea Projection 패키지나 별도로 설치한 무선 모드가 있으면 [기존 테스트판 설치 안내](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/kp-usb-test-v0.1.4)를 확인하세요.
4. 설치가 끝나면 메모리를 빼고 A3000mini를 꽂은 채 내비게이션을 완전히 재부팅합니다. 약 2분 동안 동글을 그대로 두고 **Realtek Launch**를 누르지 않은 상태에서 `rtwlan0`이 잡히는지 확인합니다. Korea Projection에서 `USB Wi-Fi AP ready`가 표시되면 iPhone과 연결합니다.

설치 중 HMG-API가 응답하지 않는다는 메시지가 뜨면 내비게이션을 재부팅하고 같은 USB에서 Korea Projection 설치를 다시 선택합니다. 합본에서 설치한 패키지를 제거할 때는 Korea Projection을 먼저 제거합니다.

## 핫스팟 실패 제보

`hostapd`가 실패로 종료하면 그 프로세스의 최근 Android 로그를 자동으로 저장합니다. 증상이 나오면 재부팅 전에 **NEMESIS → My Packages → Korea Projection CN7NPE USB Test → Launch → 제보 파일 만들기**를 선택합니다. `KoreaProjection-report/3-log.txt`의 `usb-hostapd-logcat.log` 항목에서 종료 코드와 SSID·키를 가린 진단 메시지를 확인할 수 있습니다. 차량 로그에 해당 메시지가 없으면 그 결과도 기록합니다.

USB 패키지 목록과 기존 버전의 업데이트 조건, 실패 직후 로그 수집과 제보 파일 반영을 모의 검증했습니다. 실차에서의 로그 수집과 무선 CarPlay 연결은 확인이 필요합니다.

[NEMESIS USB Package Store 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md#53-install-on-the-unit)
