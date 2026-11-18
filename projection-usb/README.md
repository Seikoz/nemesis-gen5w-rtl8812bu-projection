# Korea Projection 1.7.4 USB CarPlay 테스트판

대상은 2024년식 아반떼 N 페이스리프트 CN7NPE KOR `V039.001.260902`, TCC803x, ipTIME A3000mini `0bda:b812`입니다. NEMESIS, HMG-API 1.1.0-rc.3, RTL8812BU Gen5W v1.1.4를 먼저 설치합니다. 실제 차량과 iPhone 연결 검증이 필요한 프리릴리즈입니다.

## 설치와 확인

기존 CN7NPE USB 테스트판 `1.7.4.1` 사용자는 이 ZIP으로 Korea Projection만 업데이트합니다. NEMESIS에서 업데이트를 승인하고, 설치 USB를 뺀 뒤 A3000mini를 꽂은 채 내비를 재부팅합니다. Realtek Launch를 누르기 전에 Korea Projection이 자동으로 AP를 준비하는지 확인합니다.

처음 설치하는 경우 아래 순서를 따릅니다.

1. A3000mini를 연결하고 NEMESIS → My Packages → Realtek RTL8812BU USB Driver → Launch에서 `rtwlan0`이 잡히는지 확인합니다. 부팅 직후 나타나지 않으면 동글을 재장착해 확인합니다.
2. 기존 Korea Projection이 설치되어 있으면 NEMESIS에서 제거합니다. 별도로 설치한 `wireless-carplay-aa` 모드가 남아 있다면 HMG-API에서 해당 모드만 제거하고 변경을 적용합니다. 재부팅 안내가 나오면 재부팅합니다.
3. 릴리즈의 `Korea-Projection-1.7.4.2-CN7NPE-USB-Test.zip`을 FAT32 USB의 최상위에 풉니다. USB 루트에 `NEMESIS.data`가 보여야 합니다. `packages/korea.projection.zip`은 압축된 상태로 둡니다.
4. 정차 상태에서 NEMESIS Manager로 USB 패키지를 설치합니다. 설치 직후 HMG-API가 차량 훅 위치와 변경 계획을 확인하므로 3~5분 기다립니다. My Packages → Korea Projection CN7NPE USB Test → Launch를 열고 재부팅 안내가 나오면 USB 메모리를 뺀 뒤 재부팅합니다. 동글은 연결해 둡니다.
5. Launch에서 USB AP가 준비됐는지 확인합니다. iPhone의 Wi-Fi와 Bluetooth를 켜고 내비게이션의 기기 연결 메뉴에서 Bluetooth로 페어링한 뒤 iPhone의 CarPlay 연결을 허용합니다.

실패하면 Korea Projection → Launch → **차량 정보 저장하기**로 보고서를 저장합니다. `3-log.txt`의 `usb-realtek-launch.log` 항목에 자동 호출 결과가 들어갑니다. Realtek v1.1.6의 `Korea Projection 1.7.4.2 does not support USB Wi-Fi` 문구는 공식 1.7.x 기준으로 출력됩니다. 먼저 `RTL8812BU ready: rtwlan0`이 표시되는지 확인합니다.

## 되돌리기

NEMESIS에서 Korea Projection CN7NPE USB Test를 제거합니다. 설치 프로그램이 추가한 무선 모드는 HMG-API를 통해 제거하고, 시험판이 추가한 방화벽 허용 항목을 회수합니다. 재부팅 후 원래 Korea Projection 패키지를 다시 설치할 수 있습니다.

## 변경 이력

### USB Test v0.1.1 (NEMESIS 패키지 1.7.4.2)

- Korea Projection이 A3000mini를 감지했지만 `rtwlan0`이 없으면 직접 Realtek의 `nemesis pkg-launch`를 호출합니다. 첫 호출 뒤에도 인터페이스가 없으면 버튼이 실행하는 `load.sh`를 수동 모드로 호출하며, 같은 USB 감지 상태에서 최대 세 번만 시도합니다.
- 기존 CN7NPE 패키지에서 USB 업데이트를 허용합니다. HMG-API 무선 모드 2.4.6과 설정 도구는 v0.1.0에서 배포한 파일을 그대로 사용합니다.
- 매 부팅마다 AP 준비 표시를 다시 평가하고, 자동 Launch 결과를 차량 보고서에 포함합니다.

### USB Test v0.1.0

- Korea Projection 1.7.4의 AP 서비스와 상태 화면이 `rtwlan0`을 사용합니다. 서비스는 `0bda:b812` 드라이버 바인딩을 확인하고, 동글이 늦게 잡히면 감지 후 AP를 시도합니다.
- HMG-API 무선 모드 `2.4.6`을 새로 빌드하고 서명했습니다. DiPO의 Bluetooth 기반 무선 CarPlay 경로를 USB AP로 바꾸고 CN7NPE KOR 260902만 대상으로 지정했습니다.
- OEM Wi-Fi 서비스에서 CarPlay용 SSID와 WPA2 키를 가져옵니다. 차량 보고서에 없는 `softap.conf` 파일을 직접 읽는 데 의존하지 않습니다.
- DHCP 포트는 드라이버의 UDP 67 ↔ 1067 변환에 맞춥니다. HMG-API에는 USB 인터페이스의 DHCP, Bonjour, CarPlay 및 IPv6 이웃 탐색용 허용 규칙을 등록합니다.

## 소스와 라이선스

- Korea Projection 1.7.4의 스크립트와 APK는 GNU AGPL 3.0을 따릅니다. [원본 태그 및 소스](https://github.com/StopDragon/korea-projection/tree/v1.7.4)
- HMG-API의 무선 모드는 GNU AGPL 3.0을 따릅니다. [원본 무선 모드 소스](https://github.com/StopDragon/HMG-API/tree/b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa)
- 이 시험판의 수정과 빌드 스크립트도 GNU AGPL 3.0을 따릅니다. [시험판에 사용한 수정 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/kp-usb-test-v0.1.1/projection-usb)
- 동봉된 BusyBox의 GPL 2.0 안내와 대응 소스 위치는 패키지의 `bin/busybox-LICENSE.txt`에 있습니다.
