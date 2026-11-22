# NEMESIS RTL8812BU Gen5W Wireless Projection

현대 Gen5W 내비게이션에서 RTL88x2BU USB 무선랜을 무선 CarPlay와 Android Auto에 사용하기 위한 USB 설치 합본입니다. Korea Projection, Realtek 드라이버, HMG-API를 담았습니다.

> [!WARNING]
> 설치·업데이트·제거 과정에서 내비게이션이 멈추거나 반복 재부팅할 수 있습니다. 순정 블루투스·폰 프로젝션에 문제가 생기면 복구나 정비가 필요할 수 있습니다. 주차 상태에서 진행하고, 설치가 끝날 때까지 전원을 끄거나 USB를 빼지 마세요.
>
> 모든 책임은 설치하신 차주 본인에게 있습니다.

**[최신 USB 설치 ZIP 다운로드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/latest)** · [설치·제거 상세 안내](bundle/INSTALL-KO.md) · [전체 변경 이력](CHANGELOG.md)

## 지원 환경

| 항목 | 기준 |
| --- | --- |
| 차량 | 아반떼 CN7PE, 아반떼 하이브리드 CN7HEVPE, 아반떼 N CN7NPE |
| 펌웨어 | 국내형 **V039.001.260902**. 제품 속성의 `S5W_M`·`0000` 표기 지원 |
| 무선랜 | 아래 동글 목록 참고. 인터페이스 `rtwlan0` |
| 설치 전제 | NEMESIS Manager **1.16.7 이상** 설치, FAT32 USB 메모리 |

### 지원 동글과 시험 범위

| 모델 | USB ID 및 확인 범위 |
| --- | --- |
| ipTIME A3000mini | `0bda:b812`. CN7NPE 260902 실차 확인 |
| TP-Link Archer T3U V1 | `2357:012d`. Gen5W 모듈의 USB ID와 Korea Projection의 감지 경로를 확인했습니다. 실차 시험 전입니다. [Linux 드라이버 ID 표](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/realtek/rtw88/rtw8822bu.c) |
| 리버네트워크 NEXI NX-AC1300 (NX1126) | 제조사 사양은 RTL8812BU입니다. 출고 USB ID는 미확인이고, 공식 Linux 드라이버의 Wi-Fi 전용 기본값인 `0bda:b812`로 열거되는 기기를 시험 대상으로 합니다. [제조사 사양](https://nexi.co.kr/?np_cat=22&page_id=29) · [공식 드라이버](https://nexi.co.kr/?page_id=39&mod=document&uid=39) |

새 동글은 한 번에 하나씩 연결해 USB 480Mbps와 `rtwlan0` 준비 여부를 확인합니다. TP-Link에 대한 EHCI 호스트 자동 복구는 시험 범위에서 제외됩니다.

## 설치 및 업데이트

1. 최신 릴리스의 **Assets**에서 `-USB.zip`을 받아 FAT32 USB 메모리 최상위에 풉니다. `NEMESIS.data`와 `packages/`가 USB 루트에 있어야 합니다. `packages/` 안의 ZIP은 그대로 둡니다.
2. 주차 상태에서 **NEMESIS → Package Store → USB → Korea Projection BETA → Install / Update**를 선택합니다. 필요한 HMG-API와 Realtek 드라이버는 먼저 설치 또는 갱신됩니다.
3. 설치 USB를 사용할 동글로 교체하고 무선 모드의 적용·재부팅 안내를 따릅니다. **USB Wi-Fi AP ready (rtwlan0)**가 표시되면 iPhone의 Wi-Fi와 Bluetooth를 켜고 CarPlay에 연결합니다.
4. 합본의 HUD 경로 안내는 기본 **꺼짐**입니다. 별도 **Phone Projection TBT**를 사용 중이라면 합본 HUD 옵션을 끈 상태로 두세요. 업데이트 시 저장된 설정은 유지됩니다. [HUD 설정 방법](bundle/INSTALL-KO.md#hud-경로-안내)

제거할 때는 Korea Projection을 먼저 제거합니다. 무선 모드 업데이트는 합본으로 진행하세요. [설치·제거 상세 안내](bundle/INSTALL-KO.md)

## v0.1.41 변경 사항

- Wireless Mode의 HUD·계기판 경로 안내를 기본으로 끄고, 명시적으로 저장한 선택은 유지합니다.
- USB 설치 안내를 정리하고, 하이브리드 호환성 CI가 저장소 안의 훅 이름 목록을 사용하도록 변경했습니다.

| 구성 요소 | 버전 |
| --- | --- |
| Korea Projection BETA | **1.7.4.46** |
| HMG-API Wireless Mode | **2.4.29** (CN7PE·CN7NPE), **2.4.30** (CN7HEVPE) |
| HMG-API 본체 | **1.1.0-rc.8** (NEMESIS 패키지 **1.0.99.8**) |
| Realtek Wi-Fi Driver | **1.1.19** |

Realtek 드라이버가 동글에 연결되고 USB 480Mbps 조건을 충족하면 Korea Projection이 `rtwlan0`에 핫스폿을 엽니다. 무선 모드는 Bluetooth iAP2 세션을 Wi-Fi로 넘깁니다. USB 480Mbps 표시는 USB 버스 연결 속도입니다. [무선 모드 동작 및 빌드](projection-source/README.md)

## 실차 확인 결과

| 항목 | 확인 결과 |
| --- | --- |
| 아반떼 N CN7NPE 260902와 A3000mini | v0.1.36에서 동글을 꽂은 채 부팅해 재장착이나 Realtek 수동 Launch 없이 USB 480Mbps와 AP 준비를 확인했습니다. 한 시험에서 USB 인식은 부팅 약 14초, AP 준비는 약 27초였습니다. |
| 무선 CarPlay 음악 | 같은 차량에서 오디오 보정 적용 후 차량 스피커 출력이 확인됐습니다. 기존에 소리가 iPhone에서만 나오던 증상은 이 시험에서 해결됐습니다. |
| 곡 전환 | 같은 차량에서 제목은 즉시 바뀌고, **무선 CarPlay에서만 약 1초간 무음 뒤** 새 곡이 시작됐습니다. v0.1.39에서 무음 전후의 스트림과 출력 상태를 수집합니다. |
| HUD | 별도 Phone Projection TBT를 켜고 합본의 TBT를 끈 상태에서 작동이 확인됐습니다. v0.1.38의 통합 HUD 경로는 회전·거리 메시지 재현을 통과했으며 실차 확인을 기다리고 있습니다. |
| CarPlay 확인창 | 연결 때 차량 정보 제공 동의창이 반복 표시됐습니다. 기존 동의가 재부팅 후에도 유지되는지는 추가 확인이 필요합니다. |

장시간 재연결, 통화·Siri·내비 안내 음성, Android Auto 실차 동작, CN7PE·CN7HEVPE의 차량별 동작은 확인 중입니다.

## 문제 제보

곡 전환 무음을 시험할 때는 **HMG-API Wireless Mode → CarPlay’s own log (troubleshooting)**를 켜고 재부팅합니다. 다운로드한 곡을 무선으로 재생하며 세 번 넘긴 뒤 버튼을 누른 시각을 각각 기록합니다. 마지막 전환 약 1분 뒤 아래 절차로 로그를 저장합니다. [곡 전환 시험 상세 안내](bundle/INSTALL-KO.md#무선-곡-전환-무음-시험)

1. 증상을 재현한 뒤 시각, 차량·펌웨어, 합본 버전을 기록합니다. HUD는 지도 앱과 방향·거리 표시 여부를 함께 적습니다.
2. 같은 부팅에서 동글을 제보 USB로 바꾸고 **NEMESIS → My Packages → Korea Projection → Launch → 제보 파일 만들기**를 선택합니다.
3. `KoreaProjection-report/3-log.txt`와 `1-report.md`, `2-car-report.json`을 공유합니다. USB 인식 문제에는 Realtek `speed.log`와 `boot.log`도 첨부해 주세요. 공유 전에 기기 이름·주소와 위치 정보가 포함됐는지 확인하세요.

## 버전별 변경 사항

| 버전 | 주요 변경 |
| --- | --- |
| **v0.1.41** | HUD 경로 안내 기본 끔, USB 설치 안내 간소화, 하이브리드 CI 외부 첨부 의존성 제거 |
| v0.1.40 | Archer T3U V1 감지 및 CN7NPE 오디오 보정 적용 추가. NEXI NX-AC1300은 USB ID 조건부 시험 모델로 기록 |
| v0.1.39 | 무선 곡 전환 무음 진단. 음악 정보·버퍼 비우기·AAC 디코딩·출력 버퍼 고갈 관측과 출력 스레드 상태 기록 |
| v0.1.38 | CarPlay HUD 회전·거리 갱신 및 Wi-Fi 전환 뒤 경로 안내 요청 개선. v0.1.37의 오디오 통합 포함 |
| v0.1.37 (로컬 시험) | CN7NPE 오디오 보정을 무선 모드에 통합하고 Stock Bluetooth handoff 시험 옵션 제거 |
| v0.1.36 | 순정 CarPlay 라이브러리 MD5 검사 수정. CN7NPE에서 무선 CarPlay의 차량 스피커 출력 확인 |

v0.1.41 USB ZIP SHA-256 `51cd1e81beab7673afb5f5d526e3eec8f5e0e2d80dae595efff455d582dfe4d5`

[전체 변경 이력](CHANGELOG.md) · [이전 릴리스와 설치 ZIP](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases) · [이전 기술 검증 기록](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/cn7npe-usb-bundle-v0.1.36/README.md#검증-범위)

## 소스와 라이선스

- [Realtek 드라이버·USB 복구 도구](driver-source/README.md) · [USB 합본 스크립트](bundle)
- [Korea Projection 원본](https://github.com/StopDragon/korea-projection/tree/v1.7.4) · [CN7NPE USB 이식 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb)
- [공식 HMG-API rc.8](https://github.com/Open-HMG/HMG-API/tree/v1.1.0-rc.8) · [기반 무선 모드 2.2.0-rc.8](https://github.com/Open-HMG/hmgapi-wireless-cp-aa/tree/c47c0bbf8513e725c9852acb932bdde39e3d7edc)
- [무선 모드 이식 소스](projection-source) · [차량 지도 호환성](docs/compatibility-rc7-rc8-usb.md) · [HMG-API AGPL-3.0 라이선스](bundle/licenses/HMG-API-AGPL-3.0.txt)
