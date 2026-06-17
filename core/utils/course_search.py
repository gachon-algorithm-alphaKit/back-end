# 실행 환경: Python 3.x, Django
# 필요 라이브러리: django (ORM), 표준 라이브러리만 사용 (별도 설치 불필요)
# Input 데이터 출처: 가천대학교 강의 정보 (직접 수집 후 DB 저장)
#   - DB 모델: core.models.Course
#   - 필드: course_name, professor_name, description, day_of_week, start_time, end_time

# 자료구조: Trie (k진 트리 / 접두사 트리)
# - 강의명·교수명·초성 접두사 자동완성을 위해 4개 Trie 인스턴스 사용
# - 접두사 탐색: O(접두사 길이 + 결과 수)  vs 단순 리스트 O(n×m)
class TrieNode:
    def __init__(self):
        self.children = {}   # 자식 노드 딕셔너리 (문자 → TrieNode)
        self.is_end = False  # 단어 끝 여부
        self.courses = []    # 해당 접두사에 대응하는 강의 정보 리스트


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, info):
        # Trie 삽입: 단어 각 문자를 노드로 연결
        word = word.lower()
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.courses.append(info)

    def starts_with(self, prefix):
        # 알고리즘: Trie 탐색 (접두사 자동완성) - O(접두사 길이 + 결과 수)
        prefix = prefix.lower()
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        results, seen = [], set()
        self._dfs(node, results, seen)
        return results

    def _dfs(self, node, results, seen):
        # DFS로 접두사 하위 모든 강의 수집 (course_id 기준 중복 제거)
        if node.is_end:
            for c in node.courses:
                if c['course_id'] not in seen:
                    seen.add(c['course_id'])
                    results.append(c)
        for child in node.children.values():
            self._dfs(child, results, seen)


# 자료구조: Hash Table (해시 테이블)
# - course_id → 강의 정보 O(1) 조회, 충돌은 체이닝(버킷별 리스트)으로 처리
# - 크기 2003 (소수 사용으로 해시 충돌 최소화)
class HashTable:
    def __init__(self, size=2003):
        self.size = size
        self.table = [[] for _ in range(size)]  # 버킷 배열 (체이닝)

    def _hash(self, key):
        # 해시 함수: 다항식 롤링 해시 (base=31)
        h = 0
        for ch in str(key):
            h = (h * 31 + ord(ch)) % self.size
        return h

    def put(self, key, value):
        # 삽입: 동일 키 존재 시 갱신, 없으면 버킷에 추가 (체이닝)
        idx = self._hash(key)
        for i, (k, _) in enumerate(self.table[idx]):
            if k == key:
                self.table[idx][i] = (key, value)
                return
        self.table[idx].append((key, value))

    def get(self, key):
        # 조회: O(1) 평균 - course_id로 강의 정보 직접 접근
        idx = self._hash(key)
        for k, v in self.table[idx]:
            if k == key:
                return v
        return None


# 초성 변환 유틸리티 (초성 검색 지원)
CHOSEONG_LIST = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ',
                 'ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
CHOSEONG_SET = set(CHOSEONG_LIST)

def to_choseong(text):
    """한글 문자열을 초성으로 변환 (예: '자료구조' → 'ㅈㄹㄱㅈ')"""
    if not text:
        return ""
    result = []
    for ch in text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            result.append(CHOSEONG_LIST[(code - 0xAC00) // 588])
        else:
            result.append(ch)
    return ''.join(result)

def is_choseong_only(text):
    """입력값이 초성으로만 구성되어 있는지 판별"""
    return bool(text) and all(ch in CHOSEONG_SET for ch in text)


def rabin_karp(text, pattern, base=256, mod=10**9 + 7):
    """
    알고리즘: Rabin-Karp (라빈-카프 롤링 해시 기반 부분 문자열 탐색)
    - 강의명·교수명·강의설명(description) 내 키워드 부분 일치 탐색
    - 시간복잡도: 평균 O(n+m), 최악 O(n×m) (n=텍스트 길이, m=패턴 길이)
    - base=256, mod=10^9+7 (소수 → 충돌 최소화)
    """
    if not text or not pattern:
        return False
    text = text.lower()
    pattern = pattern.lower()
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return False

    ph, th, h = 0, 0, 1

    # 최고차항 계수 h = base^(m-1) % mod
    for _ in range(m - 1):
        h = (h * base) % mod

    # 첫 번째 윈도우 해시값 초기화
    for i in range(m):
        ph = (ph * base + ord(pattern[i])) % mod
        th = (th * base + ord(text[i]))    % mod

    # 슬라이딩 윈도우로 탐색 (롤링 해시: 맨 앞 문자 제거 + 새 문자 추가)
    for i in range(n - m + 1):
        if ph == th and text[i:i+m] == pattern:  # 해시 일치 후 실제 문자열 검증
            return True
        if i < n - m:
            th = (base * (th - ord(text[i]) * h) + ord(text[i+m])) % mod
            th = (th + mod) % mod

    return False


class CourseSearchEngine:
    """
    강의 검색 엔진 (싱글톤)
    - Trie 4개: 강의명/교수명 × 일반/초성 접두사 탐색
    - HashTable 1개: course_id → 강의 정보 O(1) 조회
    - Rabin-Karp: 부분 일치 탐색 (Trie 결과와 병합)
    """
    def __init__(self):
        # 자료구조: Trie - 강의명/교수명/초성 4개 인스턴스
        self.trie_name     = Trie()   # 강의명 일반 탐색
        self.trie_prof     = Trie()   # 교수명 일반 탐색
        self.trie_name_cho = Trie()   # 강의명 초성 탐색
        self.trie_prof_cho = Trie()   # 교수명 초성 탐색

        # 자료구조: HashTable - course_id → 강의 정보 O(1) 조회
        self.hash_table = HashTable()

        self.courses = []        # 전체 강의 리스트 (Rabin-Karp 선형 탐색용)
        self.is_loaded = False

    def load_data(self):
        """서버 기동 시 DB에서 전체 강의 데이터를 읽어 Trie + HashTable 구성"""
        from core.models import Course

        self.trie_name     = Trie()
        self.trie_prof     = Trie()
        self.trie_name_cho = Trie()
        self.trie_prof_cho = Trie()
        self.hash_table    = HashTable()
        self.courses       = []

        qs = Course.objects.all().select_related('professor', 'school')

        for r in qs:
            info = {
                'course_id'     : r.course_id,
                'course_code'   : r.course_code or '',
                'course_name'   : r.course_name or '',
                'professor_name': r.professor.name if r.professor else '',
                'major_term'    : '',
                'day_of_week'   : r.day_of_week or '',
                'start_time'    : r.start_time.strftime('%H:%M:%S') if r.start_time else '',
                'end_time'      : r.end_time.strftime('%H:%M:%S') if r.end_time else '',
                'description'   : r.description or ''
            }
            name = info['course_name']
            prof = info['professor_name']

            # Trie 삽입: 강의명/교수명 + 초성 변환 후 삽입
            if name:
                self.trie_name.insert(name, info)
                self.trie_name_cho.insert(to_choseong(name), info)
            if prof:
                self.trie_prof.insert(prof, info)
                self.trie_prof_cho.insert(to_choseong(prof), info)

            # HashTable 삽입: course_id → 강의 정보
            self.hash_table.put(info['course_id'], info)
            self.courses.append(info)

        self.is_loaded = True

    def autocomplete(self, prefix, by='name'):
        # 알고리즘: Trie 탐색 - 일반 접두사 자동완성
        if by == 'name':      return self.trie_name.starts_with(prefix)
        if by == 'professor': return self.trie_prof.starts_with(prefix)
        return []

    def autocomplete_choseong(self, prefix, by='name'):
        # 알고리즘: Trie 탐색 - 초성 접두사 자동완성
        if by == 'name':      return self.trie_name_cho.starts_with(prefix)
        if by == 'professor': return self.trie_prof_cho.starts_with(prefix)
        return []

    def search_keyword_in_field(self, keyword, field='name'):
        # 알고리즘: Rabin-Karp - 강의명 또는 교수명 내 부분 일치 탐색
        key = 'course_name' if field == 'name' else 'professor_name'
        return [c for c in self.courses if rabin_karp(c[key], keyword)]

    def search_choseong_in_field(self, keyword, field='name'):
        # 알고리즘: Rabin-Karp - 초성 변환 후 부분 일치 탐색
        key = 'course_name' if field == 'name' else 'professor_name'
        return [c for c in self.courses if rabin_karp(to_choseong(c[key]), keyword)]

    def search_by_content(self, keyword):
        # 알고리즘: Rabin-Karp - 강의 설명(description) 내 키워드 탐색
        return [c for c in self.courses
                if c['description'] and rabin_karp(c['description'], keyword)]

    def find_by_id(self, course_id):
        # 자료구조: HashTable 조회 - course_id → 강의 정보 O(1)
        return self.hash_table.get(course_id)

    def search(self, query, field):
        """
        통합 검색: Trie(접두사 일치) + Rabin-Karp(부분 일치) 결합
        1. is_choseong_only()로 초성 입력 여부 판별
        2-A. 초성: 초성 Trie 탐색 + 초성 Rabin-Karp 탐색
        2-B. 일반: 일반 Trie 탐색 + 일반 Rabin-Karp 탐색
        3. course_id 기준 중복 제거 후 [접두사 일치 → 부분 일치] 순 병합 반환
        """
        if is_choseong_only(query):
            # 초성 입력: Trie 초성 탐색 + Rabin-Karp 초성 탐색
            prefix_results  = self.autocomplete_choseong(query, by=field)
            partial_results = self.search_choseong_in_field(query, field=field)
        else:
            # 일반 입력: Trie 탐색 + Rabin-Karp 탐색
            prefix_results  = self.autocomplete(query, by=field)
            partial_results = self.search_keyword_in_field(query, field=field)

        # course_id 기준 중복 제거 후 병합 (접두사 일치 우선)
        seen = set()
        results = []
        for c in prefix_results:
            if c['course_id'] not in seen:
                seen.add(c['course_id'])
                results.append(c)
        for c in partial_results:
            if c['course_id'] not in seen:
                seen.add(c['course_id'])
                results.append(c)
        return results


# 싱글톤 인스턴스 (서버 기동 시 apps.py에서 load_data() 호출)
search_engine = CourseSearchEngine()
