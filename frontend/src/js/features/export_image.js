import { getApiBaseUrl } from "../config.js";

function dataUrlToImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
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

// Pop Art 팔레트 (Andy Warhol 스타일)
const popArtColors = [
  "#FF6B9D",  // 핑크
  "#C44569",  // 짙은 빨강
  "#FFA62B",  // 주황
  "#FFD662",  // 노랑
  "#6BCF7F",  // 초록
  "#4D96FF",  // 파랑
  "#9B59B6",  // 보라
  "#FF1493",  // 진홍색
];

function applyPopArtFilter(ctx, x, y, w, h, colorIndex) {
  const bgColor = popArtColors[colorIndex % popArtColors.length];
  ctx.fillStyle = bgColor;
  ctx.fillRect(x, y, w, h);
}

export async function exportComposite({ captureDataUrl, result }) {
  const W = 1080;
  const H = 1440;

  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");

  // 흰색 배경
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, W, H);

  const snapImg = await dataUrlToImage(captureDataUrl);

  // 연예인 이미지 URL 생성 헬퍼
  function getCelebImageUrl(item) {
    if (item?.celeb_image_url) {
      if (item.celeb_image_url.startsWith("http")) return item.celeb_image_url;
      return `${getApiBaseUrl()}${item.celeb_image_url}`;
    }
    if (item?.celeb_id) return `${getApiBaseUrl()}/api/celeb-image/${item.celeb_id}`;
    return null;
  }

  // 연예인 이미지 로드 (시도)
  let celebImg1 = null, celebImg2 = null, celebImg3 = null;
  try {
    const url1 = getCelebImageUrl(result.results[0]);
    const url2 = getCelebImageUrl(result.results[1]);
    const url3 = getCelebImageUrl(result.results[2]);

    if (url1) celebImg1 = await dataUrlToImage(url1);
    if (url2) celebImg2 = await dataUrlToImage(url2);
    if (url3) celebImg3 = await dataUrlToImage(url3);
  } catch (e) {
    console.log("Image loading error:", e);
  }

  // Grid 레이아웃 (3x3)
  // [사용자 2x2] [1위 1x1]   [1위 1x1]
  // [사용자 2x2] [Beauty]    [Beauty]
  // [2위 1x1]    [3위 1x1]   [제목/정보]

  const cellW = W / 3;
  const cellH = H / 3;

  // ===== Row 1 (상단) =====

  // 좌상 2x2 - 사용자 사진 (큼)
  ctx.fillStyle = "#e8e8f0";
  ctx.fillRect(0, 0, cellW * 2, cellH * 2);
  ctx.drawImage(snapImg, 0, 0, cellW * 2, cellH * 2);

  // 사용자 라벨
  ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
  ctx.fillRect(0, cellH * 2 - 60, cellW * 2, 60);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 24px system-ui";
  ctx.textAlign = "left";
  ctx.fillText("YOU - " + result.expression_label, 20, cellH * 2 - 20);

  // 우상 1x1 - 1위 연예인
  applyPopArtFilter(ctx, cellW * 2, 0, cellW, cellH, 1);
  if (celebImg1) {
    ctx.drawImage(celebImg1, cellW * 2, 0, cellW, cellH);
  }
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(cellW * 2, cellH - 60, cellW, 60);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("🥇 " + result.results[0]?.similarity_100 + "%", cellW * 2 + cellW / 2, cellH - 20);

  // 우우상 1x1 - "Beauty Inside"
  applyPopArtFilter(ctx, cellW * 2 + cellW, 0, cellW, cellH, 2);
  ctx.fillStyle = "#000000";
  ctx.font = "bold 32px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("Beauty", cellW * 2 + cellW + cellW / 2, cellH / 2 - 15);
  ctx.font = "bold 32px system-ui";
  ctx.fillText("Inside", cellW * 2 + cellW + cellW / 2, cellH / 2 + 20);

  // ===== Row 2 (중간) =====

  // 좌중 2x1 - 이미 사용자 사진으로 차있음

  // 우중좌 1x1 - 2위 연예인
  applyPopArtFilter(ctx, cellW * 2, cellH, cellW, cellH, 3);
  if (celebImg2) {
    ctx.drawImage(celebImg2, cellW * 2, cellH, cellW, cellH);
  }
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(cellW * 2, cellH + cellH - 60, cellW, 60);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("🥈 " + result.results[1]?.similarity_100 + "%", cellW * 2 + cellW / 2, cellH + cellH - 20);

  // 우중우 1x1 - 3위 연예인
  applyPopArtFilter(ctx, cellW * 2 + cellW, cellH, cellW, cellH, 4);
  if (celebImg3) {
    ctx.drawImage(celebImg3, cellW * 2 + cellW, cellH, cellW, cellH);
  }
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(cellW * 2 + cellW, cellH + cellH - 60, cellW, 60);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("🥉 " + result.results[2]?.similarity_100 + "%", cellW * 2 + cellW + cellW / 2, cellH + cellH - 20);

  // ===== Row 3 (하단) =====

  // 좌하 1x1 - 1위 이름
  applyPopArtFilter(ctx, 0, cellH * 2, cellW, cellH, 5);
  ctx.fillStyle = "#000000";
  ctx.font = "bold 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(result.results[0]?.celeb_name || "---", cellW / 2, cellH * 2 + cellH / 2);

  // 중하 1x1 - 2위 이름
  applyPopArtFilter(ctx, cellW, cellH * 2, cellW, cellH, 6);
  ctx.fillStyle = "#000000";
  ctx.font = "bold 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(result.results[1]?.celeb_name || "---", cellW + cellW / 2, cellH * 2 + cellH / 2);

  // 우하 1x1 - 3위 이름
  applyPopArtFilter(ctx, cellW * 2, cellH * 2, cellW, cellH, 7);
  ctx.fillStyle = "#000000";
  ctx.font = "bold 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(result.results[2]?.celeb_name || "---", cellW * 2 + cellW / 2, cellH * 2 + cellH / 2);

  // 우우하 1x1 - 정보
  applyPopArtFilter(ctx, cellW * 2 + cellW, cellH * 2, cellW, cellH, 0);
  ctx.fillStyle = "#000000";
  ctx.font = "14px system-ui";
  ctx.textAlign = "center";
  let infoY = cellH * 2 + 30;
  ctx.fillText("원본 사진은", cellW * 2 + cellW + cellW / 2, infoY);
  ctx.fillText("저장하지 않아요", cellW * 2 + cellW + cellW / 2, infoY + 25);
  ctx.font = "12px system-ui";
  ctx.fillText(new Date().toLocaleDateString("ko-KR"), cellW * 2 + cellW + cellW / 2, infoY + 60);

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) throw new Error("export toBlob failed");
  downloadBlob(blob, `beauty_inside_popart_${Date.now()}.png`);
}
