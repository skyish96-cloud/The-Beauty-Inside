export function qs(sel, root = document) {
  const el = root.querySelector(sel);
  if (!el) throw new Error(`DOM not found: ${sel}`);
  return el;
}

export function qsa(sel, root = document) {
  return Array.from(root.querySelectorAll(sel));
}

export function setText(el, text) {
  el.textContent = String(text ?? "");
}

export function on(el, event, handler) {
  el.addEventListener(event, handler);
}

export async function fetchHtml(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load HTML: ${path}`);
  return await res.text();
}

export function mountHtml(targetEl, html) {
  targetEl.innerHTML = html;
}
