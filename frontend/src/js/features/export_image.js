function dataUrlToImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = dataUrl;
  });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function exportComposite({ captureDataUrl, result }) {
  // “발표 안정성” 우선: 예쁜 카드 이미지 대신, 깔끔한 텍스트/바 합성
  const W = 1080;
  const H = 1350;

  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");

  // 배경
  ctx.fillStyle = "#0b0b10";
  ctx.fillRect(0, 0, W, H);

  // 타이틀
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 44px system-ui";
  ctx.fillText(`오늘의 표정: ${result.expression_label}`, 60, 90);

  // 스냅샷
  const snapImg = await dataUrlToImage(captureDataUrl);
  const snapW = 420;
  const snapH = 560;
  ctx.save();
  ctx.beginPath();
  ctx.roundRect(60, 130, snapW, snapH, 24);
  ctx.clip();
  ctx.drawImage(snapImg, 60, 130, snapW, snapH);
  ctx.restore();

  // 결과 카드(텍스트)
  const startX = 520;
  let y = 180;
  for (const r of result.results) {
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 34px system-ui";
    ctx.fillText(`${r.rank}위  ${r.celeb_name}`, startX, y);

    // 바
    const barX = startX;
    const barY = y + 24;
    const barW = 480;
    const barH = 18;
    ctx.fillStyle = "#2a2a38";
    ctx.fillRect(barX, barY, barW, barH);
    ctx.fillStyle = "#7c5cff";
    ctx.fillRect(barX, barY, Math.round(barW * (r.similarity_100 / 100)), barH);

    ctx.fillStyle = "#cfcfe6";
    ctx.font = "24px system-ui";
    ctx.fillText(`${r.similarity_100} / 100`, barX, barY + 48);

    y += 150;
  }

  // 프라이버시 문구
  ctx.fillStyle = "#9aa0aa";
  ctx.font = "22px system-ui";
  ctx.fillText("원본 사진은 저장하지 않아요. 다운로드는 사용자 선택이에요.", 60, H - 70);

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) throw new Error("export toBlob failed");
  downloadBlob(blob, `beauty_inside_${Date.now()}.png`);
}
