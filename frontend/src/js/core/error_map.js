export const ERROR_UI = {
  FACE_NOT_FOUND:   { text: "얼굴이 화면에 안 보여요. 카메라 정면으로 와주세요.", cta: "다시 시도" },
  MULTIPLE_FACES:   { text: "얼굴이 2명 이상 보여요. 1명만 화면에 나오게 해주세요.", cta: "다시 시도" },
  TOO_DARK:         { text: "화면이 너무 어두워요. 조명을 켜주세요.", cta: "다시 시도" },
  TOO_BLURRY:       { text: "화면이 흐려요. 카메라를 고정해 주세요.", cta: "다시 시도" },
  EXPRESSION_WEAK:  { text: "표정이 아직 약해요. 조금 더 크게 지어주세요!", cta: "다시 시도" },
  DECODE_FAIL:      { text: "이미지 처리에 실패했어요. 다시 한 번만 해볼까요?", cta: "다시 시도" },
  TIMEOUT:          { text: "분석이 지연됐어요. 네트워크를 확인해 주세요.", cta: "다시 시도" },
};

export function mapErrorToUi(error_code) {
  return ERROR_UI[error_code] ?? { text: "알 수 없는 오류가 발생했어요.", cta: "다시 시도" };
}
