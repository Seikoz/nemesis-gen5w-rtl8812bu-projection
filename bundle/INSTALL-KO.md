# 아반떼 Gen5W USB 합본 설치

**v0.1.41**은 국내형 아반떼 CN7PE, 하이브리드 CN7HEVPE, N CN7NPE의 **V039.001.260902** Gen5W(TCC803x)를 대상으로 합니다. NEMESIS Manager **1.16.7 이상**이 필요합니다. 합본에는 Korea Projection **1.7.4.46**, Wireless Mode **2.4.29**(CN7PE·CN7NPE) 또는 **2.4.30**(CN7HEVPE), HMG-API **1.1.0-rc.8**, Realtek **1.1.19**가 포함됩니다.

주차 상태에서 설치하고 완료될 때까지 전원을 끄거나 USB를 빼지 마세요. 설치 실패 시 내비게이션 재부팅이나 복구가 필요할 수 있습니다. 모든 책임은 설치하신 차주 본인에게 있습니다.

## 설치 및 업데이트

1. [최신 합본 ZIP](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/latest)을 FAT32 USB 메모리 최상위에 풉니다. `NEMESIS.data`와 `packages` 폴더가 최상위에 있어야 합니다. `packages` 안의 ZIP 세 개는 압축 상태로 둡니다.
2. USB 메모리를 내비게이션의 데이터 포트에 꽂습니다. **NEMESIS → Package Store → USB → Korea Projection CN7PE / CN7HEVPE / CN7NPE BETA**에서 **Install** 또는 **Update**를 누릅니다. 설치 계획을 승인하면 필요한 HMG-API와 Realtek 드라이버를 먼저 설치하거나 업데이트합니다.
3. 설치 완료 후 USB 메모리를 빼고 동글 하나를 꽂습니다. Wireless Mode 적용과 재부팅 안내를 따릅니다. **USB Wi-Fi AP ready (rtwlan0)**가 뜨면 iPhone의 Wi-Fi와 Bluetooth를 켜고 연결합니다.
4. CN7NPE에서는 음악을 재생해 차량 스피커 출력을 확인합니다. 오디오 보정은 Wireless Mode에 포함되어 있습니다.

ipTIME A3000mini(`0bda:b812`)는 CN7NPE에서 확인했습니다. TP-Link Archer T3U V1(`2357:012d`)과 NEXI NX-AC1300(`0bda:b812`로 인식되는 경우)은 실차 시험 대상입니다. **480Mbps** 표시는 USB 버스 속도입니다.

## HUD 경로 안내

합본의 **HMG-API → Wireless Mode → Turn-by-turn on the cluster and HUD**는 기본 **꺼짐**입니다. 별도의 **Phone Projection TBT**를 쓰는 경우 Wireless Mode의 HUD 옵션을 끈 상태로 두세요.

업데이트 시 직접 저장한 켜짐·꺼짐은 유지됩니다. 이전에 켜 두었고 별도 TBT를 사용한다면 Wireless Mode의 HUD 옵션을 끄고 적용한 뒤 재부팅하세요. 합본 HUD를 사용하려면 별도 Phone Projection TBT를 끈 뒤 Wireless Mode의 HUD 옵션을 켜고 적용·재부팅합니다. 경로를 시작해 HUD에 방향과 거리가 표시되는지 확인하세요.

## 재시도 및 제거

- HMG-API가 응답하지 않으면 내비게이션을 재부팅한 뒤 같은 USB에서 Korea Projection 설치를 다시 선택합니다.
- 합본을 제거할 때는 Korea Projection을 먼저 제거합니다. 별도로 설치한 패키지가 있다면 각 패키지의 제거 순서를 확인하세요. [Korea Projection 제거 안내](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb)

## 제보 파일 저장

1. 동글을 꽂은 채 부팅하고 약 2분 기다립니다. 인식하지 못하면 같은 부팅에서 동글을 한 번 재장착하고, 필요하면 Realtek Launch를 한 번 누릅니다. 부팅·재장착·Launch 시각과 화면 상태를 기록합니다.
2. 증상을 재현한 **같은 부팅**에서 동글을 빼고 제보 USB를 연결합니다. **NEMESIS → My Packages → Korea Projection → Launch → 제보 파일 만들기**를 선택합니다.
3. `KoreaProjection-report`의 `1-report.md`, `2-car-report.json`, `3-log.txt`를 확인합니다. USB 인식은 `speed.log`·`boot.log`, 오디오는 `usb-carplay-audio.log`, CN7NPE 오디오 보정은 `cn7npe-rtwlan0-carrier: applied` 기록을 함께 확인하세요. 제보 전에 개인 정보가 포함됐는지 확인합니다.

### 무선 곡 전환 무음 시험

**Wireless Mode → CarPlay's own log (troubleshooting)**를 켜고 재부팅합니다. 무선으로 다운로드한 곡을 재생한 뒤 간격을 두고 세 번 넘깁니다. 버튼을 누른 시각, 제목이 바뀐 시각, 소리가 들리기 시작한 시각을 기록합니다. 마지막 전환 약 1분 뒤 제보 파일을 저장합니다.

[전체 변경 이력](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/main/CHANGELOG.md) · [이전 버전 진단 절차](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/cn7npe-usb-bundle-v0.1.40/bundle/INSTALL-KO.md) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md#53-install-on-the-unit)
