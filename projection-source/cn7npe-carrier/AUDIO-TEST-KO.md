# CN7NPE A3000mini 무선 CarPlay 오디오 시험

대상은 국내형 아반떼 N CN7NPE `V039.001.260902`, TCC803x, ipTIME A3000mini(`0bda:b812`)입니다. **CN7NPE USB CarPlay Audio Test 0.1.1**은 v0.1.35의 Korea Projection 패키지에 들어 있으며 HMG-API rc.8에서 설치·적용할 수 있습니다.

1. FAT32 USB 최상위에 합본 ZIP을 풉니다. 주차 상태에서 **NEMESIS → Package Store → USB → Korea Projection BETA 1.7.4.40 → Install 또는 Update**를 누릅니다.
2. 설치 USB를 빼고 A3000mini를 연결합니다. 무선 모드가 준비되면 Korea Projection이 라이브러리 해시를 확인하고 조건에 맞는 차량에서 보정 0.1.1을 설치하거나 기존 0.1.0을 갱신한 뒤 적용합니다. 재부팅 안내가 나오면 따라 주세요.
3. CarPlay가 연결되면 음악을 재생하고 아이폰의 출력 선택 및 차량 스피커를 확인합니다.
4. 시험 후 제보 USB를 다시 연결하고 Korea Projection의 **제보 파일 만들기**를 누릅니다. `3-log.txt`에서 `libCarPlayCoreUtils.so.md5=`, `usb-carrier.log`, `cn7npe-rtwlan0-carrier: applied` 또는 `Carrier skipped:`를 확인합니다. 적용 기록과 실제 스피커 출력 여부를 함께 보냅니다.

보정 모드는 CarPlay 프로세스에서 내비의 순정 `libCarPlayCoreUtils.so` MD5가 `cf3cc23dad25b181a9fc12d606468715`와 일치하고, A3000mini의 `rtwlan0` AP가 준비되면 메모리의 Wi-Fi 인터페이스 분류 항목을 변경합니다. AP 대기는 최대 240초입니다. 순정 파일은 읽기만 합니다. 해시나 메모리 검증이 맞지 않으면 적용을 건너뜁니다. CN7NPE의 실제 오디오 출력은 이번 시험에서 확인합니다.

오디오 보정만 원복하려면 HMG-API의 **Mods**에서 **CN7NPE USB CarPlay Audio Test**를 비활성화하거나 제거하고 **Apply changes** 후 내비게이션을 재부팅합니다. Korea Projection을 제거할 때는 합본이 직접 설치한 오디오 보정도 정리됩니다.

## 출처

보정 코드와 레시피는 사용자가 제공한 `CN7PE-260902-A3000MINI-All-in-One-1.0.0.zip`의 `sources/native-carplay-carrier`에서 가져와 CN7NPE용으로 수정했습니다. AGPL-3.0 라이선스와 변경 소스는 합본에 포함됩니다. [CN7PE 패키지의 기반 NEMESIS RTL8812BU Gen5W](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.30)
