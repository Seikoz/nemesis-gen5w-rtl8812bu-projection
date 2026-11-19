# 아반떼 N 260902 NEMESIS USB 합본

2024년식 아반떼 N 페이스리프트 `CN7NPE.KOR.S5W_M.V039.001.260902`와 ipTIME A3000mini(`0bda:b812`)용 무선 카플레이 진단 테스트판입니다. 대상 헤드유닛은 TCC803x, 커널은 `3.18.24-tcc`입니다. NEMESIS Manager 1.16.7 이상이 설치되어 있어야 합니다.

**[USB 설치 ZIP v0.1.8 다운로드](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/download/cn7npe-usb-bundle-v0.1.8/NEMESIS-CN7NPE-260902-Bundle-v0.1.8-USB.zip)** · [릴리스 변경 사항](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/tag/cn7npe-usb-bundle-v0.1.8) · [전체 변경 이력](CHANGELOG.md)

| 구성 | 버전 |
| --- | --- |
| Korea Projection CN7NPE USB Test | 1.7.4.13 |
| Realtek RTL8812BU USB Driver | 1.1.11 |
| HMG-API 본체 | 1.1.0-rc.4 |
| HMG-API 무선 CarPlay·Android Auto 모드 | 2.4.6 |

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
2. 연결이 실패하면 같은 부팅에서 동글을 한 번 뺐다 꽂고 Korea Projection 상태를 다시 확인합니다. 필요한 경우 Realtek **Launch**를 한 번 누릅니다.
3. 재부팅하기 전에 USB 메모리로 바꿔 꽂고 **NEMESIS → My Packages → Korea Projection CN7NPE USB Test → Launch → 제보 파일 만들기**를 누릅니다. USB의 `KoreaProjection-report/3-log.txt`에 첫 USB 감지와 장치 번호 변경 후 각각의 UP 시도, 커널 로그, `hostapd` 권한 정보와 실패 로그가 들어갑니다. `1-report.md`와 `2-car-report.json`이 만들어졌다면 함께 첨부해 주세요.

v0.1.8의 모듈 빌드와 USB 설치 ZIP을 검증했습니다. 실차의 부팅 인식과 무선 카플레이 연결은 테스트가 필요합니다.

## 소스와 라이선스

- [Realtek 대응 소스·Gen5W 빌드 설정](driver-source/README.md) · [USB 리셋 도구](driver-source/usb_reset_a3000mini.c)
- [Korea Projection 1.7.4 원본](https://github.com/StopDragon/korea-projection/tree/v1.7.4) · [CN7NPE USB 이식 소스](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb) · [합본 진단 스크립트](bundle)
- [HMG-API 1.1.0-rc.4](https://github.com/Open-HMG/HMG-API/tree/v1.1.0-rc.4) · [NEMESIS USB 패키지 문서](https://github.com/xwtk/hmg_nemesis/blob/main/05-Packages.md)
