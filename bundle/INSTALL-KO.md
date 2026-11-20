# 아반떼 N 260902 USB 합본 설치

대상은 2024년식 아반떼 N 페이스리프트 CN7NPE KOR `V039.001.260902`, TCC803x, ipTIME A3000mini(`0bda:b812`)입니다. NEMESIS Manager **1.16.7 이상**의 USB Package Store를 사용합니다.

- Korea Projection CN7NPE USB Test **1.7.4.23** 및 무선 모드 **2.4.10**
- Realtek RTL8812BU USB Driver **1.1.16**
- HMG-API 본체 **1.1.0-rc.7**, NEMESIS 패키지 버전 **1.0.99.7**. [공식 릴리스](https://github.com/Open-HMG/HMG-API/releases/tag/v1.1.0-rc.7)

## 설치 및 업데이트

1. 합본 ZIP을 FAT32 USB 메모리 최상위에 풉니다. `NEMESIS.data`와 `packages` 폴더가 루트에 있어야 합니다. `packages` 안의 ZIP 세 개는 압축 상태로 둡니다.
2. 주차 상태에서 USB 메모리를 내비게이션 데이터 USB 포트에 꽂습니다. **NEMESIS → Package Store → USB → Korea Projection CN7NPE USB Test**를 선택하고 **Install** 또는 **Update**를 누릅니다.
3. 설치 계획을 승인합니다. HMG-API rc.7와 Realtek 1.1.16이 필요한 경우 NEMESIS가 먼저 설치하거나 업데이트합니다. 기존 CN7NPE USB 테스트판 `1.7.4.1`~`1.7.4.23`은 업데이트할 수 있습니다.
4. USB 메모리를 빼고 A3000mini를 꽂습니다. HMG-API 무선 모드가 재부팅을 요청하면 재부팅합니다. Korea Projection에 **USB Wi-Fi AP ready (rtwlan0)**가 표시되면 iPhone의 Wi-Fi와 Bluetooth를 켜고 페어링합니다.

HMG-API가 응답하지 않으면 내비게이션을 재부팅하고 같은 USB에서 Korea Projection 설치를 다시 선택합니다. 다른 Korea Projection 패키지나 별도로 설치한 무선 모드가 있다면 기존 패키지의 제거 순서를 확인하세요. 합본을 제거할 때는 Korea Projection을 먼저 제거합니다. [Korea Projection 이식 소스와 제거 안내](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb)

A3000mini가 외부 OHCI 포트에서 12Mbps로 잡히면 EHCI 소유권 반환 1회, 실패 시 외부 OHCI/EHCI 재초기화 1회를 부팅당 자동 시도합니다. v0.1.17은 OHCI를 해제한 상태에서 EHCI의 A3000mini가 실제 480Mbps·구성 완료로 준비될 때까지 최대 12초 기다린 뒤 OHCI를 복원합니다. Korea Projection의 NEMESIS 드라이버 호출 제한은 90초입니다. 대상 범위 확인 및 오류/신호 시 복원 처리는 유지합니다. 제어 파일 부재·열거 실패·복구 전후 커널 기록은 `speed.log`에 저장합니다. 드라이버 업데이트 뒤에는 A3000mini를 꽂은 채 내비를 완전히 재부팅하고 약 2분 기다립니다. 실차의 480Mbps 전환은 확인이 필요하며, 실제 속도 480 확인 뒤에만 AP를 시작합니다. 호스트 재등록은 물리 VBUS 차단을 보장하지 않습니다.

v0.1.11의 무선 모드는 AP 준비 신호와 `rtwlan0`의 AP 주소를 모두 확인한 뒤 Bluetooth iAP2를 시작합니다. 먼저 연결된 iPhone은 최대 약 3분간 AP를 기다립니다. 대기가 끝나도 AP가 준비되지 않았다면 준비 완료 후 iPhone Bluetooth를 껐다 켜 재연결합니다. A3000mini를 연결한 뒤 Korea Projection이 무선 모드를 **2.4.10로 업데이트·적용된 것을 확인하고** 내비게이션을 완전히 재부팅합니다. 첫 재부팅 뒤에 모드 업데이트 안내가 나왔다면 업데이트를 마친 뒤 다시 재부팅해야 새 훅이 적용됩니다.

v0.1.12는 `rtwlan0`의 차량 AP IPv4 대역과 IPv6 링크 로컬 대역에서 동적 TCP 포트를 허용합니다. 기존 모드 업데이트 후에는 소유한 무선 모드의 변경만 있는지 확인해 자동 적용합니다. 다른 모드 변경이나 오류가 함께 있으면 HMG-API 확인 안내가 표시됩니다. HMG-API 본체를 별도로 재설치할 필요는 없습니다.

준비 완료 화면에는 **Wi-Fi 접속 단말 수**가 표시됩니다. hostapd 인증 목록을 우선 사용하고, 지원되지 않으면 Realtek 연결 테이블로 집계합니다. 두 경로를 모두 읽지 못하면 **확인 불가**로 표시합니다. 연결한 뒤 다음 점검 주기(약 30초)에 숫자가 갱신됩니다. `perf.log`의 `sta_source=hostapd-authorized`는 인증 목록, `realtek-associated`는 드라이버 연결 상태, `unavailable`은 조회 실패를 뜻합니다. 단말 수가 늘어도 카플레이 세션 완료 여부는 별도로 확인해야 합니다.

v0.1.13은 IPv6 UDP 6031을 추가 허용하고 **실제 무선 카플레이 세션 시작**을 연결 판정 기준으로 사용합니다. AP 준비, Wi-Fi 단말 수 증가, 세션 생성만으로 연결됨이라고 표시하지 않습니다. 세션 종료·AP 변경·DiPO 프로세스 종료 뒤에는 이전 연결 표시를 사용하지 않습니다. 상태와 logcat 대체 수집은 보통 다음 30초 점검에 반영됩니다.

## 부팅과 재장착 기록 보내기

1. A3000mini를 꽂은 채 내비게이션을 완전히 재부팅하고 약 2분 기다립니다. 첫 시도에는 Realtek Launch를 누르지 않습니다.
2. 대기 문구나 AP 시작 오류가 계속되면 같은 부팅에서 동글을 한 번 재장착합니다. 필요하면 Realtek Launch를 한 번 누르고 Korea Projection 상태를 확인합니다.
3. 재부팅하기 전에 동글을 빼고 USB 메모리를 연결합니다. **NEMESIS → My Packages → Korea Projection CN7NPE USB Test → Launch → 제보 파일 만들기**를 선택합니다. `KoreaProjection-report`의 `3-log.txt`와 함께 생성된 `1-report.md`, `2-car-report.json`을 확인합니다.

`3-log.txt`의 `speed.log`에는 EHCI 복구 요청과 실제 480Mbps 확인 결과가 들어갑니다. `usb-ap-up-boot.log`와 `usb-ap-up-replug.log`는 같은 부팅의 첫 USB 장치와 USB 장치 번호가 바뀐 뒤의 UP 시도를 기록합니다. 자동 USB 복구에 따른 재열거도 장치 번호가 바뀔 수 있습니다. 각 파일에서 부팅 ID, USB 포트·장치 번호, USB 속도(`usb_speed_mbps`), UP 종료 코드, 전후 커널 로그를 확인할 수 있습니다. `12`는 full-speed, `480`은 high-speed 연결 기록입니다. `usb-hostapd-permissions-*.log`에는 실제 프로세스의 UID·권한·SELinux 컨텍스트가 들어가며, 프로세스가 먼저 종료되면 읽지 못했음을 표시합니다. `usb-hostapd-logcat-*.log`에는 해당 프로세스의 종료 코드와 AP 시작·단말 접속·실패 로그가 들어갑니다. 제보를 위해 동글을 빼고 USB 메모리로 바꾼 뒤에는 현재 상태가 AP lost로 표시될 수 있으므로, 같은 부팅에서 앞서 기록한 UP·AP 시작 결과를 함께 확인합니다.

ARM 모듈과 USB 패키지 구조를 검증했습니다. 실차에서 부팅 인식과 무선 카플레이 연결을 확인하는 진단판입니다.

[합본 변경 이력](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/cn7npe-usb-bundle-v0.1.18/CHANGELOG.md) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md#53-install-on-the-unit)

## v0.1.13 연결 진단

`3-log.txt`에 아래 항목을 자동 포함합니다. 별도 셸 명령이나 수동 logcat 수집은 필요하지 않습니다.

- `usb-carplay-events.log`: `created`(생성), `started`(실제 무선 세션 시작), `finalized`(종료), `wired`(유선) 및 Bluetooth 전환 기록. `started`도 화면·음성 정상 동작까지 보장하는 검사는 아닙니다.
- `usb-cp-capture.log`: logcat 수집 종료 코드. 권한·시간 초과로 수집하지 못한 경우 확인할 수 있습니다.
- `usb-connection-first.log`, `usb-connection-latest.log`: 같은 부팅의 첫/최근 AP·단말/세션 변화 때 방화벽, mDNS 서비스 조회 및 TCP 상태 스냅샷. 연결 대기 중에는 제한된 횟수로 재측정합니다.

`HMGAPI_input_jump_position`·`output_jump_position`이 `missing`이면 해당 진입 규칙을 관측하지 못한 것입니다. `1`이어도 뒤의 예외 규칙, 포트와 실제 카운터를 함께 확인해야 합니다. `IPv6_UDP6031_scoped_*_entries`는 커널에 관측된 해당 규칙 개수이며 카플레이 연결 여부와 별개입니다. `mdns ... query=failed`는 조회 자체가 실패한 경우이고, `matched_records=0`은 관측 창에서 응답을 확인하지 못했다는 뜻입니다.

동글을 뺀 뒤 현재 상태가 미연결로 바뀌어도 같은 부팅의 콜백·직전 스냅샷은 남습니다. 재부팅하기 전에 제보 파일을 만들어 주세요.

## v0.1.14 세션 전환 확인

Korea Projection만 설치/업데이트하고, 무선 모드 **2.4.10**이 업데이트·적용된 것을 확인한 뒤 내비게이션을 완전히 재부팅합니다. 첫 재부팅 뒤 모드 업데이트가 진행됐다면 적용 완료 후 한 번 더 재부팅해야 새 훅이 적용됩니다. HMG-API 본체나 Realtek을 별도로 재설치할 필요는 없습니다.

A3000mini를 꽂은 채 부팅하고 약 2분 기다린 뒤 연결을 시도합니다. 연결되면 3분 이상 화면·음악이 유지되는지 확인합니다. 같은 부팅에서 동글을 뽑거나 Realtek Launch를 누른 시각을 메모하고, 재부팅 전에 제보 파일을 저장합니다.

`3-log.txt`의 HMG-API 기록에서 `USB_CP_ORIGIN raw_transport=0 ... confirmed_bt_usb_ap=true wireless=true`, `USB_CP_HANDOVER stage=spp-down-preserved`, `stage=requested`, `stage=component5-connected` 순서를 확인합니다. 컴포넌트 5 연결은 iAP2 서버 연결 알림이며 프로토콜 식별·화면·음성 정상 동작까지 보장하는 표시는 아닙니다. 이관 전송 실패·취소도 같은 로그에 남습니다. 기존 방화벽·mDNS 스냅샷과 실제 세션 이벤트는 계속 제보 파일에 포함됩니다.

이전 릴리즈와 설치 ZIP도 GitHub에 보존합니다. 이전 버전으로 내리는 작업은 이번 업데이트 설치 절차와 별개입니다.

## v0.1.15 USB 12Mbps 복구 확인

Korea Projection만 설치/업데이트하고 NEMESIS 설치 계획에 **Realtek 1.1.14**가 포함됐는지 확인합니다. 같은 USB에서 의존성을 먼저 업데이트합니다. 설치 완료 후 A3000mini를 꽂은 채 내비게이션을 완전히 재부팅합니다. 무선 모드 **2.4.10**은 그대로 유지되며 HMG-API 본체는 별도로 재설치할 필요가 없습니다.

Realtek Launch를 누르거나 동글을 재장착하기 전에 약 2분 기다립니다. `speed.log`의 `repairing mode to 0755`, `EHCI ownership request exit=0`, `Verified usb=... speed_after=480` 기록으로 실제 복구를 구분합니다. 실행 권한이 이미 있거나 처음부터 USB 480Mbps인 경우에는 권한 복구/속도 복구 기록이 없을 수 있습니다. USB 480Mbps는 실제 Wi-Fi 전송 속도 480Mbps를 뜻하지 않습니다.

여전히 USB 12Mbps 대기라면 같은 부팅에서 제보 파일을 만든 뒤 `3-log.txt`와 Realtek의 `speed.log`, `boot.log`, `launch.log`(있는 경우)를 보내 주세요. `speed.log`에 새 권한·SELinux·마운트 정보가 포함됩니다. 실차에서 물리 재열거가 성공하는지는 별도 확인이 필요합니다. 이전 릴리즈·태그·ZIP은 GitHub에서 유지합니다.

## v0.1.17 외부 USB 호스트 재초기화 시험

Korea Projection만 설치/업데이트하고 설치 계획에 **Realtek 1.1.16**가 포함되는지 확인합니다. 설치를 마친 뒤 A3000mini를 직결한 채 내비게이션을 완전히 재부팅합니다. 첫 시험에는 재장착이나 Realtek Launch를 누르지 않고 약 2분 기다립니다.

부팅 시 12Mbps라면 첫 소유권 반환을 시도하고, 계속 12Mbps면 외부 플랫폼 호스트를 EHCI 우선 순서로 재초기화합니다. 동글만 연결된 단일 포트와 유일한 외부 컨트롤러 쌍을 확인해야 하므로 허브·다른 장치·활성 인터페이스·제어 파일 미지원 상태에서는 새 단계를 거부합니다. 컨트롤러가 다시 등록되면서 USB 버스 번호나 장치 번호가 바뀌거나 재사용될 수 있습니다.

`speed.log`에서 `Recovery stage=external-host-restart EHCI-first`, `USB cold recovery: validated`, `restore ehci-platform ... result=1`, `restore ohci-platform ... result=1`, 이어서 `Verified usb=... speed_after=480` 순서를 확인합니다. restore의 result=1은 바인딩 복원 성공이며 실제 속도 성공은 마지막 speed_after=480으로 판단합니다. request_exit=0만으로 480Mbps라고 판단하지 않습니다.

속도 대기가 계속되면 **재부팅 전에** 제보 USB로 바꾸고 제보 파일을 만듭니다. `3-log.txt`와 Realtek `speed.log`, `boot.log`, `launch.log`(있는 경우)를 보내 주세요. 컨트롤러 복원 실패가 기록되면 내비게이션을 완전히 재부팅해 정상 바인딩 복원을 확인합니다. 드라이버 재등록은 물리 전원 차단을 보장하지 않으며 실차의 480Mbps 전환 성공은 확인이 필요합니다. 12/480Mbps는 USB 버스 인식 속도입니다.

## v0.1.18 HMG-API rc.7 업데이트

Korea Projection **1.7.4.23**의 설치/업데이트만 선택하면 HMG-API 본체 **1.1.0-rc.7**(NEMESIS **1.0.99.7**) 이상이 필요하다는 의존성에 따라 같은 USB의 공식 패키지가 먼저 설치됩니다. Realtek **1.1.16**과 RTL8812BU용 무선 모드 **2.4.10**, rtwlan0·EHCI 복구·방화벽·카플레이 세션 처리는 v0.1.17과 동일합니다. 공식 무선 모드 2.2.0-rc.8은 이 합본에 넣지 않습니다.

설치를 마친 뒤 A3000mini를 꽂고 Korea Projection 상태 화면의 **지금 재부팅**을 눌러 새 본체 런타임을 적용합니다. HMG-API 앱에서 **1.1.0-rc.7**, 훅 활성 상태와 기존 무선 모드 **2.4.10**을 확인합니다. 기존 차량 로컬 지도(`state/local-map.json`)와 모드/설정은 본체 업데이트 시 보존되는 구조입니다. CN7PE 지도는 CN7NPE 전용 지도로 간주하지 않습니다. 훅이 꺼져 있으면 상태 화면의 지도 확인 결과를 함께 제보해주세요.

rc.7의 문제 기록은 **HMG-API → Logs → Record a problem**에서 시작하고 증상 재현 후 종료합니다. 12Mbps 복구 분석에는 Korea Projection 제보 파일과 Realtek `speed.log`도 함께 보내주세요. 이번 본체 교체만으로 실제 USB 480Mbps 전환이나 카플레이 연결이 검증된 것은 아닙니다.
