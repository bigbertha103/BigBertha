import hashlib
import json
import logging
import os
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


# ── CustomTextSplitter ────────────────────────────────────────────

class CustomTextSplitter:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 <= self._chunk_size:
                current = (current + "\n\n" + para).strip() if current else para
            else:
                if current:
                    chunks.append(current)
                if len(para) <= self._chunk_size:
                    current = para
                else:
                    sentences = para.replace(". ", ".\n").replace("! ", "!\n").replace("? ", "?\n").split("\n")
                    for sent in sentences:
                        sent = sent.strip()
                        if not sent:
                            continue
                        if len(current) + len(sent) + 1 <= self._chunk_size:
                            current = (current + " " + sent).strip() if current else sent
                        else:
                            if current:
                                chunks.append(current)
                            if len(sent) <= self._chunk_size:
                                current = sent
                            else:
                                for i in range(0, len(sent), self._chunk_size - self._chunk_overlap):
                                    piece = sent[i:i + self._chunk_size]
                                    if piece.strip():
                                        chunks.append(piece.strip())
                                current = ""

        if current:
            chunks.append(current)

        return [c for c in chunks if c.strip()]


# ── DocumentLoader ────────────────────────────────────────────────

class DocumentLoader:
    SUPPORTED = {".txt", ".md", ".py", ".pdf", ".docx", ".doc"}

    @staticmethod
    def _load_text(file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1")

    @staticmethod
    def _load_pdf(file_path: Path) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except Exception as exc:
            logger.warning("Erreur lecture PDF %s : %s", file_path.name, exc)
            return ""

    @staticmethod
    def _load_docx(file_path: Path) -> str:
        try:
            import docx
            doc = docx.Document(str(file_path))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as exc:
            logger.warning("Erreur lecture DOCX %s : %s", file_path.name, exc)
            return ""

    @classmethod
    def load(cls, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return cls._load_pdf(file_path)
        if suffix in {".docx", ".doc"}:
            return cls._load_docx(file_path)
        if suffix in {".txt", ".md", ".py"}:
            return cls._load_text(file_path)
        logger.warning("Extension non supportée : %s", suffix)
        return ""


# ── BagOfWordsEmbeddingFunction ───────────────────────────────────

class _BagOfWordsEmbeddingFunction:
    _DIM = 384

    def name(self) -> str:
        return "bag_of_words_384"

    def __call__(self, input: list[str]) -> list[list[float]]:
        import re
        result = []
        for text in input:
            vec = np.zeros(self._DIM, dtype=np.float32)
            tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
            for token in tokens:
                vec[hash(token) % self._DIM] += 1.0
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm
            result.append(vec.tolist())
        return result


# ── SimpleVectorStore — remplace ChromaDB ────────────────────────

class SimpleVectorStore:
    """Vector store pure Python/numpy, compatible Python 3.14+."""

    _DIM = 384

    def __init__(self, persist_dir: str, collection_name: str):
        self._dir = Path(persist_dir) / collection_name
        self._dir.mkdir(parents=True, exist_ok=True)
        self._vectors_file = self._dir / "vectors.npz"
        self._meta_file = self._dir / "metadata.json"
        self._load()

    def _load(self):
        if self._vectors_file.exists() and self._meta_file.exists():
            try:
                data = np.load(str(self._vectors_file), allow_pickle=True)
                self._ids: list[str] = list(data["ids"])
                self._embeddings: np.ndarray = data["embeddings"]
                self._documents: list[str] = list(data["documents"])
                with open(self._meta_file, encoding="utf-8") as f:
                    self._metadatas: list[dict] = json.load(f)
                return
            except Exception as exc:
                logger.warning("Impossible de charger le vector store, réinitialisation : %s", exc)
        self._ids = []
        self._embeddings = np.zeros((0, self._DIM), dtype=np.float32)
        self._documents = []
        self._metadatas = []

    def _save(self):
        np.savez(
            str(self._vectors_file),
            ids=np.array(self._ids, dtype=object),
            embeddings=self._embeddings,
            documents=np.array(self._documents, dtype=object),
        )
        with open(self._meta_file, "w", encoding="utf-8") as f:
            json.dump(self._metadatas, f, ensure_ascii=False)

    def count(self) -> int:
        return len(self._ids)

    def add(
        self,
        documents: list[str],
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ):
        emb = np.array(embeddings, dtype=np.float32)
        self._ids.extend(ids)
        self._documents.extend(documents)
        self._metadatas.extend(metadatas or [{} for _ in ids])
        self._embeddings = np.vstack([self._embeddings, emb]) if self._embeddings.shape[0] > 0 else emb
        self._save()

    def upsert(
        self,
        documents: list[str],
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ):
        existing = {id_: i for i, id_ in enumerate(self._ids)}
        for doc, id_, emb, meta in zip(
            documents, ids, embeddings, metadatas or [{} for _ in ids]
        ):
            if id_ in existing:
                idx = existing[id_]
                self._documents[idx] = doc
                self._metadatas[idx] = meta
                self._embeddings[idx] = np.array(emb, dtype=np.float32)
            else:
                self._ids.append(id_)
                self._documents.append(doc)
                self._metadatas.append(meta)
                new_emb = np.array([emb], dtype=np.float32)
                self._embeddings = np.vstack([self._embeddings, new_emb]) if self._embeddings.shape[0] > 0 else new_emb
        self._save()

    def delete(self, ids: list[str]):
        to_remove = set(ids)
        keep = [i for i, id_ in enumerate(self._ids) if id_ not in to_remove]
        self._ids = [self._ids[i] for i in keep]
        self._documents = [self._documents[i] for i in keep]
        self._metadatas = [self._metadatas[i] for i in keep]
        self._embeddings = self._embeddings[keep] if keep else np.zeros((0, self._DIM), dtype=np.float32)
        self._save()

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 3,
    ) -> dict:
        if self.count() == 0:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
        q = np.array(query_embeddings[0], dtype=np.float32)
        q_norm = float(np.linalg.norm(q))
        if q_norm > 0:
            q = q / q_norm
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        normed = np.where(norms > 0, self._embeddings / norms, self._embeddings)
        sims = normed @ q
        n = min(n_results, self.count())
        top_idx = np.argsort(-sims)[:n].tolist()
        return {
            "documents": [[self._documents[i] for i in top_idx]],
            "metadatas": [[self._metadatas[i] for i in top_idx]],
            "ids": [[self._ids[i] for i in top_idx]],
            "distances": [[float(1.0 - sims[i]) for i in top_idx]],
        }


# ── RAGManager ────────────────────────────────────────────────────

class RAGManager:
    def __init__(self, collection_name: str, persist_dir: str, embedding_model: str):
        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._embedding_model = embedding_model

        self._ef = _BagOfWordsEmbeddingFunction()
        self._collection = SimpleVectorStore(
            persist_dir=persist_dir,
            collection_name=collection_name,
        )
        logger.info(
            "RAGManager — collection '%s' prête (%d docs)",
            collection_name,
            self._collection.count(),
        )

    def add_document(
        self,
        file_path: Path,
        chunk_size: int = 400,
        chunk_overlap: int = 50,
        metadata: dict | None = None,
    ) -> list[str]:
        text = DocumentLoader.load(file_path)
        splitter = CustomTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_text(text)
        if not chunks:
            logger.warning("Aucun chunk produit pour %s", file_path.name)
            return []

        base_meta = {
            "filename": file_path.name,
            "file_type": file_path.suffix.lstrip(".").lower(),
        }
        if metadata:
            base_meta.update(metadata)

        filename_hash = hashlib.md5(file_path.name.encode()).hexdigest()[:8]
        ids = [f"{filename_hash}_{file_path.stem}_chunk_{i}" for i in range(len(chunks))]
        metas = [dict(base_meta) for _ in chunks]
        embeddings = self._ef(chunks)

        self._collection.add(documents=chunks, ids=ids, embeddings=embeddings, metadatas=metas)
        logger.info("Document '%s' indexé — %d chunks", file_path.name, len(chunks))
        return ids

    def delete_document(self, chunk_ids: list[str]) -> None:
        self._collection.delete(ids=chunk_ids)
        logger.info("Suppression %d chunks", len(chunk_ids))

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        try:
            count = self._collection.count()
            if count == 0:
                return []
            n = min(top_k, count)
            q_emb = self._ef([query])
            results = self._collection.query(query_embeddings=q_emb, n_results=n)
            output = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            for doc, meta, dist in zip(docs, metas, distances):
                output.append({"document": doc, "metadata": meta or {}, "distance": dist})
            return output
        except Exception as exc:
            logger.error("Erreur recherche RAG : %s", exc)
            return []

    def get_context_for_query(self, query: str, top_k: int = 3) -> str:
        results = self.search(query, top_k)
        if not results:
            return ""
        parts = []
        for r in results:
            source = r.get("metadata", {}).get("filename", "document")
            parts.append(f"[Source : {source}]\n{r['document']}")
        return "\n\n---\n\n".join(parts)

    def add_text(self, text: str, doc_id: str, metadata: dict | None = None) -> None:
        meta = dict(metadata) if metadata else {}
        try:
            emb = self._ef([text])
            self._collection.upsert(documents=[text], ids=[doc_id], embeddings=emb, metadatas=[meta])
            logger.info("session_memory — bilan indexé id=%s", doc_id)
        except Exception as exc:
            logger.error("session_memory — erreur indexation id=%s : %s", doc_id, exc)

    def get_collection_info(self) -> dict:
        return {"name": self._collection_name, "count": self._collection.count()}

    def delete_collection(self) -> None:
        import shutil
        coll_dir = Path(self._persist_dir) / self._collection_name
        if coll_dir.exists():
            shutil.rmtree(str(coll_dir))
        logger.info("Collection '%s' supprimée", self._collection_name)


# ── Singleton module-level ────────────────────────────────────────

_manager: RAGManager | None = None


def init_rag(collection_name: str | None = None) -> RAGManager:
    global _manager
    collection = collection_name or os.getenv("RAG_COLLECTION_NAME", "bigbertha_prod")
    persist_dir = os.getenv("RAG_PERSIST_DIR", "backend/data/chroma_db")
    model = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    _manager = RAGManager(
        collection_name=collection,
        persist_dir=persist_dir,
        embedding_model=model,
    )
    return _manager


def get_rag() -> RAGManager | None:
    return _manager


_session_manager: RAGManager | None = None


def init_session_rag() -> RAGManager:
    global _session_manager
    collection = os.getenv("RAG_SESSION_COLLECTION_NAME", "session_memory")
    persist_dir = os.getenv("RAG_PERSIST_DIR", "backend/data/chroma_db")
    model = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    _session_manager = RAGManager(
        collection_name=collection,
        persist_dir=persist_dir,
        embedding_model=model,
    )
    return _session_manager


def get_session_rag() -> RAGManager | None:
    return _session_manager
