export function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function runLoadingSteps(setStepText, steps) {
  // steps: [{ text, ms }]
  for (const s of steps) {
    setStepText(s.text);
    await sleep(s.ms);
  }
}
