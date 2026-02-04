import { runLoadingSteps } from "../core/timers.js";

export async function renderLoading(root, { setStatusText }) {
  const stepEl = root.querySelector("[data-loading-step]");
  const subEl = root.querySelector("[data-loading-sub]");
  const setStep = (t) => { if (stepEl) stepEl.textContent = t; };
  const setSub = (t) => { if (subEl) subEl.textContent = t; };
  setSub("");

  await runLoadingSteps(setStep, [
    { text: "표정 확인 중…", ms: 600 },
    { text: "닮은꼴 비교 중…", ms: 700 },
    { text: "결과 정리 중…", ms: 600 },
  ]);

  // WS 재시도 문구는 app.js에서 setStatusText로 override 가능
  setStatusText?.("");
}
