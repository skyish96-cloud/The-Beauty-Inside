import { CONFIG } from "../config.js";

function calcResize(w, h, maxEdge) {
  const longEdge = Math.max(w, h);
  if (longEdge <= maxEdge) return { w, h };
  const scale = maxEdge / longEdge;
  return { w: Math.round(w * scale), h: Math.round(h * scale) };
}

function blobToBase64Raw(blob) {
  // "data:image/jpeg;base64,..." 없이 raw base64만 뽑기
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => {
      const dataUrl = String(fr.result);
      const comma = dataUrl.indexOf(",");
      resolve(dataUrl.slice(comma + 1));
    };
    fr.onerror = reject;
    fr.readAsDataURL(blob);
  });
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(String(fr.result));
    fr.onerror = reject;
    fr.readAsDataURL(blob);
  });
}

export async function captureJpegBase64(videoEl) {
  const vw = videoEl.videoWidth;
  const vh = videoEl.videoHeight;
  if (!vw || !vh) throw new Error("video not ready");

  const { w, h } = calcResize(vw, vh, CONFIG.CAPTURE_MAX_EDGE);

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");

  // 캡처 미러(원하면 끄기)
  if (CONFIG.MIRROR_CAPTURE) {
    ctx.translate(w, 0);
    ctx.scale(-1, 1);
  }
  ctx.drawImage(videoEl, 0, 0, w, h);

  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", CONFIG.JPEG_QUALITY)
  );
  if (!blob) throw new Error("toBlob failed");

  const jpegBase64 = await blobToBase64Raw(blob);
  const dataUrl = await blobToDataUrl(blob); // UI 미리보기용(프리픽스 포함)

  return { jpegBase64, dataUrl, width: w, height: h };
}
