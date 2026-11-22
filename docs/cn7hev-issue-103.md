# CN7HEV 내장 Wi-Fi와 CN7PE USB CarPlay 로그 비교

## Korea Projection 제보

| 제보 | 설정과 결과 |
| --- | --- |
| 초기형 CN7HEV, 2021년식 | 내비 `CN7HEV.KOR.0000.V039.001.260902`, Korea Projection 1.7.1, HMG-API 1.0.2, 무선 모드 2.3.0. 차량 지도 확인과 부팅 훅 적용을 통과했고, 내장 `wlan0`에서 Korea Projection의 AP와 DHCP가 동작했습니다. 5GHz 채널 149로 AP가 올라왔고 제보 시점 카플레이 연결 수는 1이었습니다. |
| CN7HEV22 | Korea Projection 1.7.2에서 지도 확인을 통과했습니다. DHD 어댑터 전원 활성화가 재시도 끝에 실패했고, `wlan0`이 생기지 않아 무선 모드를 설치하지 못했습니다. |
| 초기형 CN7HEV, 2020년 12월 출고 | `260902` 업데이트와 HMG-API rc.4 지도 적용 뒤 Korea Projection 1.7.4, 무선 모드 2.4.5로 내장 Wi-Fi에서 음악·통화와 RESET 후 재연결이 됐다는 제보입니다. 이 댓글에는 별도 첨부 로그가 없습니다. |

첨부 원본과 최신 제보는 [2021년식 성공 로그](https://github.com/StopDragon/korea-projection/issues/103#issuecomment-6728508868), [CN7HEV22 실패 로그](https://github.com/StopDragon/korea-projection/issues/103#issuecomment-6879729445), [2020년 출고차 성공 제보](https://github.com/StopDragon/korea-projection/issues/103#issuecomment-6985758583)에서 확인할 수 있습니다.

페이스리프트 CN7PE의 공식 패키지 제보에서도 차량 지도 검증 뒤 `module_version=3`과 `wlan0` 미검출이 기록됐습니다. CN7NPE 260902에서도 순정 Wi-Fi 감지 문제가 보고됐습니다. [CN7PE #382](https://github.com/StopDragon/korea-projection/issues/382) · [CN7NPE #62](https://github.com/StopDragon/korea-projection/issues/62)

## 오디오에서 확인한 차이

첨부된 초기형 CN7HEV 성공 로그는 19:45:21과 19:46:01에 DipoService가 `ResourceOwner.CONTROLLER AudioTye:Media`와 음악 우선권을 기록했습니다. 네이티브 `TccCarPlay_iAPSendMessage()` 호출도 관측됐습니다. 송신 호출의 반환값과 오디오 스트림 설정 시작은 이 로그에서 확인되지 않습니다. [CN7HEV 성공 로그](https://github.com/StopDragon/korea-projection/issues/103#issuecomment-6728508868)

A3000mini를 사용한 CN7PE의 v0.1.26 로그에서는 `rtwlan0`과 AP가 준비되고 무선 세션 및 Bluetooth iAP2 컴포넌트 4가 올라왔습니다. 뒤이어 첫 네이티브 전환 송신이 `rc=19`를 반환했고, 컴포넌트 5에서 `LimitMaxResend`가 반복됐습니다. 09:56:00에 음악 우선권을 얻었지만 DipoService는 `AudioTye:Unknown`을 기록했습니다. 이 차이로 오디오 타입이 인식되는 단계와 우선권을 얻는 단계를 구분할 수 있습니다. 전환 실패와 차량 오디오 문제의 인과관계는 아직 확인되지 않았습니다. [RTL8812BU Gen5W #2](https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/issues/2)

같은 CN7PE 로그의 IPv6 필터에는 `rtwlan0`의 UDP 6031 허용 규칙이 입력·출력에 각각 두 줄 있었고 카운터는 0이었습니다. 구형 `ip6tables`는 헤더에 `opt`를 표시하면서 IPv6 행에서 해당 값을 생략했고, 이 때문에 기존 요약에서 규칙 개수도 0으로 표시됐습니다.

## v0.1.31 시험판

제보의 `usb-carplay-audio.log`와 **USB CarPlay trial history**에 DipoService의 오디오 타입·우선권과 네이티브 iAP 송신 호출 개수를 보존합니다. IPv6 UDP 6031 규칙은 헤더와 행의 `opt` 표기가 달라도 집계합니다. 오디오 전환, 네트워크 정책과 A3000mini의 `rtwlan0` 동작은 기존 v0.1.30 경로를 따릅니다.
