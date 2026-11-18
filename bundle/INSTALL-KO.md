# 아반떼 N 260902 USB 합본 설치

2024년식 아반떼 N 페이스리프트 CN7NPE KOR `V039.001.260902`, TCC803x, ipTIME A3000mini(`0bda:b812`)용 테스트판입니다. NEMESIS Manager **1.16.7 이상**의 USB Package Store를 사용합니다.

- Realtek RTL8812BU USB Driver **1.1.8** [기반 드라이버 릴리스와 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/v1.1.7)
- Korea Projection CN7NPE USB Test **1.7.4.6** 및 번들 무선 모드 **2.4.6** [기반 Korea Projection 릴리스와 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/kp-usb-test-v0.1.4)

Korea Projection을 설치하려면 차량에서 HMG-API 본체 `1.1.0-rc.3`이 이미 실행 중이어야 합니다. 합본에 들어 있는 것은 Korea Projection이 설치하는 HMG-API 무선 모드입니다.

## 설치 순서

1. 내려받은 합본 ZIP을 FAT32 USB 메모리 최상위에 풉니다. 최상위에 `NEMESIS.data`와 `packages` 폴더가 있어야 합니다. `packages` 안의 두 ZIP은 압축된 상태로 둡니다.
2. 주차 상태에서 메모리를 차량 데이터 USB 포트에 꽂습니다. **NEMESIS → Package Store → USB**에서 **Korea Projection CN7NPE USB Test**를 열고 **Install** 또는 **Update**를 누릅니다.
3. Realtek이 없거나 버전이 1.1.8보다 낮으면 NEMESIS가 같은 USB의 Realtek을 설치 계획에 추가합니다. 이 계획을 승인하면 Realtek 설치 또는 업데이트가 먼저 진행되고 Korea Projection이 이어집니다. 이미 Realtek 1.1.8 이상이 설치되어 있으면 Korea Projection 설치로 넘어갑니다. 기존 CN7NPE USB 테스트판 `1.7.4.1`부터 `1.7.4.5`까지는 업데이트할 수 있습니다. 다른 Korea Projection 패키지나 별도로 설치한 무선 모드가 있으면 [기존 테스트판 설치 안내](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/kp-usb-test-v0.1.4)를 확인하세요.
4. 설치가 끝나면 메모리를 빼고 A3000mini를 꽂은 채 내비게이션을 완전히 재부팅합니다. 약 2분 동안 동글을 그대로 두고 **Realtek Launch**를 누르지 않은 상태에서 `rtwlan0`이 잡히는지 확인합니다. Korea Projection에서 `USB Wi-Fi AP ready`가 표시되면 iPhone과 연결합니다.

두 패키지를 제거할 때는 Korea Projection을 먼저 제거합니다. 이번 합본은 설치 순서와 새 패키지 버전 표기를 반영합니다. 실차에서의 합본 설치, 부팅 자동 인식과 무선 CarPlay 연결은 확인이 필요합니다.

[NEMESIS USB Package Store 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md#53-install-on-the-unit)
