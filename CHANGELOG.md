# 변경사항

## 프로젝트 및 릴리스 운영

- 프로젝트 이름을 **NEMESIS RTL8812BU Gen5W**, 저장소 이름을 `nemesis-rtl8812bu-gen5w`로 정리했습니다.
- 릴리스 제목을 영문으로 통일하고 최신 합본이 GitHub에서 바로 보이도록 **Latest**로 등록합니다.
- 새 다운로드 검증 후 이전 릴리스와 태그를 정리하고, 버전별 변경 사항을 README와 이 문서에 기록합니다.

## USB 합본 v0.1.8

- v0.1.7 실차 로그에서 HALMAC 초기화 실패와 `rtwlan0` 활성화 실패가 반복됐고, `hostapd`의 `CAP_NET_ADMIN`과 `CAP_NET_RAW`는 유지된 것을 확인했습니다.
- Realtek **1.1.11**은 `rtw_power_mgnt=0`, `rtw_ips_mode=0`, `rtw_enusbss=0`으로 로드합니다. HALMAC의 전원 켜기, 펌웨어 다운로드, MAC·PHY 초기화 단계별 실패와 상태 코드를 제보 커널 로그에 추가합니다. 실차의 복구 여부는 확인이 필요합니다.
- 부팅 첫 USB 장치 기록에 사용한 `printf`를 차량 셸에서 지원하는 `echo`로 바꿨습니다. 부팅 직후와 USB 장치 번호 변경 후의 기록이 같은 파일로 합쳐지던 문제를 수정했습니다.
- Korea Projection **1.7.4.13**은 인터페이스 활성화 성공을 확인한 뒤 2초 기다렸다가 `hostapd`를 시작합니다. UP 실패 시의 기록은 `usb-ap-up-*.log`에 남기고 다음 서비스 점검에서 재시도합니다.
- HMG-API 본체 **1.1.0-rc.4**와 무선 모드 **2.4.6**을 동봉합니다. 배포에는 v0.1.8 USB 합본 ZIP과 해당 태그 한 개를 사용합니다.

## USB 합본 v0.1.7

- Realtek **1.1.10**의 Gen5W ARM 모듈에 RTL8822B의 HALMAC·펌웨어 초기화 실패 상태와 네트워크 장치 열기 실패를 커널 로그에 기록하는 코드를 추가했습니다. 두 모듈의 vermagic과 커널 심볼 의존성을 기존 모듈과 대조했습니다.
- Korea Projection **1.7.4.12**는 부팅 시 처음 감지한 USB 장치와 장치 번호 변경 뒤의 UP 시도를 별도 기록합니다. 각 기록에 서비스 권한, UP 종료 코드, 관련 USB·커널 메시지가 들어갑니다.
- `hostapd` 프로세스의 UID, Linux capabilities, SELinux 컨텍스트와 실패 직후의 Android 로그를 같은 USB 관측 기록과 연결해 `3-log.txt`에 포함합니다.
- 같은 부팅·USB 장치의 `Operation not permitted` 판별을 수정했습니다. HMG-API **1.1.0-rc.4**와 무선 모드 **2.4.6**을 포함합니다.
- GitHub 배포를 최신 USB 합본 ZIP 한 개로 정리하고, 이전 릴리스의 변경 이력을 이 문서에 보존합니다.
- 릴리스 태그를 v0.1.7로 정리했습니다. 설치 안내와 라이선스의 이식 소스는 원본 커밋으로 연결합니다. ZIP의 설치 안내와 소스 링크를 갱신해 SHA-256을 릴리스에 다시 기록했습니다.

## USB 합본 v0.1.6

- Korea Projection **1.7.4.11**이 `rtwlan0` 활성화 중 `Operation not permitted`를 감지하면 서비스 권한과 USB 식별을 확인합니다. 대상 A3000mini의 Realtek 드라이버 연결을 부팅당 한 번 갱신하고 활성화를 재시도합니다.
- 제보 파일의 `usb-ap-up.log` 항목에 `ifconfig` 결과, 서비스 권한, 관련 커널 메시지, 드라이버 재연결 결과를 기록합니다.

## USB 합본 v0.1.5

- NEMESIS 1.16.7이 이전 앱 폴더를 지운 뒤 새 설치 전 검사를 실행할 때, 남아 있는 Korea Projection 무선 모드 **2.4.6**이 정상 업데이트를 막던 조건을 수정했습니다. 기존 모드의 소유 기록과 식별 정보로 확인합니다.
- Korea Projection **1.7.4.10**에서 이전 합본의 업데이트와 v0.1.4 설치 실패 후 재시도를 지원합니다. `hostapd` 실패 시 제보 파일에 Android 로그를 남깁니다.

## USB 합본 v0.1.4

- Korea Projection **1.7.4.9**가 `hostapd` 실패 직후 해당 프로세스의 Android `logcat`을 수집합니다. SSID와 키를 가린 최근 오류를 `3-log.txt`의 `usb-hostapd-logcat.log` 항목에 포함합니다.
- HMG-API **1.1.0-rc.4**, Realtek **1.1.9**, Korea Projection 무선 모드 **2.4.6**을 포함합니다.

## USB 합본 v0.1.3

- HMG-API 본체를 공식 **1.1.0-rc.4**로 교체했습니다. NEMESIS에서 Korea Projection을 선택하면 rc.3 또는 그 이전 버전을 rc.4로 먼저 업데이트합니다.
- Korea Projection 패키지 **1.7.4.8**에 새 의존성과 기존 테스트판의 업데이트 조건을 반영했습니다. 기존 무선 모드 **2.4.6**과 Realtek **1.1.9**를 그대로 사용합니다.

## USB 합본 v0.1.2

- 차량 로그에 기록된 HMG-API 본체 **1.1.0-rc.3** 공식 빌드를 추가했습니다. Korea Projection **1.7.4.7**을 선택하면 NEMESIS가 필요한 HMG-API와 Realtek을 같은 USB에서 찾아 먼저 설치하거나 업데이트합니다.
- Korea Projection은 새로 설치된 HMG-API 데몬이 응답할 시간을 준 뒤 설치를 진행합니다.
- Realtek **1.1.9**는 패키지 이름으로 CN7NPE Korea Projection USB 테스트판을 식별합니다. 이전 드라이버와 동일한 커널 모듈과 USB 리셋 도구를 사용합니다.

## USB 합본 v0.1.1

- Korea Projection **1.7.4.6**이 Realtek **1.1.8 이상**을 요구하도록 NEMESIS 의존성을 선언했습니다. USB 탭에서 Korea Projection을 선택하면 NEMESIS가 필요한 드라이버를 같은 USB에서 찾아 먼저 설치하거나 업데이트합니다.
- Realtek **1.1.8**은 Korea Projection **1.7.4.6**을 USB 테스트판으로 인식합니다. v1.1.7의 커널 모듈과 USB 리셋 도구를 사용합니다.

## USB 합본 v0.1.0

- Korea Projection CN7NPE USB Test **1.7.4.5**와 Realtek 드라이버 **1.1.7**을 같은 USB 메모리에서 설치할 수 있는 합본 ZIP으로 제공했습니다.

## v1.1.7 (A3000mini 부팅 인식 테스트)

- NEMESIS 서비스 시작 시 모듈을 먼저 로드하고 Android 부팅 완료 후에도 인식을 재시도합니다. 서비스의 첫 시점과 각 시도 결과는 `preload.log`에 기록합니다.
- 아반떼 N CN7NPE `260902`에서 승인된 A3000mini(`0bda:b812`)가 드라이버에 연결되지 않으면 해당 USB 장치에만 리셋을 부팅당 한 번 요청합니다. Korea Projection과 드라이버 서비스가 모두 재시도하더라도 한쪽만 이 복구를 실행합니다.
- 복구를 실행한 시도의 `boot.log`에 `usb_device_reset`과 USB 설정 재적용 결과를 기록합니다. Korea Projection USB 테스트판 `1.7.4.5`의 기존 드라이버 호출과 호환됩니다.

## v1.1.6 (자동 Launch 테스트)

- Android 부팅 완료 후, 지원 동글이 USB에 잡혔지만 Wi-Fi 인터페이스가 아직 없으면 NEMESIS Manager의 Launch 버튼과 같은 `nemesis pkg-launch realtek.88x2bu`를 실행합니다.
- 부팅 서비스는 실행 상태를 유지합니다. 같은 동글에 최대 세 번 시도하고, USB가 새로 감지되거나 Wi-Fi 인터페이스가 살아났다 사라지면 다시 시도할 수 있습니다.
- 실행 결과는 `boot.log`에, 실제 Launch 스크립트의 결과는 `launch.log`에 기록합니다.

## v1.1.5 (부팅 테스트)

- 초기 로드 결과와 관계없이 Android 부팅 완료 뒤 드라이버 로드와 USB 연결 상태를 다시 확인합니다. 부팅 중 USB 장치가 다시 감지되는 경우에도 추가 기회를 제공합니다.
- 초기 단계는 USB 설정을 재적용하지 않습니다. Android 시작 뒤에도 동일한 A3000mini가 연결되지 않을 때만 기존의 부팅당 한 번 재시도를 사용합니다.
- 각 부팅 시도의 출력과 종료 코드를 NEMESIS 서비스의 `preload.log`에 남깁니다. 마지막 시도의 결과는 `boot.log`에 기록합니다.
- Korea Projection CN7NPE USB 테스트판 `1.7.4.1`을 일반 1.7.x 미지원 안내에서 제외합니다.

## v1.1.4

- NEMESIS 부팅 서비스에서 드라이버를 먼저 로드하고 USB 인식을 기다립니다.
- 부팅 시 `0bda:b812`가 계속 연결되지 않으면 승인된 단일 인터페이스 장치에 한해 현재 USB 설정을 부팅당 한 번 다시 적용합니다.
- 부팅 인식 시도와 USB 재설정 여부를 `boot.log`에 저장합니다. Korea Projection 1.7.4 이식에 필요한 변경도 README에 기록했습니다.

## v1.1.3

- 아반떼 N `260902`의 v1.1.2 실차 로그에서 A3000mini(`0bda:b812`)가 `rtl88x2bu`에 자동 연결되고 `rtwlan0`으로 등록된 것을 확인했습니다.
- Korea Projection 1.7.x가 설치된 경우 USB 드라이버의 인식 성공과 Korea Projection의 USB 미지원 상태를 각각 안내합니다. `launch.log`에는 설치된 Korea Projection 버전과 USB 지원 판정을 기록합니다.
- Korea Projection의 무선 모드 설치에는 해당 프로젝트의 USB 동글 지원이 필요합니다. [공식 지원 계획](https://github.com/StopDragon/korea-projection#usb-wi-fi-동글-180-준비-중)

## v1.1.2

- 아반떼 N `260902` 실차 로그에서 동글 `0bda:b812`와 모듈 등록은 확인됐지만 USB 인터페이스 `4-1:1.0`은 `unbound`였습니다. 자동 연결 뒤에도 인터페이스가 비어 있으면 USB ID와 클래스가 일치하는 동글에 한해 `rtl88x2bu` 연결을 한 번 재요청합니다.
- 동글을 꽂기 전에 **Launch**로 모듈을 먼저 올릴 수 있습니다.
- 로그에 `manual_bind`, USB 자동 연결 설정, 장치 승인 상태, 인터페이스 alias 및 엔드포인트 수를 추가했습니다. 기존 ARM 모듈을 사용합니다. 실차에서 연결 재시도 성공 여부는 확인 전입니다.

## v1.1.1

- 빌드 없이 FAT32 USB에 풀어 사용하는 설치 ZIP을 배포했습니다.
- GPL-2.0 라이선스와 재빌드로 대조한 모듈 대응 소스를 추가했습니다.

## v1.1

- USB 인터페이스 하위 경로 외에 시스템 네트워크 장치와 드라이버 정보를 함께 조회하도록 개선했습니다.
- Launch 실패 시 USB 드라이버 연결 상태와 커널 메시지를 기록하도록 추가했습니다.

## v1.0

- Gen5W `tcc803x` / `tcc897x`, Linux `3.18.24-tcc`용 `88x2bu` 모듈의 수동 로드와 제거를 추가했습니다.
