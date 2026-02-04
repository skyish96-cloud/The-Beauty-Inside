function medalByRank(rank) {
  if (rank === 1) return "🥇";
  if (rank === 2) return "🥈";
  return "🥉";
}

export function renderResult(root, { captureDataUrl, result, onRetry, onDownload }) {
  const snap = root.querySelector("[data-snapshot]");
  if (snap) snap.src = captureDataUrl;

  const expr = root.querySelector("[data-expression]");
  if (expr) expr.textContent = result.expression_label;

  const list = root.querySelector("[data-results]");
  if (list) {
    list.innerHTML = "";
    for (const item of result.results) {
      const card = document.createElement("div");
      card.className = `celeb-card rank-${item.rank}`;
      card.innerHTML = `
        <div class="celeb-rank">${medalByRank(item.rank)} ${item.rank}위</div>
        <div class="celeb-name">${item.celeb_name}</div>
        <div class="celeb-score">
          <div class="bar"><div class="bar-fill" style="width:${item.similarity_100}%"></div></div>
          <div class="score">${item.similarity_100} / 100</div>
        </div>
      `;
      list.appendChild(card);
    }
  }

  const btnRetry = root.querySelector("[data-btn-retry]");
  const btnDownload = root.querySelector("[data-btn-download]");
  if (btnRetry) btnRetry.onclick = onRetry;
  if (btnDownload) btnDownload.onclick = onDownload;
}
