# RTL88x2BU 대응 소스

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

두 모듈의 `srcversion`은 `A8402F29F362DF030025EE3`입니다. 원본과 재빌드 파일을 비교했을 때 ELF 섹션의 차이는 컴파일 날짜·시각 문자열과 GNU 빌드 ID였습니다. 배포 ZIP에는 아래 해시의 원본 모듈을 담았습니다. [재빌드 기록](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/actions/runs/44081118324)

| 모듈 | SHA-256 |
| --- | --- |
| `88x2bu.ko` | `19b256a2710ea8613ce1018ec214131b30f71d4a075eebaeb25c2d4e29d2f7e7` |
| `88x2bu_tcc897x.ko` | `370bee146497a743cd0e70b7432cec83a18ca12ccc11cf21edb168d2c6e79dc0` |
