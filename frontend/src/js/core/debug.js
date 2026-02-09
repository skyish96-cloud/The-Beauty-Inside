export const DEBUG = true; // 필요하면 false

export function dbg(tag, ...args) {
  if (!DEBUG) return;
  console.log(tag, ...args);
}

export function group(tag, fn) {
  if (!DEBUG) return fn();
  console.groupCollapsed(tag);
  try { return fn(); }
  finally { console.groupEnd(); }
}

// DOM 없으면 즉시 에러로 터뜨려서 "파일/라인"을 얻는 용도
export function must(root, selector, ctx = "") {
  const el = root?.querySelector?.(selector);
  if (!el) {
    const msg = `[DOM_MISSING] ${selector} ${ctx ? `(${ctx})` : ""}`;
    console.error(msg, { root });
    throw new Error(msg);
  }
  return el;
}
