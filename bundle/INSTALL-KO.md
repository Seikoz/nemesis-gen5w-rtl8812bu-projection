# 아반떼 CN7PE·CN7HEVPE·CN7NPE 260902 USB 합본 설치

대상은 국내형 아반떼 CN7PE, 아반떼 하이브리드 CN7HEVPE, 아반떼 N CN7NPE의 `V039.001.260902` Gen5W(TCC803x), ipTIME A3000mini(`0bda:b812`)입니다. CN7HEVPE는 실차 시험 대상입니다. NEMESIS Manager **1.16.7 이상**의 USB Package Store를 사용합니다.

- Korea Projection CN7PE / CN7HEVPE / CN7NPE BETA **1.7.4.44** — 설치·AP·연결 관리 및 무선 CarPlay 곡 전환 진단
- HMG-API Wireless Mode **2.4.25** (CN7PE·CN7NPE) / **2.4.26** (CN7HEVPE) — HMG-API 안의 무선 모드 (공식 2.2.0-rc.8 기반 USB 이식판)
- Realtek Wi-Fi Driver **1.1.19** — RTL8812BU 무선랜 드라이버
- HMG-API 본체 **1.1.0-rc.8**, NEMESIS 패키지 버전 **1.0.99.8**. [공식 릴리스](https://github.com/Open-HMG/HMG-API/releases/tag/v1.1.0-rc.8)

## 설치 및 업데이트

1. 합본 ZIP을 FAT32 USB 메모리 최상위에 풉니다. `NEMESIS.data`와 `packages` 폴더가 루트에 있어야 합니다. `packages` 안의 ZIP 세 개는 압축 상태로 둡니다.
2. 주차 상태에서 USB 메모리를 내비게이션 데이터 USB 포트에 꽂습니다. **NEMESIS → Package Store → USB → Korea Projection CN7PE / CN7HEVPE / CN7NPE BETA**를 선택하고 **Install** 또는 **Update**를 누릅니다.
3. 설치 계획을 승인합니다. HMG-API rc.8과 Realtek Wi-Fi Driver 1.1.19가 필요한 경우 NEMESIS가 먼저 설치하거나 업데이트합니다. 기존 Korea Projection BETA `1.7.4.1`~`1.7.4.43`은 업데이트할 수 있습니다.
4. USB 메모리를 빼고 A3000mini를 꽂습니다. HMG-API 무선 모드 적용·재부팅 안내를 따릅니다. Korea Projection에 **USB Wi-Fi AP ready (rtwlan0)**가 표시되면 iPhone의 Wi-Fi와 Bluetooth를 켜고 연결합니다.

CN7NPE 오디오 보정은 **HMG-API Wireless Mode 2.4.25**에 포함됩니다. 예전 오디오 테스트 항목을 이미 삭제한 차량도 같은 Korea Projection 업데이트를 설치하면 보정을 받을 수 있습니다. 음악을 재생해 차량 스피커를 확인하고, 제보에서는 `cn7npe-rtwlan0-carrier: applied`를 확인합니다.

CarPlay HUD를 시험할 때는 HMG-API에서 **Phone Projection TBT**를 끄고 **Wireless Mode → Turn-by-turn on the cluster and HUD**를 켠 뒤 재부팅합니다. CarPlay 지도 앱으로 경로를 시작해 다음 회전 방향과 거리가 HUD에 표시되는지 확인합니다. 제보에서 `CarPlay: route guidance Start-only result=`와 `CarPlay: first HUD turn submitted`를 확인할 수 있습니다.

## 무선 곡 전환 무음 시험

1. 주차 상태에서 **HMG-API Wireless Mode → CarPlay's own log (troubleshooting)**를 켜고 재부팅합니다.
2. 무선 CarPlay가 연결되면 가능한 한 초기에 같은 다운로드 곡을 재생하고, 전환 사이에 몇 초를 두고 다음 곡을 세 번 눌러 봅니다. 제목이 바뀐 시각, 무음 길이, 새 곡이 들리기 시작한 시각을 기록합니다.
3. 마지막 곡 전환 뒤 약 1분 기다린 다음 제보 USB로 교체해 **제보 파일 만들기**를 실행합니다. `3-log.txt`의 `usb-carplay-audio.log`에 얻을 수 있었던 음악 정보 갱신, 버퍼 비우기, AAC 디코딩 시작, 출력 버퍼 고갈 신호와 초기 출력 스레드 상태가 들어갑니다. 이 로그는 스피커에서 실제로 소리가 나온 시각을 측정하지 않습니다.

HMG-API가 응답하지 않으면 내비게이션을 재부팅하고 같은 USB에서 Korea Projection 설치를 다시 선택합니다. 다른 Korea Projection 패키지나 별도로 설치한 무선 모드가 있다면 기존 패키지의 제거 순서를 확인하세요. 합본을 제거할 때는 Korea Projection을 먼저 제거합니다. [Korea Projection 이식 소스와 제거 안내](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb)

A3000mini가 외부 OHCI 포트에서 12Mbps로 잡히면 EHCI 소유권 반환 1회, 실패 시 외부 OHCI/EHCI 재초기화 1회를 부팅당 자동 시도합니다. v0.1.17은 OHCI를 해제한 상태에서 EHCI의 A3000mini가 실제 480Mbps·구성 완료로 준비될 때까지 최대 12초 기다린 뒤 OHCI를 복원합니다. Korea Projection의 NEMESIS 드라이버 호출 제한은 90초입니다. 대상 범위 확인 및 오류/신호 시 복원 처리는 유지합니다. 제어 파일 부재·열거 실패·복구 전후 커널 기록은 `speed.log`에 저장합니다. 드라이버 업데이트 뒤에는 A3000mini를 꽂은 채 내비를 완전히 재부팅하고 약 2분 기다립니다. 실차의 480Mbps 전환은 확인이 필요하며, 실제 속도 480 확인 뒤에만 AP를 시작합니다. 호스트 재등록은 물리 VBUS 차단을 보장하지 않습니다.

v0.1.11의 무선 모드는 AP 준비 신호와 `rtwlan0`의 AP 주소를 모두 확인한 뒤 Bluetooth iAP2를 시작합니다. 먼저 연결된 iPhone은 최대 약 3분간 AP를 기다립니다. 대기가 끝나도 AP가 준비되지 않았다면 준비 완료 후 iPhone Bluetooth를 껐다 켜 재연결합니다. A3000mini를 연결한 뒤 Korea Projection이 무선 모드를 **2.4.10로 업데이트·적용된 것을 확인하고** 내비게이션을 완전히 재부팅합니다. 첫 재부팅 뒤에 모드 업데이트 안내가 나왔다면 업데이트를 마친 뒤 다시 재부팅해야 새 훅이 적용됩니다.

v0.1.12는 `rtwlan0`의 차량 AP IPv4 대역과 IPv6 링크 로컬 대역에서 동적 TCP 포트를 허용합니다. 기존 모드 업데이트 후에는 소유한 무선 모드의 변경만 있는지 확인해 자동 적용합니다. 다른 모드 변경이나 오류가 함께 있으면 HMG-API 확인 안내가 표시됩니다. HMG-API 본체를 별도로 재설치할 필요는 없습니다.

준비 완료 화면에는 **Wi-Fi 접속 단말 수**가 표시됩니다. hostapd 인증 목록을 우선 사용하고, 지원되지 않으면 Realtek 연결 테이블로 집계합니다. 두 경로를 모두 읽지 못하면 **확인 불가**로 표시합니다. 연결한 뒤 다음 점검 주기(약 30초)에 숫자가 갱신됩니다. `perf.log`의 `sta_source=hostapd-authorized`는 인증 목록, `realtek-associated`는 드라이버 연결 상태, `unavailable`은 조회 실패를 뜻합니다. 단말 수가 늘어도 카플레이 세션 완료 여부는 별도로 확인해야 합니다.

v0.1.13은 IPv6 UDP 6031을 추가 허용하고 **실제 무선 카플레이 세션 시작**을 연결 판정 기준으로 사용합니다. AP 준비, Wi-Fi 단말 수 증가, 세션 생성만으로 연결됨이라고 표시하지 않습니다. 세션 종료·AP 변경·DiPO 프로세스 종료 뒤에는 이전 연결 표시를 사용하지 않습니다. 상태와 logcat 대체 수집은 보통 다음 30초 점검에 반영됩니다.

## 부팅과 재장착 기록 보내기

1. A3000mini를 꽂은 채 내비게이션을 완전히 재부팅하고 약 2분 기다립니다. 첫 시도에는 Realtek Launch를 누르지 않습니다.
2. 대기 문구나 AP 시작 오류가 계속되면 같은 부팅에서 동글을 한 번 재장착합니다. 필요하면 Realtek Launch를 한 번 누르고 Korea Projection 상태를 확인합니다.
3. 재부팅하기 전에 동글을 빼고 USB 메모리를 연결합니다. **NEMESIS → My Packages → Korea Projection CN7PE / CN7HEVPE / CN7NPE BETA → Launch → 제보 파일 만들기**를 선택합니다. `KoreaProjection-report`의 `3-log.txt`와 함께 생성된 `1-report.md`, `2-car-report.json`을 확인합니다.

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

## v0.1.18 HMG-API rc.7 + 무선 rc.8 USB 이식판

Korea Projection **1.7.4.23**만 설치/업데이트합니다. 필요한 HMG-API 본체 **1.1.0-rc.7**(NEMESIS **1.0.99.7**)가 먼저 갱신되고, 공식 무선 **2.2.0-rc.8** 기반 USB 이식판 **2.4.11**이 기존 합본 서명으로 업데이트됩니다. Realtek **1.1.16**과 EHCI 복구는 그대로입니다.

A3000mini를 꽂은 채 Korea Projection 상태 화면의 **지금 재부팅**을 누릅니다. HMG-API 앱에서 **1.1.0-rc.7 / 훅 활성**, 무선 모드 **2.4.11**을 확인합니다. 첫 재부팅 후 무선 모드 업데이트·적용 안내가 나오면 완료 후 한 번 더 재부팅하세요. 초기 시험에는 재장착/Realtek Launch 없이 약 2분 기다립니다.

기존 차량 로컬 지도는 `state/local-map.json`에 보존됩니다. 확인된 351개 지도와 맞지 않는 신규 8개 훅 선언은 제외하며, 새 다중 폰 제어·AA 주차는 등록하지 않습니다. 카플레이 주차 기능도 지도에 해당 점이 있어야 켜집니다. 이전 한국판 전용 `tbt_fit`·별표 팝업 건너뛰기는 이번 무선 모드에 이식하지 않았습니다. 공식 원본 ZIP을 따로 설치하면 기존 서명/USB AP 처리와 맞지 않으므로 이 합본에서 업데이트합니다.

실제 480Mbps·카플레이 연결 유지 여부는 차량에서 확인해야 합니다. 실패하면 Korea Projection 제보 파일과 Realtek `speed.log`, `boot.log`, `launch.log`를 함께 보냅니다. rc.7의 **Logs → Record a problem**도 사용할 수 있습니다. [호환성 검토](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/cn7npe-usb-bundle-v0.1.18/docs/compatibility-rc7-rc8-usb.md).

## v0.1.19 오디오 지원 파일 자동 적용

Korea Projection **1.7.4.24**만 Update합니다. HMG-API rc.7·무선 모드 2.4.11·Realtek 1.1.16은 v0.1.18과 같습니다. 설치 후 메모리를 빼고 A3000mini를 연결해 상태 화면을 엽니다.

이미 무선 모드 2.4.11이 설치됐어도 새 오디오 지원 파일이 적용되지 않았다면, 같은 합본의 소유 파일과 전체 설치 파일 해시·현재 적용 계획을 확인한 뒤 AP 시작 전에 자동 적용합니다. **“오디오 지원 파일을 자동 적용했습니다. 지금 재부팅을 눌러 주세요.”**가 나오면 반드시 **지금 재부팅**을 누릅니다. 같은 부팅에서 서비스를 다시 시작해도 재적용하지 않고 재부팅을 기다립니다. 적용할 파일이 이미 모두 맞으면 이 단계는 생략합니다.

다른 모드의 변경·문제·되돌리기, 고정한 모드, 수정되거나 다른 파일, 적용 실패가 있으면 자동 적용을 보류합니다. 이 경우 HMG-API 변경 사항을 직접 확인하고 `usb-audio-apply.log`, `usb-mod-files-check.log`, `mod-apply.txt`가 포함된 제보 파일을 수집합니다. 자동 재부팅은 하지 않습니다.

재부팅 후에는 재장착이나 Realtek Launch 없이 먼저 시험합니다. 이번 이전 로그에서는 수동 재장착 전에 이미 480Mbps·rtwlan0 준비를 통과했고, 이후 HMG-API 설정을 기다렸습니다. 새 로그의 **USB readiness passed**와 오디오 적용/모드 준비 단계를 구분해 확인합니다. 지원 파일을 적용한 뒤에도 멜론이 휴대폰에서 재생되면, 연결 직전부터 HMG-API **Logs → Record a problem**을 켜고 증상 재현 후 종료해 함께 보내주세요. 실제 무음 해소와 전체 자동 부팅 결과는 실차 확인이 필요합니다.

## v0.1.20 표시 이름 정리

Korea Projection **1.7.4.25**만 Update하면 드라이버 **1.1.17**과 무선 모드 **2.4.12**도 갱신됩니다. 설치 뒤 재부팅하고 모드 적용 안내가 나오면 완료 후 한 번 더 재부팅합니다. 기존 패키지를 먼저 제거할 필요는 없습니다.

| 표시 위치 | 이전 이름 | 새 이름 / 역할 |
| --- | --- | --- |
| NEMESIS USB 목록·My Packages | Realtek RTL8812BU USB Driver | **Realtek Wi-Fi Driver** — RTL8812BU 커널 드라이버 |
| HMG-API 모드 목록 | RTL8812BU USB Wireless (based on 2.2.0-rc.8) | **HMG-API Wireless Mode (USB)** — 카플레이/AA 무선 모드 |
| NEMESIS USB 목록·My Packages | HMG-API | **HMG-API** — 본체, 이름 유지 |

무선 모드는 HMG-API 본체와 별개입니다. 이름 갱신을 위한 버전 증가이며 커널 모듈·드라이버 스크립트·무선 훅·오디오 지원 파일·방화벽 동작은 v0.1.19와 같습니다. 패키지 ID와 기존 작성자 서명을 유지해 기존 설정과 업데이트 경로를 보존합니다. 이전 이름이 남으면 해당 위치의 버전이 위 버전으로 갱신됐는지 확인하세요.


## v0.1.21 이름 확정

- **HMG-API Wireless Mode 2.4.13**: 이전 이름에서 `(USB)`를 제거합니다.
- **Korea Projection CN7NPE BETA 1.7.4.26**: 이전 `Korea Projection CN7NPE USB Test`의 새 표시 이름입니다.
- **Realtek Wi-Fi Driver 1.1.17**, **HMG-API 1.1.0-rc.7**은 그대로입니다.

USB 목록에서 **Korea Projection CN7NPE BETA → Update**만 선택합니다. 기존 USB Test 이름과 새 BETA 이름을 모두 업데이트 대상으로 인정합니다. 기존 패키지·모드 ID와 작성자 서명을 유지하므로 먼저 제거할 필요가 없습니다. 설치 후 재부팅하고 모드 갱신/적용 안내가 나오면 완료 후 다시 재부팅합니다. 표시 이름·업데이트 버전만 바꾸며 무선 연결·오디오·드라이버 동작은 v0.1.20과 같습니다.

## v0.1.22 부팅 대기 단축 시험

Korea Projection CN7NPE BETA **1.7.4.27**로 Update합니다. 처음 설치했거나 모드·권한 복구가 필요한 부팅은 기존 확인 절차를 따릅니다. 기존 설정이 완료됐고 HMG-API 적용 계획·관리 파일 상태·지도 확인 기록이 맞으면, USB 480Mbps와 rtwlan0 준비 뒤 기존 120초 권한 복구 대기를 생략합니다.

A3000mini를 그대로 꽂고 재부팅합니다. 제보의 ap.log에서 USB 준비, `USB boot: existing wireless setup checked`, `USB AP ready` 시각을 비교합니다. 대기 경로를 탔다면 `using delayed HMG-API setup`과 `usb-boot-setup.log`를 확인합니다. 단축 시간은 차량에서 측정해야 합니다. 멜론 음악 출력은 별개로 시험합니다.

## v0.1.23 iAP2 전환 시험

Korea Projection CN7NPE BETA **1.7.4.28**로 Update한 뒤 무선 모드 **2.4.14**의 적용·재부팅 안내를 따릅니다. 무선으로 확인된 transport 0 세션은 Bluetooth SPP 종료 뒤 휴대폰의 CarPlay 채널 데이터를 최대 1.2초 기다립니다. 데이터가 오면 즉시 전달을 시작하고, 시간 안에 오지 않으면 차량 쪽에서 기존 전환을 요청합니다.

연결 전에 HMG-API **Logs → Record a problem**을 시작합니다. 멜론을 재생하고 아이폰에 차량 출력이 나타나는지, 차량 스피커에서 재생되는지 각각 확인합니다. 실패하면 기록 파일과 `3-log.txt`를 저장합니다. 무선 모드 설정에서 **CarPlay's own log (troubleshooting)**를 켠 뒤 재부팅해 비교하면, 수집 가능한 경우 순정 CarPlay의 스트림 협상 로그도 얻을 수 있습니다. 시험 뒤에는 이 설정을 끄고 로그 공유 전 기기 이름을 가립니다.

`first-peer-data`, `peer-wait-expired`, `first-native-send`와 `iAP2 connect success comp=5` 순서를 확인합니다. `component5-connected`는 연결 콜백이며, 식별 완료는 별도 단계입니다. 새 전환 순서의 효과와 실제 오디오 출력은 실차 확인이 필요합니다.

## v0.1.24 부팅 시간과 오디오 확인

A3000mini를 꽂은 채 **지금 재부팅**을 누릅니다. 제보 파일 `3-log.txt`의 `usb-boot-timing.log`에는 커널 부팅 후 각 단계가 처음 관측된 시간이 초 단위로 나옵니다.

| 항목 | 측정 지점 |
| --- | --- |
| service_start | Korea Projection 서비스 시작 |
| android_ready | Android 부팅 완료 확인 |
| usb_480_interface_ready | USB 480Mbps와 rtwlan0 준비 확인 |
| ap_prerequisites_ready | HMG-API 설정을 포함한 AP 시작 조건 통과 |
| ap_ready | hostapd와 DHCP 준비 |
| carplay_observed | 서비스 점검에서 시작된 무선 카플레이 세션을 최초 확인 |

동글 재장착이나 AP 재시작이 첫 기록을 덮어쓰지 않습니다. 설치한 직후에는 같은 부팅의 시간이 기록되므로 설치 후 재부팅해 비교합니다. 카플레이는 점검에서 확인한 시각이며 실제 연결 시각을 보려면 세션 이벤트를 확인합니다. 항목이 없으면 제보 때까지 관측되지 않았습니다.

오디오를 시험하기 전에 HMG-API Wireless Mode의 **CarPlay music and Siri over Wi-Fi (AAC, Opus)**가 켜져 있는지 확인합니다. 스트림 설정까지 기록하려면 같은 메뉴의 **CarPlay's own log (troubleshooting)**를 켜고 모드 안내에 따라 재부팅합니다. **Logs → Record a problem**을 연결 전에 시작하고, 같은 세션에서 멜론과 Apple 팟캐스트 같은 다른 앱을 차례로 재생합니다. 아이폰에 차량 출력이 나타나는지, 차량 스피커로 소리가 나는지, 재생 시각을 적어 주세요. 제보를 만든 뒤 로그 설정을 끄고 공유 전 기기 이름을 확인합니다.

## v0.1.25 CN7PE 설치 시험

내비 버전 정보가 `CN7PE.KOR.S5W_M.V039.001.260902`인지 확인합니다. NEMESIS가 이미 설치된 차량에서 FAT32 USB에 합본을 풀고 **Korea Projection CN7PE / CN7NPE BETA → Install**을 선택합니다. 기존 합본이 설치된 CN7NPE에서는 **Update**를 선택합니다.

설치 USB를 A3000mini로 교체합니다. CN7PE에서는 USB 준비 뒤 HMG-API의 CN7PE용 지도 확인을 통과해야 무선 설정을 진행합니다. 지도 확인에 실패하면 상태 화면에서 실패 이유를 확인하고 HMG-API **Car Report**와 Korea Projection 제보의 `usb-cn7pe-map.log`가 포함된 `3-log.txt`를 같은 부팅에서 저장하세요. 무선 모드 적용 후 재부팅 안내를 따릅니다.

CN7PE의 실제 자동 인식, 핫스팟, 무선 카플레이·안드로이드 오토 및 차량 오디오는 주차 상태에서 확인합니다. 설치 전에 차량의 버전이 위 범위와 일치하는지 확인하세요.


## v0.1.26 CN7HEVPE 하이브리드 시험

대상은 `CN7HEVPE.KOR.S5W_M.V039.001.260902` 국내형 Gen5W TCC803x와 A3000mini입니다. NEMESIS USB 목록에서 **Korea Projection CN7PE / CN7HEVPE / CN7NPE BETA → Install**을 선택합니다. 기존 합본 사용자는 **Update**를 선택합니다.

A3000mini를 꽂고 기다립니다. 하이브리드는 내비 자체 파일을 읽어 HMG-API 차량 지도를 생성한 뒤, 필요한 훅이 있으면 지도 검증을 거쳐 하이브리드용 무선 모드 **2.4.16**을 적용합니다. 첫 지도 생성에는 수분이 걸릴 수 있습니다. 화면에 재부팅 안내가 나오면 적용 후 재부팅합니다. 이미 있는 차량 지도는 검증해 사용합니다.

지도 확인에서 멈추면 같은 부팅의 **HMG-API Car Report**와 `usb-cn7hevpe-map.log`가 포함된 Korea Projection `3-log.txt`를 저장합니다. 하이브리드판은 무선 설정 페이지 대체와 카플레이 시작 시 Bluetooth 유지 훅 없이 시험합니다. 실차의 USB 인식, 무선 연결·유지, 차량 오디오는 확인이 필요합니다.

## v0.1.27 무선 카플레이 오디오 비교

1. Korea Projection을 **Update**하고 아반떼 N·일반형에서는 무선 모드 **2.4.17**이 적용될 때까지 재부팅 안내를 따릅니다.
2. 주차 상태에서 **HMG-API → HMG-API Wireless Mode → Stock Bluetooth handoff (CarPlay audio test)**를 켭니다. 오디오 스트림 로그도 필요하면 **CarPlay's own log (troubleshooting)**를 켭니다. 설정을 적용하고 내비게이션을 재부팅합니다.
3. A3000mini를 꽂은 상태에서 무선 카플레이를 연결합니다. 멜론, 내비 안내, 통화를 각각 시험하고 어느 스피커에서 나오는지, 아이폰에 차량이 출력으로 표시되는지, 연결이 유지되는지를 기록합니다.
4. 문제가 남으면 동글을 제보 USB로 교체하고 Korea Projection의 `3-log.txt`를 저장합니다. `usb-carplay-audio.log`에서 `bluetooth_handoff=stock`, 오디오 스트림 설정·오류와 오디오 우선권 요청을 확인할 수 있습니다. 원본 CarPlay 상세 로그가 필요하면 연결 전부터 HMG-API **Logs → Record a problem**도 사용합니다.
5. 대조 시험은 같은 메뉴에서 **Stock Bluetooth handoff**를 끄고 재부팅한 뒤 반복합니다. 시험 설정 기본값은 꺼짐입니다. 켠 상태에서 연결이 반복해서 끊기면 끄고 재부팅하세요.

전환 시험은 CN7PE·CN7NPE의 확인된 USB 무선 CarPlay 세션에 적용됩니다. 하이브리드 **2.4.18**에서는 새 제보 기록을 사용할 수 있습니다. `rtwlan0`의 패킷·드롭 카운터는 인터페이스 전체 통계이며 음성 패킷 자체의 손실률과는 별개의 수치입니다. 공유 전에 원본 로그에서 기기 이름과 주소를 가리세요.

## v0.1.28 iAP2 재전환과 오디오 제보

1. Korea Projection을 **Update**한 뒤 무선 모드 적용과 재부팅 안내를 따릅니다. 처음 비교할 때는 이전 시험과 같은 **Stock Bluetooth handoff** 설정을 사용합니다.
2. **HMG-API Wireless Mode → CarPlay's own log (troubleshooting)**를 켜고 안내에 따라 재부팅합니다. A3000mini를 꽂은 채 CarPlay를 연결하고, 멜론·안내·통화의 실제 출력을 시험합니다. 오디오 수집은 연결을 시작할 때부터 백그라운드에서 진행됩니다.
3. 재부팅하기 전에 Korea Projection 제보 `3-log.txt`를 저장합니다. `usb-carplay-audio.log`에서 `waiting-after-rc19`, `resume-on-peer`, `native-send-accepted`, `component5-ready` 및 오디오 스트림 설정 기록을 확인합니다. `native_rows=0`인 경우 그 스캔에서 순정 CarPlay 로그가 관측되지 않은 상태입니다. 원본 로그가 필요하면 HMG-API의 **Record a problem**도 함께 사용합니다.

터널 데이터가 늦게 도착하면 보존한 첫 패킷과 함께 iAP2 전환을 재개합니다. 데이터가 끝내 도착하지 않는 세션에는 화면을 유지한 채 대기 기록을 남깁니다. 차량 오디오 출력은 실차 확인이 필요합니다.

## v0.1.29 HT20 및 iAP2 협상 중 AP 재시작 보류

Korea Projection의 **Update**를 완료하고 새 무선 모드를 적용합니다. **HMG-API → HMG-API Wireless Mode**에서 두 옵션을 각각 바꿀 수 있습니다. 기본값은 둘 다 꺼짐입니다. 옵션을 바꿀 때마다 HMG-API의 **Apply changes**를 실행하고 헤드유닛을 재부팅합니다.

| 옵션 | 켰을 때의 동작 |
| --- | --- |
| **Channel 149 HT20 (USB AP test)** | `rtwlan0` 핫스팟의 5GHz 채널 149에서 채널 폭을 20MHz로 설정합니다. 끄면 HT40+ 설정을 사용합니다. |
| **Defer AP restart during iAP2 (90 s)** | 현재 USB AP에서 확인된 첫 Bluetooth iAP2 연결부터 최대 90초 동안, 순정 `softap.conf`의 SSID나 암호 변경 때문에 요청된 AP 재시작을 미룹니다. 협상이 끝나거나 기한이 지나면 보류 조건을 해제합니다. |

주차 상태에서 한 번에 한 옵션씩 켜고 같은 아이폰으로 CarPlay 화면, 음악·내비 안내·통화, 연결 유지 여부를 확인합니다. `3-log.txt`의 `ap.log`에는 `USB AP options`와 실제 설정 변경을 보류했을 때의 `USB AP restart deferred for Bluetooth iAP2`가 나옵니다. `usb-hostapd.log`의 시작 줄에서 HT20/HT40+를 확인합니다. USB 재열거와 AP 프로세스 종료는 기존 복구 절차로 처리합니다.

## v0.1.36 CarPlay 라이브러리 검사

Korea Projection **1.7.4.41**에서 제보 파일과 오디오 보정이 같은 MD5 검사 경로를 사용합니다. `3-log.txt`의 `libCarPlayCoreUtils.so.md5=`와 `libCarPlayCoreUtils.so.check=`에서 해시와 검사 도구의 종료 코드를 볼 수 있습니다. 해시가 맞으면 기존 조건에 따라 오디오 보정을 자동으로 설치하거나 적용합니다.

## v0.1.35 HMG-API rc.8 및 CN7NPE 오디오 시험

Korea Projection을 업데이트하면 필요한 경우 HMG-API 본체도 rc.8로 업데이트합니다. 합본의 Wireless Mode 2.4.21·2.4.22가 계속 `rtwlan0`의 USB AP를 사용합니다.

조건에 맞는 CN7NPE 260902는 오디오 보정 0.1.1을 자동 설치하거나 이전 0.1.0에서 갱신합니다. 내비게이션을 재부팅하라는 안내를 따른 뒤 HMG-API 화면의 **1.1.0-rc.8 / Hooks on**과 차량 스피커 출력을 확인합니다. 제보 `3-log.txt`의 `usb-carrier.log`와 `cn7npe-rtwlan0-carrier: applied`에서 보정 적용 여부를 확인할 수 있습니다.

## v0.1.34 CN7NPE 오디오 시험

Korea Projection이 A3000mini의 무선 모드를 준비한 뒤 순정 CarPlay 라이브러리의 해시를 확인합니다. CN7NPE 260902에서 해시가 일치하고 다른 HMG-API 변경이 없으면 포함된 오디오 보정이 자동으로 설치·적용됩니다. 재부팅 안내가 나오면 동글을 꽂은 채 안내를 따릅니다. 최초 설정 중 무선 모드와 오디오 보정 단계에서 각각 재부팅 안내가 나올 수 있습니다.

음악을 재생해 차량 스피커를 확인합니다. 제보 `3-log.txt`의 `usb-carrier.log`에는 설치·적용·보류 사유가 기록됩니다. `cn7npe-rtwlan0-carrier: applied`는 재부팅 뒤 CarPlay 메모리에서 보정이 적용된 기록입니다. 자동 설치한 모드는 Korea Projection을 제거할 때 정리됩니다.

## v0.1.33 CarPlay 라이브러리 확인

업데이트 후 제보용 USB를 꽂고 **NEMESIS → My Packages → Korea Projection → Launch → 제보 파일 만들기**를 누릅니다. `KoreaProjection-report/3-log.txt` 앞부분의 **CarPlay native library fingerprint**에서 `libCarPlayCoreUtils.so.md5=` 값을 확인할 수 있습니다. 이 항목은 내비의 `/system/lib/libCarPlayCoreUtils.so`를 읽어서 계산하므로 A3000mini를 뺀 상태에서도 기록됩니다. 파일 없음, 읽기 권한 없음, 계산 실패는 각각 `missing`, `unreadable`, `hash-failed`로 표시됩니다.

## v0.1.31 CarPlay 오디오 진단

**USB CarPlay trial history**의 `dipo_audio_focus`에 차량이 기록한 오디오 타입과 음악 우선권이 남습니다. `dipo_audio_mode`에는 기본 오디오 모드와 음악·전화·Siri 우선권이 기록됩니다. `native_iap_send_rows`는 최근 스캔에서 본 네이티브 iAP 송신 호출 로그 개수입니다. 전송 성공 여부는 `native-send-accepted` 등 iAP2 단계와 함께 확인합니다. 차량 스피커 출력 여부는 시험 결과에 별도로 적습니다.

## v0.1.30 A/B/C 로그 한 번에 내보내기

1. Korea Projection **1.7.4.35**로 업데이트합니다. 순정 오디오 협상 로그도 필요하면 첫 재부팅 전에 **HMG-API Wireless Mode → CarPlay's own log (troubleshooting)**를 켭니다.
2. A3000mini를 꽂은 채 **A 둘 다 끔 → B HT20만 켬 → C iAP2 재시작 보류만 켬** 순서로 시험합니다. 옵션을 바꿀 때마다 **Apply changes → 재부팅**합니다. 화면과 실제 소리 출력이 확인된 뒤 약 1분 동안 로그가 수집되도록 기다립니다. 연결이 실패했으면 시도 후 약 1분 기다립니다.
3. C 시험을 끝낸 뒤 재부팅 전에 동글 대신 제보 USB를 꽂습니다. **NEMESIS → My Packages → Korea Projection → Launch → 제보 파일 만들기**를 한 번 누릅니다. `KoreaProjection-report/3-log.txt`의 **USB CarPlay trial history**에 최근 8회 부팅의 옵션과 iAP2·오디오 진단이 모입니다.

같은 조건을 반복해도 부팅별로 저장하며 두 옵션을 모두 켠 시험은 D로 표시합니다. AP·터널 전환·오디오 설정·우선권 로그는 정해진 진단 항목만 저장합니다. 실제 소리가 차량과 아이폰 중 어디에서 나왔는지는 연결 시각과 함께 메모해 주세요.
