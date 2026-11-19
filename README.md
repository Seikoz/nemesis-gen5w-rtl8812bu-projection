# NEMESIS RTL8812BU Gen5W

현대·기아 Gen5W 내비게이션에서 **RTL8812BU USB 무선랜 드라이버의 인식과 AP 작동을 구현·검증하는 프로젝트**입니다. 현재 테스트 대상은 2024년식 아반떼 N 페이스리프트 `CN7NPE.KOR.S5W_M.V039.001.260902`와 ipTIME A3000mini(`0bda:b812`)입니다. TCC803x, 커널 `3.18.24-tcc`, NEMESIS Manager 1.16.7 이상을 사용합니다. 차량에서 무선 카플레이 연결을 시험할 수 있도록 Korea Projection과 HMG-API를 포함한 USB 설치 ZIP을 제공합니다.

**[USB 설치 ZIP v0.1.13 다운로드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/download/cn7npe-usb-bundle-v0.1.13/NEMESIS-CN7NPE-260902-Bundle-v0.1.13-USB.zip)** · [릴리스 변경 사항](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/cn7npe-usb-bundle-v0.1.13) · [전체 변경 이력](CHANGELOG.md)

| 구성 | 버전 |
| --- | --- |
| Korea Projection CN7NPE USB Test | 1.7.4.18 |
| Realtek RTL8812BU USB Driver | 1.1.13 |
| HMG-API 본체 | 1.1.0-rc.4 |
| HMG-API 무선 CarPlay·Android Auto 모드 | 2.4.9 |

## USB 설치

1. ZIP을 FAT32 USB 메모리 최상위에 풉니다. 아래처럼 `NEMESIS.data`가 루트에 있고 `packages/` 안의 ZIP 세 개가 압축 상태여야 합니다.
2. 주차 상태에서 내비게이션의 데이터 USB 포트에 메모리를 연결합니다. **NEMESIS → Package Store → USB → Korea Projection CN7NPE USB Test**에서 **Install** 또는 **Update**를 누릅니다.
3. 설치 계획을 승인합니다. NEMESIS는 필요한 HMG-API와 Realtek을 같은 USB에서 먼저 설치하거나 업데이트합니다. 무선 모드가 재부팅을 요청하면 내비를 재부팅합니다.
4. 설치 USB를 빼고 A3000mini를 꽂습니다. Korea Projection 상태 화면에 **USB Wi-Fi AP ready (rtwlan0)**가 표시되면 iPhone을 내비게이션 Bluetooth에 페어링하고 CarPlay를 허용합니다.

```text
USB/
├── NEMESIS.data
├── INSTALL-KO.md
└── packages/
    ├── hmgapi.zip
    ├── korea.projection.zip
    └── realtek.88x2bu.zip
```

기존 합본에서 업데이트하거나 설치 중 오류가 발생하면 [합본 설치·업데이트 안내](bundle/INSTALL-KO.md)를 확인하세요.

## 부팅과 재장착 결과 제보

1. A3000mini를 꽂은 채 내비게이션을 완전히 재부팅하고, **Realtek Launch**를 누르기 전에 약 2분 기다립니다.
2. 연결이 실패하면 같은 부팅에서 동글을 한 번 뺐다 꽂고 Korea Projection 상태를 다시 확인합니다. 필요한 경우 Realtek **Launch**를 한 번 누릅니다. v0.1.10은 먼저 USB 480Mbps 복구를 자동 시도합니다.
3. 재부팅하기 전에 USB 메모리로 바꿔 꽂고 **NEMESIS → My Packages → Korea Projection CN7NPE USB Test → Launch → 제보 파일 만들기**를 누릅니다. USB의 `KoreaProjection-report/3-log.txt`에 첫 USB 감지와 장치 번호 변경 후 각각의 UP 시도, 커널 로그, `hostapd` 권한 정보와 실패 로그가 들어갑니다. `1-report.md`와 `2-car-report.json`이 만들어졌다면 함께 첨부해 주세요.

v0.1.11 실차 로그에서 AP 준비 후 Bluetooth iAP2 시작까지 확인했습니다. 이후 동적 TCP 포트의 연결 재시도가 기록됐으며, 기존 단말 수 집계는 Realtek 접속을 놓칠 수 있었습니다. v0.1.12는 `rtwlan0`의 AP IPv4 대역과 IPv6 링크 로컬 대역에서 동적 TCP를 허용하고, hostapd 인증 목록 또는 Realtek의 현재 연결 테이블로 단말 수를 표시합니다. 읽지 못하면 0대 대신 **확인 불가**로 표시합니다.

v0.1.13은 IPv6 링크 로컬 피어의 UDP 6031을 추가 허용합니다. **AP 준비·Wi-Fi 단말 접속과 카플레이 연결 완료를 구분**하며, 실제 무선 세션 시작 콜백을 받은 경우에만 연결됨으로 표시합니다. 생성·시작·종료 콜백과 현재 부팅·AP 세대·DiPO 프로세스 시작 시각을 대조하므로 이전 세션 기록으로 연결됐다고 판단하지 않습니다. 갱신은 보통 다음 점검 주기(약 30초)에 반영됩니다.

제보 파일 `3-log.txt`에 `usb-carplay-events.log`, `usb-cp-capture.log`, `usb-connection-first.log`, `usb-connection-latest.log`를 포함합니다. 방화벽의 실제 규칙·점프 순서·패킷/바이트 카운터와 IPv6 UDP 6031 항목 수, mDNS 조회 결과·서비스 포트, TCP 소켓 상태를 확인할 수 있습니다. 첫 스냅샷과 최근 스냅샷을 보존하므로 동글을 빼고 제보 USB로 바꾼 뒤에도 직전 기록을 볼 수 있습니다. mDNS 응답 없음만으로 서비스 부재나 연결 실패를 단정하지 않습니다.

동글 연결 후 무선 모드가 **2.4.9로 업데이트되고 적용된 것을 확인한 뒤** 완전히 재부팅합니다. 실차의 카플레이 연결 성공은 아직 미확인입니다.

## 버전별 변경 사항

| 합본 버전 | 변경 사항 |
| --- | --- |
| v0.1.13 | IPv6 UDP 6031 허용, 실제 방화벽 규칙·순서·카운터와 mDNS 진단, 실제 카플레이 세션 기준 연결 표시 |
| v0.1.12 | USB AP 대역의 동적 TCP 허용, 현재 접속 단말 수·확인 불가 표시, 기존 설치의 포트 정책 자동 적용 |
| v0.1.11 | AP 준비 전에 Bluetooth iAP2가 시작되는 순서 수정, 준비 후 자동 진행, 끊긴 연결의 대기 취소 |
| v0.1.10 | 부팅 시 A3000mini의 외부 포트를 EHCI로 되돌리는 복구 추가, 실제 USB 480Mbps를 확인한 뒤 AP 시작 |
| v0.1.9 | 분리된 네트워크 장치 등록 정리, 재장착 시 AP·DHCP 재시작, 첫 USB 기록 저장 수정, USB 속도·단말 접속 로그 추가 |
| v0.1.8 | Realtek 절전 옵션 비활성화, HALMAC 단계별 실패 로그 추가, `printf` 미지원 오류 수정, 인터페이스 UP 성공 뒤 AP 시작 |
| v0.1.7 | 칩 초기화 실패 로그와 부팅·재열거별 UP 결과, `hostapd` 권한·실패 로그를 제보 파일에 추가 |
| v0.1.6 | 인터페이스 활성화가 거부되면 권한·USB 상태 확인 후 드라이버 연결을 부팅당 한 번 갱신 |
| v0.1.5 | 기존 HMG-API 무선 모드가 남은 상태에서 Korea Projection을 업데이트하는 조건 수정 |
| v0.1.4 | `hostapd` 실패 직후 해당 프로세스의 Android 로그 자동 수집 |
| v0.1.3 | HMG-API 본체를 공식 1.1.0-rc.4로 교체 |
| v0.1.2 | HMG-API 본체를 포함하고 Korea Projection 설치 시 필요한 의존성을 먼저 설치 |
| v0.1.1 | Korea Projection 설치 시 Realtek 드라이버를 같은 USB에서 먼저 설치 |
| v0.1.0 | Korea Projection CN7NPE USB 테스트판과 Realtek 드라이버를 하나의 USB 설치 ZIP으로 제공 |

자세한 수정 내역과 이전 드라이버 버전의 이력은 [CHANGELOG.md](CHANGELOG.md)에 기록합니다.

## 릴리스 운영

새 합본 ZIP은 GitHub의 **Latest**로 등록합니다. 테스트 상태는 영문 릴리스 제목과 본문에 표시합니다. 새 공개 다운로드와 SHA-256을 확인한 뒤 이전 릴리스와 태그를 정리해 최신 합본 ZIP 한 개를 제공합니다. 변경 사항은 배포 전에 이 README와 CHANGELOG.md에 기록합니다. [Latest release](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/latest)

## 소스와 라이선스

- [Realtek 대응 소스·Gen5W 빌드 설정](driver-source/README.md) · [USB 리셋 도구](driver-source/usb_reset_a3000mini.c)
- [Korea Projection 1.7.4 원본](https://github.com/StopDragon/korea-projection/tree/v1.7.4) · [CN7NPE USB 이식 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb) · [합본 진단 스크립트](bundle)
- [HMG-API 1.1.0-rc.4](https://github.com/Open-HMG/HMG-API/tree/v1.1.0-rc.4) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
