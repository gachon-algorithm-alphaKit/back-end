# core/utils/course_search.py

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.courses = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, info):
        word = word.lower()
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.courses.append(info)

    def starts_with(self, prefix):
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
        if node.is_end:
            for c in node.courses:
                if c['course_id'] not in seen:
                    seen.add(c['course_id'])
                    results.append(c)
        for child in node.children.values():
            self._dfs(child, results, seen)


class HashTable:
    def __init__(self, size=2003):
        self.size = size
        self.table = [[] for _ in range(size)]

    def _hash(self, key):
        h = 0
        for ch in str(key):
            h = (h * 31 + ord(ch)) % self.size
        return h

    def put(self, key, value):
        idx = self._hash(key)
        for i, (k, _) in enumerate(self.table[idx]):
            if k == key:
                self.table[idx][i] = (key, value)
                return
        self.table[idx].append((key, value))

    def get(self, key):
        idx = self._hash(key)
        for k, v in self.table[idx]:
            if k == key:
                return v
        return None

CHOSEONG_LIST = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ',
                 'ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
CHOSEONG_SET = set(CHOSEONG_LIST)

def to_choseong(text):
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
    return bool(text) and all(ch in CHOSEONG_SET for ch in text)

def rabin_karp(text, pattern, base=256, mod=10**9 + 7):
    if not text or not pattern:
        return False
    text = text.lower()
    pattern = pattern.lower()
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return False
    ph, th, h = 0, 0, 1
    for _ in range(m - 1):
        h = (h * base) % mod
    for i in range(m):
        ph = (ph * base + ord(pattern[i])) % mod
        th = (th * base + ord(text[i]))    % mod
    for i in range(n - m + 1):
        if ph == th and text[i:i+m] == pattern:
            return True
        if i < n - m:
            th = (base * (th - ord(text[i]) * h) + ord(text[i+m])) % mod
            th = (th + mod) % mod
    return False

class CourseSearchEngine:
    def __init__(self):
        self.trie_name     = Trie()
        self.trie_prof     = Trie()
        self.trie_name_cho = Trie()
        self.trie_prof_cho = Trie()
        self.hash_table = HashTable()
        self.courses = []
        self.is_loaded = False

    def load_data(self):
        from core.models import Course
        
        self.trie_name     = Trie()
        self.trie_prof     = Trie()
        self.trie_name_cho = Trie()
        self.trie_prof_cho = Trie()
        self.hash_table = HashTable()
        self.courses = []
        
        # Load from DB
        qs = Course.objects.all().select_related('professor', 'school')
        
        for r in qs:
            info = {
                'course_id': r.course_id,
                'course_code': r.course_code or '',
                'course_name': r.course_name or '',
                'professor_name': r.professor.name if r.professor else '',
                'major_term': '', # Empty since not in models currently
                'day_of_week': r.day_of_week or '',
                'start_time': r.start_time.strftime('%H:%M:%S') if r.start_time else '',
                'end_time': r.end_time.strftime('%H:%M:%S') if r.end_time else '',
                'description': r.description or ''
            }
            name = info['course_name']
            prof = info['professor_name']
            
            if name:
                self.trie_name.insert(name, info)
                self.trie_name_cho.insert(to_choseong(name), info)
            if prof:
                self.trie_prof.insert(prof, info)
                self.trie_prof_cho.insert(to_choseong(prof), info)
                
            self.hash_table.put(info['course_id'], info)
            self.courses.append(info)
            
        self.is_loaded = True

    def autocomplete(self, prefix, by='name'):
        if by == 'name':      return self.trie_name.starts_with(prefix)
        if by == 'professor': return self.trie_prof.starts_with(prefix)
        return []

    def autocomplete_choseong(self, prefix, by='name'):
        if by == 'name':      return self.trie_name_cho.starts_with(prefix)
        if by == 'professor': return self.trie_prof_cho.starts_with(prefix)
        return []

    def search_keyword_in_field(self, keyword, field='name'):
        key = 'course_name' if field == 'name' else 'professor_name'
        return [c for c in self.courses if rabin_karp(c[key], keyword)]

    def search_choseong_in_field(self, keyword, field='name'):
        key = 'course_name' if field == 'name' else 'professor_name'
        return [c for c in self.courses if rabin_karp(to_choseong(c[key]), keyword)]

    def search_by_content(self, keyword):
        return [c for c in self.courses
                if c['description'] and rabin_karp(c['description'], keyword)]

    def find_by_id(self, course_id):
        return self.hash_table.get(course_id)

    def search(self, query, field):
        # query.lower() to ensure case-insensitivity consistency across checks
        q_lower = query.lower()
        if is_choseong_only(query):
            prefix_results = self.autocomplete_choseong(query, by=field)
            partial_results = self.search_choseong_in_field(query, field=field)
        else:
            prefix_results = self.autocomplete(query, by=field)
            partial_results = self.search_keyword_in_field(query, field=field)
            
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

# Singleton instance
search_engine = CourseSearchEngine()
