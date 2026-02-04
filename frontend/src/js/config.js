export const CONFIG = {
  WS_PATH: "/ws/analyze",
  WS_TIMEOUT_MS: 8000,
  WS_RETRY_MAX: 2,
  WS_RETRY_BASE_DELAY_MS: 500,

  CAPTURE_MAX_EDGE: 640,       // 긴 변 기준
  JPEG_QUALITY: 0.8,           // 0.7~0.85 권장 범위
  MIRROR_PREVIEW: true,        // 미리보기 거울모드
  MIRROR_CAPTURE: true,        // 캡처도 미러(원하면 false)

  // 통합 전 UI 개발용. 백엔드 mock 준비되면 false.
  USE_MOCK: false,
  // USE_MOCK: true,
};

export function getWsUrl() {
  const proto = (location.protocol === "https:") ? "wss:" : "ws:";
  return `${proto}//${location.host}${CONFIG.WS_PATH}`;
}
