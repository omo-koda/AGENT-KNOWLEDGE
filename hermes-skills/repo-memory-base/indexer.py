from pathlib import Path
import json, time, re
from typing import List, Dict, Any, Optional

class RepoMemoryEngine:
    def __init__(self, index_path: str = None, repo_path: str = None):
        self.index_path = index_path or '/Users/bino/.hermes/skills/repo-memory-base/index.json'
        self.repo_path_default = repo_path or '/Users/bino/AGENT-KNOWLEDGE'
        self.docs: List[Dict[str, Any]] = []
        self.updated: Optional[int] = None
        self._load_index()
        if self.docs is None:
            self.docs = []

    def _load_index(self):
        try:
            with open(self.index_path, 'r') as f:
                data = json.load(f)
            self.docs = data.get('docs', [])
            self.updated = data.get('updated')
        except FileNotFoundError:
            self.docs = []
            self.updated = None
        except Exception as e:
            print(f"Error loading index from {self.index_path}: {e}")
            self.docs = []
            self.updated = None

    def _save_index(self):
        try:
            root = Path(self.index_path).parent
            root.mkdir(parents=True, exist_ok=True)
            with open(self.index_path, 'w') as f:
                json.dump({'docs': self.docs, 'updated': int(time.time())}, f, indent=2)
        except Exception as e:
            print(f"Error saving index to {self.index_path}: {e}")

    @staticmethod
    def _tokenize(text: str):
        if not text:
            return []
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        return tokens

    def load_repo(self, repo_path: Optional[str] = None, max_files: int = 1000, file_extensions: List[str] = ['.md', '.txt', '.mdx', '.markdown', '.py', '.js', '.yaml', '.yml', '.json', '.sh']):
        repo = Path(repo_path or self.repo_path_default)
        if not repo.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path or self.repo_path_default}")
        
        docs = []
        count = 0
        for p in repo.rglob('*'):
            if p.is_dir():
                continue
            if '/.git/' in str(p.resolve()):
                continue
            ext = p.suffix.lower()
            # Allow indexing of files with no extension as text content
            if ext and ext not in file_extensions:
                continue
            try:
                data = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if not data or len(data.strip()) < 10:
                continue

            docs.append({
                'path': str(p.resolve()),
                'title': p.name,
                'content': data,
                'length': len(data)
            })
            count += 1
            if count >= max_files:
                break
        
        self.docs = docs
        self._save_index()
        return len(docs)

    def _score_doc(self, query_tokens: List[str], doc: Dict[str, Any]) -> float:
        text = doc.get('content', '')
        if not text:
            return 0.0
        tokens = self._tokenize(text)
        if not tokens:
            return 0.0
        
        token_set = set(tokens)
        score = 0.0
        for t in query_tokens:
            if t in token_set:
                score += 1.0
        
        doc_length = doc.get('length', 1.0)
        if doc_length > 0:
            score = score / (1.0 + doc_length / 1000.0)
        return score

    def query_repo(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        if not self.docs:
            return []
        qtokens = self._tokenize(query)
        if not qtokens:
            return []
        
        scored_docs = []
        for d in self.docs:
            s = self._score_doc(qtokens, d)
            if s > 0:
                scored_docs.append((s, d))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for s, d in scored_docs[:top_k]:
            snippet = d.get('content', '')[:400]
            results.append({
                'path': d['path'],
                'title': d['title'],
                'snippet': snippet.replace('\n', ' ')
            })
        return results

    def show_doc(self, index: int) -> Optional[Dict[str, str]]:
        if index < 0 or index >= len(self.docs):
            return None
        d = self.docs[index]
        return {
            'path': d['path'],
            'title': d['title'],
            'content': d['content']
        }

    def status(self) -> Dict[str, Any]:
        return {
            'docs_count': len(self.docs),
            'index_path': self.index_path,
            'repo_path': self.repo_path_default,
            'updated': self.updated
        }

if __name__ == '__main__':
    engine = RepoMemoryEngine()
    if not engine.docs:
        print('Indexing repo (extensionless allowed)...')
        engine.load_repo('/Users/bino/AGENT-KNOWLEDGE', max_files=1000)
        print('Docs indexed:', len(engine.docs))
        engine._save_index()
    print('Status:', engine.status())
