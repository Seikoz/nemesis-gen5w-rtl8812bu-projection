# 아반떼 Gen5W USB 합본 설치

**v0.1.47**은 국내형 아반떼 CN7PE, 하이브리드 CN7HEVPE, N CN7NPE의 **V039.001.260902** Gen5W(TCC803x)를 대상으로 합니다. NEMESIS Manager **1.16.7 이상**이 필요합니다. 합본에는 Korea Projection **1.7.4.52**, Wireless Mode **2.4.31**(CN7PE·CN7NPE) 또는 **2.4.32**(CN7HEVPE), HMG-API **1.1.0-rc.8**, Realtek **1.1.19**가 포함됩니다.

주차 상태에서 설치하고 완료될 때까지 전원을 끄거나 USB를 빼지 마세요. 설치 실패 시 내비게이션 재부팅이나 복구가 필요할 수 있습니다. 모든 책임은 설치하신 차주 본인에게 있습니다.

## 설치 및 업데이트

1. 받은 합본 ZIP을 FAT32 USB 메모리 최상위에 풉니다. `NEMESIS.data`와 `packages` 폴더가 최상위에 있어야 합니다. `packages` 안의 ZIP 세 개는 압축 상태로 둡니다.
2. USB 메모리를 내비게이션의 데이터 포트에 꽂습니다. **NEMESIS → Package Store → USB → Korea Projection CN7PE / CN7HEVPE / CN7NPE BETA**에서 **Install** 또는 **Update**를 누릅니다. 설치 계획을 승인하면 필요한 HMG-API와 Realtek 드라이버를 먼저 설치하거나 업데이트합니다.
3. 설치 완료 후 USB 메모리를 빼고 동글 하나를 꽂습니다. Wireless Mode 적용과 재부팅 안내를 따릅니다. **USB Wi-Fi AP ready (rtwlan0)**가 뜨면 iPhone의 Wi-Fi와 Bluetooth를 켜고 연결합니다.
4. CN7NPE에서는 음악을 재생해 차량 스피커 출력을 확인합니다. 오디오 보정은 Wireless Mode에 포함되어 있습니다.

ipTIME A3000mini(`0bda:b812`)는 CN7NPE에서 확인했습니다. TP-Link Archer T3U V1(`2357:012d`)과 NEXI NX-AC1300(`0bda:b812`로 인식되는 경우)은 실차 시험 대상입니다. **480Mbps** 표시는 USB 버스 속도입니다.

## 연결 대시보드

설치 후 내비게이션의 Android 앱 목록에서 **무선 연결 대시보드**를 엽니다. 목록에서 찾을 수 없으면 **NEMESIS → My Packages → Korea Projection → Launch**로 엽니다. 대시보드를 여는 동안 약 5초마다 상태를 읽고 **마지막 확인** 시각을 표시합니다.

설치 또는 업데이트 시 **무선 연결 대시보드**의 홈 바로가기 등록을 자동으로 요청합니다. 순정 홈에서 외부 앱 바로가기를 지원하면 홈에 아이콘이 추가됩니다. 설치 중 등록 요청을 보내지 못했다면 앱을 처음 열 때 시도합니다. 앱의 **홈 바로가기 추가** 버튼으로 수동 요청도 할 수 있습니다.

- **버전**은 합본, Korea Projection, Realtek 드라이버 패키지, HMG-API, 설치된 Wireless Mode를 표시합니다.
- **무선랜**은 USB 제품명 또는 USB ID로 확인한 모델, USB 버스 속도, 현재 핫스폿 SSID를 표시합니다. `0bda:b812`에서 제품명으로 모델을 구분할 수 없으면 칩셋과 USB ID를 표시합니다. 단말 한 대의 인증과 송신 링크 속도가 확인되면 Wi-Fi 링크도 따로 표시합니다.
- **Wi-Fi 품질**은 채널, 접속 단말 수, 확인 가능한 신호 세기와 송신 링크를 표시합니다. 채널 실측을 지원하지 않으면 핫스폿 설정값을 별도로 표시합니다.
- **무선 연결**은 CarPlay 세션과 Android Auto의 무선 연결 상태를 따로 표시합니다. 최신 진행 상태와 이번 부팅 중 기록된 마지막 설정 실패를 확인할 수 있습니다.
- **부팅 후 준비 시간**은 USB 480Mbps·인터페이스 인식과 핫스폿 준비가 처음 확인된 부팅 후 시각입니다.
- **HUD**는 Phone Projection TBT와 Wireless Mode HUD 설정을 보여 주고 두 설정이 켜져 있으면 표시합니다.
- **GPS 연동 상태**의 **차량 GPS**는 내비게이션이 보고한 최근 수신 상태입니다. 위성 상태가 들어오면 신호 대 잡음비(SNR)가 보고된 위성 수, 최근 위치 계산에 사용한 위성 수, 수신 위성의 평균 SNR(dB)을 표시합니다. 위성 상태가 10초 이상 갱신되지 않으면 **확인 불가**로 표시합니다. **휴대폰 GPS 연동**은 확인 신호를 읽을 수 없어 **확인 불가**로 표시합니다.

GPS 위성 상태를 받기 위해 대시보드 앱은 정확한 위치 권한을 사용합니다. 앱은 기존 내비게이션 수신 상태를 읽고 화면에 표시합니다. 별도 위치 업데이트를 요청하거나 좌표를 저장하지 않습니다.

## HUD 경로 안내

HUD는 별도 **Phone Projection TBT**를 설치해 **켜짐**으로 사용하세요. 원본 모드는 활성 상태에서 CarPlay 길안내를 사용하며, **Android Auto 길안내**도 기본 켜짐입니다. [Phone Projection TBT 설치 안내](https://github.com/ch0iiih/HMG_Phone_Projection_TBT/releases/latest)

합본의 **HMG-API → Wireless Mode → 계기판·HUD 길안내**는 중복 표시를 피하기 위해 기본 **꺼짐**입니다. 업데이트 시 저장한 선택은 유지됩니다. 두 모드가 모두 켜져 있다면 Wireless Mode의 **계기판·HUD 길안내**를 끄고 적용한 뒤 재부팅하세요. 경로를 시작해 HUD에 방향과 거리가 표시되는지 확인합니다.

## 재시도 및 제거

- HMG-API가 응답하지 않으면 내비게이션을 재부팅한 뒤 같은 USB에서 Korea Projection 설치를 다시 선택합니다.
- 합본을 제거할 때는 Korea Projection을 먼저 제거합니다. 별도로 설치한 패키지가 있다면 각 패키지의 제거 순서를 확인하세요. [Korea Projection 제거 안내](https://github.com/Seikoz/nemesis-gen5w-rtl8812bu-projection/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb)

## 제보 파일 저장

1. 동글을 꽂은 채 부팅하고 약 2분 기다립니다. 인식하지 못하면 같은 부팅에서 동글을 한 번 재장착하고, 필요하면 Realtek Launch를 한 번 누릅니다. 부팅·재장착·Launch 시각과 화면 상태를 기록합니다.
2. 증상을 재현한 **같은 부팅**에서 동글을 빼고 제보 USB를 연결합니다. **NEMESIS → My Packages → Korea Projection → Launch → 제보 파일 만들기**를 선택합니다.
3. `KoreaProjection-report`의 `1-report.md`, `2-car-report.json`, `3-log.txt`를 확인합니다. USB 인식은 `speed.log`·`boot.log`, 오디오는 `usb-carplay-audio.log`, CN7NPE 오디오 보정은 `cn7npe-rtwlan0-carrier: applied` 기록을 함께 확인하세요. 제보 전에 개인 정보가 포함됐는지 확인합니다.

### 무선 곡 전환 무음 시험

**Wireless Mode → CarPlay 상세 로그 (문제 진단)**를 켜고 재부팅합니다. 다운로드한 곡을 무선 CarPlay로 재생한 뒤 간격을 두고 세 번 넘깁니다. 버튼을 누른 시각, 제목이 바뀐 시각, 소리가 들리기 시작한 시각을 기록합니다. 마지막 전환 약 1분 뒤 제보 파일을 저장합니다.

[전체 변경 이력](https://github.com/Seikoz/nemesis-gen5w-rtl8812bu-projection/blob/main/CHANGELOG.md) · [이전 버전 진단 절차](https://github.com/Seikoz/nemesis-gen5w-rtl8812bu-projection/blob/cn7npe-usb-bundle-v0.1.40/bundle/INSTALL-KO.md) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md#53-install-on-the-unit)
