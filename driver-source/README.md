# RTL88x2BU 대응 소스

## USB 합본 v0.1.15: EHCI 도구 실행 권한 복구

Realtek **1.1.14**는 [common.sh](../package/scripts/common.sh)의 high-speed 경로가 실행 권한 확인 없이 helper를 호출하던 누락을 수정합니다. 해당 파일이 정상 패키지 파일인지 확인하고 필요할 때 `0755`로 복구한 후 시도 마커를 만듭니다. 실행 준비 실패는 하드웨어 시도 횟수로 세지 않습니다. 실제 480Mbps 재열거 확인·부팅당 최대 두 번·기존 native 도구의 장치/컨트롤러 범위는 유지합니다. 권한을 복구해도 실행을 거부하면 진단 정보를 남기며 SELinux/noexec 정책은 변경하지 않습니다.

[실행 비트 손실 재현 및 22개 회귀 검사, EHCI 조건 검사와 Android API 19 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44668325705). [권한 회귀 검사](../tests/test_usb_recovery_permissions.py). 커널 모듈과 native 복구 도구는 이전 버전과 동일하며, 도구 SHA-256은 `d74f898158c27e2999148343f23cf23d3ff0a2a49811dd8808bc9ef0081a6d1e`입니다. 실제 차량의 12→480Mbps 전환 및 Wi-Fi 처리량 개선은 아직 검증되지 않았습니다.

## USB 합본 v0.1.10 USB 속도 복구 도구

Realtek **1.1.13**에 포함한 `usb-reset-a3000mini`의 `--high-speed` 명령은 직결 A3000mini, USB 12Mbps, 단일 포트의 외부 OHCI와 비어 있는 EHCI 컨트롤러를 확인합니다. 대상 EHCI의 `companion` 파일에 `-1`을 써 포트 소유권을 되돌리고, 로더가 재열거 후 실제 속도를 검사합니다. 인터페이스가 이미 UP이면 도구는 요청을 거부합니다.

제어 방식은 Linux 3.18의 `store_companion()`와 `set_owner()`를 따릅니다. [EHCI sysfs 소스](https://github.com/torvalds/linux/blob/v3.18/drivers/usb/host/ehci-sysfs.c) · [포트 소유권 소스](https://github.com/torvalds/linux/blob/v3.18/drivers/usb/host/ehci-hub.c)

[Android 빌드와 조건 검사](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44475139056) · [복구 도구 소스](usb_reset_a3000mini.c) · [조건 검사](test_usb_speed.py)

## USB 합본 v0.1.9 진단 모듈

Realtek **1.1.12**의 모듈은 아래에 기록된 Gen5W 소스에 [칩 초기화 진단 패치](chip-init-diagnostics.patch)를 적용해 빌드했습니다. HALMAC·펌웨어 초기화 실패와 네트워크 장치를 올리다 실패한 지점에 `88x2bu: Gen5W chip-init failed` 로그를 남깁니다. HALMAC 내부의 전원 켜기, 펌웨어 다운로드, MAC·PHY 초기화 실패는 `Gen5W halmac failed stage=...`와 상태 코드로 기록합니다. 실패 반환값은 기존 코드와 같습니다.

[빌드 워크플로](../.github/workflows/build-gen5w-diagnostics.yml)는 두 모듈의 vermagic과 외부 심볼 목록을 GRT47 v2.0.7 바이너리와 대조합니다. [릴리스용 드라이버 빌드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44472253936)

| 모듈 | SHA-256 |
| --- | --- |
| `88x2bu.ko` (TCC803x) | `9c87432954becc5ee30a745feaf818af6864134b70256ccd466cebfd42f118c7` |
| `88x2bu_tcc897x.ko` (TCC897x) | `4b6dfd6b2f8148ea89bbcd12f9a36da7e3b0f736a5ffe563514dd4e44444795c` |

동글 분리 시 Gen5W의 정지 처리 경로에서 `rtw_os_ndevs_unregister()`를 호출해 이전 네트워크 장치 등록을 해제합니다. 재장착 뒤 중지된 `rtwlan0`을 현재 장치로 판정하는 경로를 수정했습니다. 이 변경의 실차 재연결 검증이 필요합니다.

## Gen5W 기반 모듈과 재빌드

이 디렉터리는 NEMESIS RTL8812BU 패키지 v1.1.1에 포함된 두 ARM 모듈의 GPL-2.0 대응 소스와 빌드 설정을 제공합니다.

| 파일 | 내용 |
| --- | --- |
| [rtl88x2bu-source.tar.gz](rtl88x2bu-source.tar.gz) | Gen5W 패치가 적용된 드라이버 전체 소스 및 GPL-2.0 라이선스 |
| [config_tcc803x.txt](config_tcc803x.txt) | TCC803x 커널 설정 |
| [config_tcc897x.txt](config_tcc897x.txt) | TCC897x 커널 설정 |
| [rebuild.sh](rebuild.sh) | 입력 버전을 고정한 ARM 모듈 재빌드 및 비교 스크립트 |

재빌드는 빈 Ubuntu 22.04 환경에서 실행합니다. `bc`, `bison`, `flex`, `kmod`, `libelf-dev`, `libc6-i386`, GCC, make, Python 3, curl, unzip이 필요합니다. 스크립트가 `/opt/src`와 `/opt/arm-eabi-4.7`에 작업 디렉터리를 만들고, 결과는 현재 작업 폴더의 `verification-output/`에 저장합니다.

```sh
bash driver-source/rebuild.sh
```

빌드 입력은 드라이버 커밋 `04ed7009bac4b235fe1880ba29e23159f49a6121`, GRT47의 v2.0.7 커널 빌드 스크립트와 설정, Linux 3.18.24, AOSP ARM GCC 4.7입니다. [드라이버 원본](https://github.com/cilynx/rtl88x2bu/tree/04ed7009bac4b235fe1880ba29e23159f49a6121) · [Gen5W 빌드 입력](https://github.com/GRT47/HKG_5W_USB_Wlan/tree/bcfe084b198475c6edf138b8ee8e080bb48b7902/package_usbwifi_hotspot/kernel_build)

기반 모듈 두 개의 `srcversion`은 `A8402F29F362DF030025EE3`입니다. 원본과 재빌드 파일을 비교했을 때 ELF 섹션의 차이는 컴파일 날짜·시각 문자열과 GNU 빌드 ID였습니다. v1.1.1 배포에는 아래 해시의 원본 모듈을 담았습니다. [재빌드 기록](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44081118324)

| 모듈 | SHA-256 |
| --- | --- |
| `88x2bu.ko` | `19b256a2710ea8613ce1018ec214131b30f71d4a075eebaeb25c2d4e29d2f7e7` |
| `88x2bu_tcc897x.ko` | `370bee146497a743cd0e70b7432cec83a18ca12ccc11cf21edb168d2c6e79dc0` |
