import { CONFIG, getWsUrl } from "../config.js";

function nowMs() { return Date.now(); }

function backoffDelay(attempt) {
  return CONFIG.WS_RETRY_BASE_DELAY_MS * Math.pow(2, attempt);
}

function mockResult(session_id, seq) {
  return {
    type: "result",
    session_id,
    seq,
    latency_ms: 42,
    expression_label: "smile",
    similarity_method: "cosine",
    quality_flags: [],
    results: [
      { rank: 1, celeb_id: "c_001", celeb_name: "A", similarity: 0.82, similarity_100: 82 },
      { rank: 2, celeb_id: "c_014", celeb_name: "B", similarity: 0.79, similarity_100: 79 },
      { rank: 3, celeb_id: "c_203", celeb_name: "C", similarity: 0.77, similarity_100: 77 },
    ],
  };
}

export async function analyzeOnce(payload) {
  if (CONFIG.USE_MOCK) {
    await new Promise(r => setTimeout(r, 600));
    return mockResult(payload.session_id, payload.seq);
  }

  const url = getWsUrl();
  const ws = new WebSocket(url);

  const timeoutAt = nowMs() + CONFIG.WS_TIMEOUT_MS;

  return await new Promise((resolve, reject) => {
    let done = false;

    const timer = setInterval(() => {
      if (done) return;
      if (nowMs() > timeoutAt) {
        done = true;
        try { ws.close(); } catch {}
        clearInterval(timer);
        reject({ type: "error", error_code: "TIMEOUT", message: "client timeout" });
      }
    }, 50);

    ws.onopen = () => {
      try {
        ws.send(JSON.stringify(payload));
      } catch (e) {
        done = true;
        clearInterval(timer);
        reject({ type: "error", error_code: "TIMEOUT", message: "send failed" });
      }
    };

    ws.onmessage = (ev) => {
      if (done) return;
      try {
        const msg = JSON.parse(ev.data);
        done = true;
        clearInterval(timer);
        ws.close();

        if (msg.type === "result") return resolve(msg);
        if (msg.type === "error") return reject(msg);
        return reject({ type: "error", error_code: "DECODE_FAIL", message: "unknown message type" });
      } catch (e) {
        done = true;
        clearInterval(timer);
        try { ws.close(); } catch {}
        reject({ type: "error", error_code: "DECODE_FAIL", message: "json parse failed" });
      }
    };

    ws.onerror = () => {
      if (done) return;
      done = true;
      clearInterval(timer);
      reject({ type: "error", error_code: "TIMEOUT", message: "ws error" });
    };

    ws.onclose = () => {
      // onmessage에서 close되는 정상 케이스와 구분은 done으로 처리
    };
  });
}

export async function analyzeWithRetry(payload, onRetryStatus) {
  // onRetryStatus(text) : "재시도 중..." 같은 UI용
  for (let attempt = 0; attempt <= CONFIG.WS_RETRY_MAX; attempt++) {
    try {
      const res = await analyzeOnce(payload);
      return res;
    } catch (err) {
      // 서버가 계약 에러코드를 준 경우는 재시도보다 UX가 우선
      if (err?.type === "error" && err?.error_code && err?.error_code !== "TIMEOUT") {
        throw err;
      }
      if (attempt === CONFIG.WS_RETRY_MAX) throw err;

      onRetryStatus?.(`연결 재시도 중… (${attempt + 1}/${CONFIG.WS_RETRY_MAX})`);
      await new Promise(r => setTimeout(r, backoffDelay(attempt)));
    }
  }
  throw { type: "error", error_code: "TIMEOUT", message: "retry exhausted" };
}
