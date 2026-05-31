"""
Korean profanity / spam / hate-speech filter.

• PROFANITY_LIST  – ~90 terms (욕설 · 광고성 · 혐오)
• check_profanity(text) → (is_clean: bool, matched_words: list[str])
"""

import re
import logging

logger = logging.getLogger('core.security')

# ──────────────────────────────────────────────
# 금칙어 목록
# ──────────────────────────────────────────────
PROFANITY_LIST: list[str] = [
    # ── 욕설 / 비속어 ────────────────────────
    '시발', '씨발', '씨빨', '씨팔', 'ㅅㅂ', 'ㅆㅂ', 'ㅅㅃ',
    '개새끼', 'ㄱㅅㄲ', '개색끼', '개세끼', '개쉑',
    '병신', 'ㅂㅅ', '빙신', '벼ㅇ신',
    '지랄', 'ㅈㄹ', '짓거리',
    '닥쳐', '꺼져', '엿먹어', '죽어', '뒤져', '뒤져라',
    '미친놈', '미친년', '미친새끼', '미친', '미틴',
    '또라이', '돌아이', '돌았네',
    '멍청이', '바보', '등신', '저능아',
    '좆', '좃', 'ㅈ같', '좆같',
    '느금마', '느금', 'ㄴㄱㅁ', '니미', '니엄마',
    '새끼', 'ㅅㄲ', '색히', '쌔끼',
    '창녀', '걸레', '보지', '자지',
    '쓰레기', '쓰렉이', '찐따', '흉자',
    '꼴통', '한심', '찐찌버거',
    '섹스', '강간', '성폭행',
    '패드립', '충동', '자살해',
    '애미', '애비', '에미', '에비',
    '개돼지', '개쥐', '개좆',
    '빡대가리', '대가리', '빡빡이',

    # ── 광고성 / 스팸 ────────────────────────
    '카톡', '텔레', '텔레그램', '오픈채팅', '오픈카톡',
    '부업', '재택알바', '재택부업', '투잡',
    '수익보장', '수익인증', '일당보장',
    '무료상담', '무료체험', '선착순',
    '대출', '급전', '소액대출', '당일대출',
    '코인', '비트코인', '리딩방', '주식리딩',
    '카지노', '도박', '슬롯', '바카라', '토토', '배팅',
    'bit.ly', 'tinyurl', 'goo.gl', 'me2.do',

    # ── 혐오 / 차별 ──────────────────────────
    '한남', '한녀', '한남충', '한녀충',
    '김치녀', '된장녀', '맘충',
    '틀딱', '급식충', '진지충',
    '똥꼬충', '똥남', '정신병자',
    '장애인비하', '흑형', '깜둥이',
    '쪽바리', '짱깨', '짱개', '느그나라',
]

# ──────────────────────────────────────────────
# 자모 사이 공백 제거  (예: 'ㅅ ㅂ' → 'ㅅㅂ')
# 한글 자모 범위: ㄱ(0x3131) – ㅣ(0x3163)
# ──────────────────────────────────────────────
_JAMO_RE = re.compile(r'([\u3131-\u3163])\s+([\u3131-\u3163])')


def _normalize(text: str) -> str:
    """검사 전 텍스트 정규화."""
    # 1) 소문자 통일 (영어)
    text = text.lower()
    # 2) 자모 사이 공백 반복 제거
    prev = None
    while prev != text:
        prev = text
        text = _JAMO_RE.sub(r'\1\2', text)
    return text


def check_profanity(text: str) -> tuple[bool, list[str]]:
    """
    텍스트에서 금칙어를 검사합니다.

    Returns:
        (is_clean, matched_words)
        is_clean=True  → 문제 없음
        is_clean=False → matched_words 에 걸린 단어 목록
    """
    normalized = _normalize(text)
    matched: list[str] = []

    for word in PROFANITY_LIST:
        if word.lower() in normalized:
            matched.append(word)

    is_clean = len(matched) == 0

    if not is_clean:
        logger.warning(
            "Profanity detected: matched=%s | original_text=%s",
            matched, text[:200],
        )

    return is_clean, matched
