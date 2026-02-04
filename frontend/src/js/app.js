import { fetchHtml, mountHtml, qs } from "./core/dom.js";
import { initSession, getState, setRoute, setStream, setCapture, setResult, setError, nextSeq } from "./core/state.js";
import { startWebcam, stopWebcam, describeCameraError } from "./features/webcam.js";
import { captureJpegBase64 } from "./features/capture.js";
import { analyzeWithRetry } from "./features/ws_client.js";
import { renderLoading } from "./features/render_loading.js";
import { renderResult } from "./features/render_result.js";
import { exportComposite } from "./features/export_image.js";
import { mapErrorToUi } from "./core/error_map.js";

const PATH = {
  HOME: "../src/pages/home.html",
  LOADING: "../src/pages/loading.html",
  RESULT: "../src/pages/result.html",
  ERROR: "../src/pages/error.html",
};

async function go(route) {
  const app = qs("#app");
  const html = await fetchHtml(PATH[route]);
  mountHtml(app, html);
  setRoute(route);
  return app;
}

function setStatus(root, text) {
  const el = root.querySelector("[data-status]");
  if (el) el.textContent = text ?? "";
}

async function bootHome() {
  const root = await go("HOME");
  const st = getState();

  initSession();
  setStatus(root, "");

  const videoEl = root.querySelector("[data-video]");
  const hintEl = root.querySelector("[data-cam-hint]");
  const btnCapture = root.querySelector("[data-btn-capture]");
  const btnRetryCam = root.querySelector("[data-btn-retry-cam]");

  async function connectCamera() {
    // 기존 스트림 정리
    stopWebcam(st.stream, videoEl);
    setStream(null);

    try {
      const stream = await startWebcam(videoEl);
      setStream(stream);
      if (hintEl) hintEl.textContent = "카메라 연결됨";
      setStatus(root, "");
    } catch (err) {
      const d = describeCameraError(err);
      if (hintEl) hintEl.textContent = `${d.title} — ${d.detail}`;
      setStatus(root, "카메라 연결이 필요해요.");
    }
  }

  btnRetryCam?.addEventListener("click", connectCamera);

  btnCapture?.addEventListener("click", async () => {
    const s = getState();
    if (!s.stream) {
      setStatus(root, "카메라가 아직 준비되지 않았어요. 먼저 연결해 주세요.");
      return;
    }

    // Step2) capture
    setStatus(root, "캡처 중…");
    let cap;
    try {
      cap = await captureJpegBase64(videoEl);
      setCapture(cap);
    } catch (e) {
      setError({ error_code: "DECODE_FAIL", message: "capture failed" });
      return bootError();
    }

    // Step3) WS
    return bootLoadingAndAnalyze();
  });

  // 최초 카메라 자동 연결
  await connectCamera();
}

async function bootLoadingAndAnalyze() {
  const root = await go("LOADING");
  const st = getState();

  setStatus(root, "");
  renderLoading(root, { setStatusText: (t) => setStatus(root, t) });

  const payload = {
    type: "analyze",
    session_id: st.sessionId,
    seq: nextSeq(),
    ts_ms: Date.now(),
    image_format: "jpeg",
    image_b64: st.lastCapture.jpegBase64, // prefix 없는 raw base64
  };

  try {
    const res = await analyzeWithRetry(payload, (t) => setStatus(root, t));
    setResult(res);
    return bootResult();
  } catch (err) {
    // err is AnalyzeError or {error_code, message}
    setError({ error_code: err.error_code || "TIMEOUT", message: err.message || "unknown" });
    return bootError();
  }
}

async function bootResult() {
  const root = await go("RESULT");
  const st = getState();

  renderResult(root, {
    captureDataUrl: st.lastCapture.dataUrl,
    result: st.lastResult,
    onRetry: () => bootHome(),
    onDownload: async () => {
      setStatus(root, "이미지 생성 중…");
      await exportComposite({ captureDataUrl: st.lastCapture.dataUrl, result: st.lastResult });
      setStatus(root, "다운로드 완료!");
    },
  });
}

async function bootError() {
  const root = await go("ERROR");
  const st = getState();

  const ui = mapErrorToUi(st.lastError?.error_code);
  const titleEl = root.querySelector("[data-error-title]");
  const textEl = root.querySelector("[data-error-text]");
  const btnEl = root.querySelector("[data-btn-error-cta]");

  if (titleEl) titleEl.textContent = "다시 시도해볼까요?";
  if (textEl) textEl.textContent = ui.text;
  if (btnEl) {
    btnEl.textContent = ui.cta;
    btnEl.onclick = () => bootHome();
  }
}

bootHome();
