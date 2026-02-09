import { getApiBaseUrl } from "../config.js";

function medalByRank(rank) {
  if (rank === 1) return "🥇";
  if (rank === 2) return "🥈";
  return "🥉";
}

// 점수에 따른 재미있는 메시지
function getMatchMessage(score, rank) {
  if (rank === 1) {
    if (score >= 90) return "완벽한 도플갱어! 👯";
    if (score >= 80) return "쌍둥이 수준이에요! ✨";
    if (score >= 70) return "꽤 닮았어요! 💫";
    return "비슷한 느낌! 🌟";
  }
  if (rank === 2) {
    if (score >= 80) return "이것도 닮았네요! 😊";
    if (score >= 70) return "은근 비슷해요! 👀";
    return "살짝 닮은꼴 ✌️";
  }
  if (score >= 70) return "어딘가 닮았어요! 🤔";
  return "3등도 훌륭해요! 🎉";
}

// 표정별 재미있는 코멘트
function getFunComment(expression, topScore) {
  const comments = {
    smile: [
      "😄 웃는 얼굴이 최고예요!",
      "😊 행복한 미소가 빛나네요!",
      "🌞 눈부신 미소의 소유자!"
    ],
    sad: [
      "🥺 슬픈 눈빛도 매력적이에요",
      "💧 감성적인 분위기가 느껴져요",
      "🌧️ 우울한 날에도 멋져요"
    ],
    surprise: [
      "😲 놀란 표정이 귀여워요!",
      "🤯 깜짝! 놀라운 매력!",
      "👀 순수한 놀람이 포착됐어요"
    ],
    neutral: [
      "😌 자연스러운 매력이 최고!",
      "✨ 담담한 표정도 멋져요",
      "🎭 무표정도 카리스마!"
    ]
  };

  const exprComments = comments[expression] || comments.neutral;
  return exprComments[Math.floor(Math.random() * exprComments.length)];
}

// 하단 팁 메시지
function getFooterTip(expression) {
  const tips = {
    smile: "💡 슬픈 표정으로도 시도해보세요. 다른 결과가 나올 수 있어요!",
    sad: "💡 환하게 웃으면 또 다른 닮은꼴을 찾을 수 있어요!",
    surprise: "💡 자연스러운 표정으로도 테스트해보세요!",
    neutral: "💡 다양한 표정으로 시도하면 다른 결과가 나와요!"
  };
  return tips[expression] || tips.neutral;
}

// 컨페티 생성
function createConfetti(container) {
  const colors = ['#FF8A80', '#FFD54F', '#5BC4A8', '#81D4FA', '#CE93D8', '#FFAB91'];
  const confettiCount = 50;

  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confetti.style.cssText = `
      left: ${Math.random() * 100}%;
      background: ${colors[Math.floor(Math.random() * colors.length)]};
      animation-delay: ${Math.random() * 2}s;
      animation-duration: ${2 + Math.random() * 2}s;
    `;
    container.appendChild(confetti);
  }

  // 3초 후 제거
  setTimeout(() => {
    container.innerHTML = '';
  }, 4000);
}

// 점수 카운트업 애니메이션
function animateScore(element, targetScore, duration = 1000) {
  const startTime = performance.now();
  const startScore = 0;

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // easeOutExpo
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
    const currentScore = Math.round(startScore + (targetScore - startScore) * eased);

    element.textContent = currentScore;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

export function renderResult(root, { captureDataUrl, result, onRetry, onDownload }) {
  // 사용자 사진
  const snap = root.querySelector("[data-snapshot]");
  if (snap) snap.src = captureDataUrl;

  // 표정 태그
  const expr = root.querySelector("[data-expression]");
  if (expr) {
    const expressionLabel = result.expression_label || 'neutral';
    expr.textContent = expressionLabel;
    expr.className = `expression-tag ${expressionLabel}`;
  }

  // 최고 점수 표시
  const topScore = result.results[0]?.similarity_100 || 0;
  const topScoreEl = root.querySelector("[data-top-score]");
  if (topScoreEl) {
    animateScore(topScoreEl, topScore, 1500);
  }

  // 매치 배지 색상
  const matchBadge = root.querySelector("[data-match-badge]");
  if (matchBadge) {
    if (topScore >= 85) matchBadge.classList.add('excellent');
    else if (topScore >= 70) matchBadge.classList.add('good');
  }

  // 재미있는 코멘트
  const funComment = root.querySelector("[data-fun-comment]");
  if (funComment) {
    funComment.textContent = getFunComment(result.expression_label, topScore);
  }

  // 하단 팁
  const footerTip = root.querySelector("[data-footer-tip]");
  if (footerTip) {
    footerTip.textContent = getFooterTip(result.expression_label);
  }

  // 컨페티 효과
  const confettiContainer = root.querySelector(".confetti-container");
  if (confettiContainer && topScore >= 70) {
    createConfetti(confettiContainer);
  }

  // 1등 카드 렌더링 (별도 영역)
  const firstPlaceContainer = root.querySelector("[data-first-place]");
  const runnersUpContainer = root.querySelector("[data-results]");

  if (firstPlaceContainer) {
    firstPlaceContainer.innerHTML = "";
  }
  if (runnersUpContainer) {
    runnersUpContainer.innerHTML = "";
  }

  for (const item of result.results) {
    let url = item.celeb_image_url || `/api/celeb-image/${item.celeb_id}`;
    if (url && !url.startsWith("http")) {
      url = `${getApiBaseUrl()}${url}`;
    }
    const celebImageUrl = url;
    const matchMsg = getMatchMessage(item.similarity_100, item.rank);

    if (item.rank === 1 && firstPlaceContainer) {
      // 1등: 큰 카드로 렌더링
      const card = document.createElement("div");
      card.className = "first-place-card celeb-card rank-1";

      card.innerHTML = `
        <div class="first-celeb-image-wrap">
          <img class="first-celeb-image" src="${celebImageUrl}" alt="${item.celeb_name}">
          <div class="rank-badge rank-1">1</div>
        </div>
        <div class="first-celeb-info">
          <div class="celeb-rank">🥇 1위</div>
          <div class="celeb-name">${item.celeb_name}</div>
          <div class="celeb-match-msg">${matchMsg}</div>
          <div class="celeb-score">
            <div class="bar"><div class="bar-fill" data-bar style="width:0%"></div></div>
            <div class="score">
              <span class="score-label">유사도</span>
              <span class="score-value" data-score-animate="${item.similarity_100}">0</span>
              <span class="score-unit">점</span>
            </div>
          </div>
        </div>
      `;
      firstPlaceContainer.appendChild(card);

      // 점수 애니메이션
      setTimeout(() => {
        const barFill = card.querySelector('.bar-fill');
        const scoreEl = card.querySelector('[data-score-animate]');
        if (barFill) barFill.style.width = `${item.similarity_100}%`;
        if (scoreEl) animateScore(scoreEl, item.similarity_100, 1200);
      }, 300);

    } else if (runnersUpContainer) {
      // 2, 3등: 기존 작은 카드로 렌더링
      const card = document.createElement("div");
      card.className = `celeb-card rank-${item.rank}`;

      card.innerHTML = `
        <div class="celeb-header">
          <div class="celeb-image-wrap">
            <img class="celeb-image" src="${celebImageUrl}" alt="${item.celeb_name}">
            <div class="rank-badge rank-${item.rank}">${item.rank}</div>
          </div>
          <div class="celeb-info">
            <div class="celeb-rank">${medalByRank(item.rank)} ${item.rank}위</div>
            <div class="celeb-name">${item.celeb_name}</div>
            <div class="celeb-match-msg">${matchMsg}</div>
          </div>
        </div>
        <div class="celeb-score">
          <div class="bar"><div class="bar-fill" data-bar style="width:0%"></div></div>
          <div class="score">
            <span class="score-label">유사도</span>
            <span class="score-value" data-score-animate="${item.similarity_100}">0</span>
            <span class="score-unit">점</span>
          </div>
        </div>
      `;
      runnersUpContainer.appendChild(card);

      // 점수 애니메이션 (딜레이)
      setTimeout(() => {
        const barFill = card.querySelector('.bar-fill');
        const scoreEl = card.querySelector('[data-score-animate]');
        if (barFill) barFill.style.width = `${item.similarity_100}%`;
        if (scoreEl) animateScore(scoreEl, item.similarity_100, 1200);
      }, 300 + (item.rank - 1) * 200);
    }
  }

  // 버튼 이벤트
  const btnRetry = root.querySelector("[data-btn-retry]");
  const btnDownload = root.querySelector("[data-btn-download]");
  if (btnRetry) btnRetry.onclick = onRetry;
  if (btnDownload) btnDownload.onclick = onDownload;
}
