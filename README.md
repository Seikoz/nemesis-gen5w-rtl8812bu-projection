# NEMESIS RTL8812BU Gen5W

현대·기아 Gen5W 내비게이션에서 **RTL8812BU USB 무선랜 드라이버의 인식과 AP 작동을 구현·검증하는 프로젝트**입니다. 현재 테스트 대상은 2024년식 아반떼 N 페이스리프트 `CN7NPE.KOR.S5W_M.V039.001.260902`와 ipTIME A3000mini(`0bda:b812`)입니다. TCC803x, 커널 `3.18.24-tcc`, NEMESIS Manager 1.16.7 이상을 사용합니다. 차량에서 무선 카플레이 연결을 시험할 수 있도록 Korea Projection과 HMG-API를 포함한 USB 설치 ZIP을 제공합니다.

**[USB 설치 ZIP v0.1.18 다운로드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/download/cn7npe-usb-bundle-v0.1.18/NEMESIS-CN7NPE-260902-Bundle-v0.1.18-USB.zip)** · [릴리스 변경 사항](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/cn7npe-usb-bundle-v0.1.18) · [전체 변경 이력](CHANGELOG.md)

| 구성 | 버전 |
| --- | --- |
| Korea Projection CN7NPE USB Test | 1.7.4.23 |
| Realtek RTL8812BU USB Driver | 1.1.16 |
| HMG-API 본체 | 1.1.0-rc.7 |
| RTL8812BU USB 무선 모드 | 2.4.11 (공식 2.2.0-rc.8 기반) |

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

동글 연결 후 무선 모드가 **2.4.10로 업데이트되고 적용된 것을 확인한 뒤** 완전히 재부팅합니다. 실차의 카플레이 연결 성공은 아직 미확인입니다.

v0.1.14는 `transport=0`으로 시작한 실제 무선 세션이 SPP 종료 직후 `BT_DETACHED`로 끊기던 경로를 수정합니다. USB iAP2 연결이 없고, 이 브리지가 요청한 Bluetooth iAP2(컴포넌트 4)의 기기 일치와 같은 `rtwlan0` AP 준비를 확인한 경우에만 해당 세션을 무선으로 인정합니다. SPP가 끝나면 카플레이 채널(컴포넌트 5)로 이관합니다. 실제 USB 연결과 확인되지 않은 세션은 구분합니다.

종료·재연결·AP 변경 뒤 이전 작업이 실행되지 않도록 attach/detach와 대기 중인 iAP2 전송을 세션별로 확인합니다. 상태 기록과 15초 갱신에서도 원래 `transport=0` 값을 보존합니다. HMG-API 본체와 Realtek 드라이버를 따로 재설치할 필요는 없습니다. 실차의 연결 유지 여부는 확인이 필요합니다.

v0.1.15는 USB가 OHCI 12Mbps로 인식된 상태에서 EHCI 복구 도구가 `Permission denied`로 실행되지 않던 경로를 수정합니다. Realtek **1.1.14**는 패키지 도구의 실행 권한을 확인·복구한 뒤 기존 EHCI 복구를 요청하고, 실제 재열거 후 **USB 480Mbps**를 확인합니다. 실행 준비 실패는 하드웨어 시도 횟수에 포함하지 않습니다. Korea Projection **1.7.4.20** 설치 시 같은 USB의 새 Realtek 패키지가 먼저 설치/업데이트됩니다.

여기의 **12/480Mbps는 USB 버스 인식 속도이며 Wi-Fi 링크 속도나 실제 전송량이 아닙니다.** 물리 연결이나 장치 상태 때문에 480Mbps를 확인하지 못하면 AP 시작을 계속 대기하고 `speed.log`에 결과를 남깁니다. 실차의 480Mbps 인식과 카플레이 연결 지속 여부는 확인이 필요합니다. 무선 모드 **2.4.10**의 세션 판정·iAP2 이관과 기존 드라이버 커널 모듈은 유지합니다.

v0.1.16은 소유권 반환 뒤에도 USB 12Mbps가 유지되면 **외부 OHCI/EHCI 컨트롤러를 EHCI 우선 순서로 다시 초기화하는 두 번째 단계**를 자동 시도합니다. 직결 A3000mini 한 대, 단일 포트의 유일한 외부 플랫폼 컨트롤러 쌍, 비어 있는 EHCI와 내려간 인터페이스를 확인한 경우에만 진행합니다. 내부 `tcc-ehci`, 다른 장치가 연결된 루트, 허브·복수 컨트롤러·활성 인터페이스는 제외합니다.

Realtek **1.1.15**와 Korea Projection **1.7.4.21**을 포함합니다. 기존 소유권 반환 한 번과 새 재초기화 한 번으로 부팅당 횟수를 제한하고, 실제 USB 속도 480을 확인한 경우에만 AP를 시작합니다. 호스트 드라이버 재등록은 물리 VBUS 전원 차단을 보장하지 않습니다. 차량 보드의 바인딩 지원·PHY 동작에 따라 결과가 달라지므로 실차에서 480Mbps 전환을 확인해야 합니다.

v0.1.17은 EHCI 등록 1초 뒤 OHCI를 복원하던 고정 지연을 바꾸어, **EHCI 아래 A3000mini의 실제 480Mbps·구성 완료를 최대 12초 확인한 뒤 OHCI를 복원**합니다. 버스 번호 대신 검증한 플랫폼 장치를 따라가고, 준비되지 않아도 제한 시간 뒤 호스트 복원을 시도합니다. Korea Projection의 드라이버 호출 제한을 20초에서 90초로 늘립니다. 복구별 시작 uptime과 버스 번호 변경 전후의 커널 메시지를 `speed.log`에 남깁니다. Realtek **1.1.16**, Korea Projection **1.7.4.22**를 포함하며 실차 전환 결과는 확인이 필요합니다.

v0.1.18은 **HMG-API 본체 1.1.0-rc.7**과 **공식 무선 모드 2.2.0-rc.8 기반 USB 이식판 2.4.11**을 포함합니다. Korea Projection **1.7.4.23**만 설치/업데이트하면 필요한 본체가 같은 USB에서 먼저 업데이트되고, 기존 모드도 같은 합본 작성자 서명으로 교체됩니다. `rtwlan0`·USB AP 준비 대기·확인된 transport=0 세션·iAP2 이관·방화벽 진단을 최신 소스에 이식했습니다. Realtek **1.1.16**은 그대로입니다.

기존 차량 지도의 351개 훅에 없는 신규 8개 선언은 모드 전체가 비활성화되는 것을 막기 위해 제외했습니다. 새 다중 휴대폰 제어·AA 주차 기능은 이 대상 빌드에서 등록하지 않으며, 카플레이 주차 기능도 추가 지도 점이 있어야 작동합니다. 이전 한국판의 `tbt_fit`·별표 팝업 건너뛰기는 이번 상위 소스에 이식하지 않았습니다. [호환성 검토와 제한 사항](docs/compatibility-rc7-rc8-usb.md)을 확인하세요.

설치 후 완전히 재부팅하고 HMG-API **1.1.0-rc.7 / Hooks on**, 무선 모드 **2.4.11**을 확인합니다. 모드 교체/적용 뒤 재부팅 안내가 나오면 한 번 더 재부팅하세요. USB 480Mbps 전환과 카플레이의 화면·음성·연결 유지는 실차에서 확인이 필요합니다.

## 버전별 변경 사항

| 합본 버전 | 변경 사항 |
| --- | --- |
| v0.1.18 | HMG-API rc.7 + 공식 무선 rc.8 기반 USB 이식판 2.4.11, 351개 지도 호환·AP 대기·세션/이관·방화벽 검증, Realtek 1.1.16 유지 |
| v0.1.17 | EHCI 480Mbps 구성 완료 대기 후 OHCI 복원, 드라이버 호출 제한 20→90초, USB 버스 재번호화 이후의 커널 로그 수집 |
| v0.1.16 | 소유권 반환 후 12Mbps가 유지되면 외부 OHCI/EHCI를 EHCI 우선 순서로 재초기화, 대상 범위·복원·실제 480 확인 |
| v0.1.15 | USB 12→480Mbps 복구 도구의 실행 권한 누락 수정, 준비 실패 시 시도 예산 보존, 조회·진단 도구 실행 권한 복구 |
| v0.1.14 | 확인된 USB-AP Bluetooth 세션의 transport=0 판정, SPP 종료 후 iAP2 이관, 이전 세션의 예약 작업·전송 차단 |
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

## v0.1.18 배포 검증

- [공식 SDK·회귀 24개·실제 수정 메서드/패치 엔진·351개 지도 호환 검사와 Android API 19 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44701743445)를 통과했습니다. 상위 CpTx/재이관 91개와 경로 안내 60개 검사도 포함합니다. 사유 제조사 라이브러리가 필요한 네이티브 레시피 검사는 파일 부재로 건너뛰었습니다.
- 29개 셸 문법, rc.7 내부 파일/지도 493개 해시, 모드 작성자/서명·업데이트 조건, 실제 rc.4 스크립트의 상태 보존, 기존 드라이버/도구 보존과 동일 입력 재빌드를 확인했습니다. 실차 USB 480Mbps·연결·음성은 확인이 필요합니다.
- USB ZIP SHA-256: `c49b5052ed26fdaa428fbc89eed3df98b8e641423a3895fe9ff8859c95fe9a87`

## v0.1.17 배포 검증

- [실제 C 코드의 EHCI 버스 재번호화·지연 준비·미구성/다른 장치·시간 초과·실패/신호 복원 검사, 24개 회귀 검사와 Android API 19 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44680540924)를 통과했습니다.
- 29개 셸 문법, 새 드라이버 의존성·90초 호출 제한·모드 서명, 기존 커널/카플레이 모드/본체 보존과 동일 입력 재빌드를 확인했습니다. 차량에서 실제 480Mbps 전환은 확인이 필요합니다.
- USB ZIP SHA-256: `773ebcc1e222caddbe4497b45fa1777a7ad6f5918c0533b4f8e62c0f52dddab4`

## v0.1.16 배포 검증

- [실제 C 코드의 외부 호스트 재초기화 모의 검사·기존 EHCI 검사·23개 회귀 검사와 Android API 19 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44677378486)를 통과했습니다. 해제/등록 효과와 실패·SIGTERM을 모의해 순서·내부 호스트 보존·복원을 확인했습니다.
- 29개 셸 문법, 새 의존성·helper ELF·모드 서명, 기존 커널/카플레이 모드/본체 보존과 동일 입력 재빌드를 확인했습니다. 실차 480Mbps 자동 전환은 확인이 필요합니다.
- USB ZIP SHA-256: `74022f1af7b88e1a6130ab4e4417afeb30e3805505375511a410acc301424e78`

## v0.1.15 배포 검증

- [Linux의 실행 비트 손실 재현·22개 회귀 검사·기존 EHCI 범위 검사와 Android API 19 도구 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44668325705)를 통과했습니다.
- 29개 셸 문법, 새 드라이버 의존성, 모드 서명과 기존 커널/실행 파일/카플레이 모드 보존 및 동일 입력 재빌드를 확인했습니다. 실차의 USB 480Mbps 복구와 Wi-Fi 처리량은 아직 확인되지 않았습니다.
- USB ZIP SHA-256: `db9b9339939a9e560b81da5f1f1a1f1c2679641ffce496cdbecae7d7dbee78bb`

## v0.1.14 배포 검증

- [실제 수정 메서드의 끊김 재현·이관·세션 격리 검사와 Android API 19 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44665053112)를 통과했습니다. 16개 회귀 검사, 기존 AP 대기 검사와 원래 transport 값을 보존하는 상태 갱신 검사도 포함합니다.
- 중첩 ZIP·29개 셸 문법·동일 작성자 서명, 2.4.6~2.4.10 업데이트/재설치 조건, 기존 드라이버·본체·네트워크 정책 보존을 확인했습니다. 동일 입력 재빌드의 파일 내용도 일치합니다. 실차의 연결 지속 여부는 확인이 필요합니다.
- USB ZIP SHA-256: `ddac046fe0a26230b1a5548a44194b83d995f133ab7f6fc2c2adf2f6a25ad1f1`

## v0.1.13 배포 검증 기록

- [회귀 검사·세션 콜백·Android 훅 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44536318095), [mDNS 응답 해석 검사·ARMv7 도구 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44535807005)를 통과했습니다.
- 중첩 패키지·29개 셸 문법·모드 서명·드라이버/본체 보존과 동일 입력 재빌드를 확인했습니다. 차량에서의 실제 방화벽 통과·카플레이 동작 확인은 남아 있습니다.
- USB ZIP SHA-256: `340087b19afb6daaea24699776a1ebc80eed468da0ea121f5377129ab1b79f5c`

## 릴리스 운영

새 합본 ZIP은 GitHub의 **Latest**로 등록합니다. 테스트 상태는 영문 릴리스 제목과 본문에 표시하고 공개 다운로드와 SHA-256을 확인합니다. **이전 릴리스·태그·설치 ZIP은 삭제하지 않고 보존**하여 버전별로 내려받을 수 있게 합니다. 각 릴리스에는 완성된 USB 설치 ZIP 한 개를 올립니다. 변경 사항은 배포 전에 이 README와 CHANGELOG.md에 기록합니다. [Latest release](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/latest)

## 소스와 라이선스

- [Realtek 대응 소스·Gen5W 빌드 설정](driver-source/README.md) · [USB 리셋 도구](driver-source/usb_reset_a3000mini.c)
- [Korea Projection 1.7.4 원본](https://github.com/StopDragon/korea-projection/tree/v1.7.4) · [CN7NPE USB 이식 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb) · [합본 진단 스크립트](bundle)
- [HMG-API 1.1.0-rc.7](https://github.com/Open-HMG/HMG-API/tree/v1.1.0-rc.7) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
