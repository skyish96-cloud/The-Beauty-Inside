import { CONFIG } from "../config.js";

function isLocalhost() {
  const h = location.hostname;
  return h === "localhost" || h === "127.0.0.1";
}

export async function startWebcam(videoEl) {
  // (A) 보안 컨텍스트 선제 안내 포인트
  // getUserMedia는 보안 컨텍스트에서만 동작하는 경우가 많음
  if (!window.isSecureContext && !isLocalhost()) {
    const err = new Error("Insecure context");
    err.name = "SecurityError";
    throw err;
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    const err = new Error("getUserMedia not supported");
    err.name = "NotSupportedError";
    throw err;
  }

  // (B) autoplay 안정화 세팅
  videoEl.autoplay = true;
  videoEl.muted = true;
  videoEl.playsInline = true;

  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user" },
    audio: false,
  });

  videoEl.srcObject = stream;
  await videoEl.play();

  videoEl.style.transform = CONFIG.MIRROR_PREVIEW ? "scaleX(-1)" : "none";
  return stream;
}

export function stopWebcam(stream, videoEl) {
  if (videoEl) videoEl.srcObject = null;
  if (!stream) return;
  for (const t of stream.getTracks()) t.stop();
}

export function describeCameraError(err) {
  const name = err?.name || "";

  // 보안 컨텍스트(HTTPS/localhost) 이슈를 “명확 문구”로 분리
  if (name === "SecurityError" || (!window.isSecureContext && location.protocol !== "https:")) {
    return {
      title: "HTTPS(또는 localhost) 환경이 필요해요",
      detail: "현재 접속 환경에서는 카메라가 차단될 수 있어요. HTTPS 또는 localhost로 실행해 주세요."
    };
  }

  if (name === "NotAllowedError" || name === "PermissionDeniedError") {
    return { title: "카메라 권한이 필요해요", detail: "브라우저에서 카메라 권한을 허용한 뒤 다시 시도해 주세요." };
  }
  if (name === "NotFoundError" || name === "DevicesNotFoundError") {
    return { title: "카메라를 찾을 수 없어요", detail: "카메라가 연결되어 있는지 확인해 주세요." };
  }
  if (name === "NotReadableError") {
    return { title: "카메라를 열 수 없어요", detail: "다른 앱이 카메라를 사용 중인지 확인해 주세요." };
  }
  if (name === "NotSupportedError") {
    return { title: "지원되지 않는 환경이에요", detail: "이 브라우저에서는 카메라 API를 사용할 수 없어요." };
  }
  return { title: "카메라 초기화 실패", detail: "장치 상태를 확인한 뒤 다시 시도해 주세요." };
}
