const state = {
  route: "HOME", // HOME | LOADING | RESULT | ERROR
  sessionId: null,
  seq: 0,

  stream: null,
  lastCapture: null, // { jpegBase64, dataUrl, width, height }
  lastResult: null,  // AnalyzeResult
  lastError: null,   // { error_code, message }
};

export function initSession() {
  // 단순/충돌 적은 세션ID: s_<timestamp>_<rand>
  const rand = Math.random().toString(16).slice(2, 8);
  state.sessionId = `s_${Date.now()}_${rand}`;
  state.seq = 0;
}

export function nextSeq() {
  state.seq += 1;
  return state.seq;
}

export function getState() { return state; }

export function setRoute(route) { state.route = route; }
export function setStream(stream) { state.stream = stream; }
export function setCapture(capture) { state.lastCapture = capture; }
export function setResult(result) { state.lastResult = result; }
export function setError(err) { state.lastError = err; }
