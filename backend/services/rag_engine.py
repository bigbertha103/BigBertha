import hashlib
import logging
import os
from pathlib import Path

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
                    # Découper le paragraphe long par phrases
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
                                # Découper par caractères en dernier recours
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
            logger.error("Erreur lecture PDF %s : %s", file_path.name, exc)
            raise

    @staticmethod
    def _load_docx(file_path: Path) -> str:
        try:
            import docx
            doc = docx.Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as exc:
            logger.error("Erreur lecture DOCX %s : %s", file_path.name, exc)
            raise

    @staticmethod
    def load_doc(path: Path) -> str:
        # Stratégie 1 : essayer python-docx (fonctionne sur .doc récents)
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            pass
        # Stratégie 2 : lire comme texte brut (fonctionne pour .doc = HTML/RTF web)
        import re
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                raw = path.read_text(encoding=enc)
                clean = re.sub(r"<[^>]+>", " ", raw)
                clean = re.sub(r"\s+", " ", clean).strip()
                if len(clean) > 100:
                    return clean
            except Exception:
                continue
        return ""

    @classmethod
    def load(cls, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix not in cls.SUPPORTED:
            raise ValueError(f"Extension non supportée : {suffix}")
        if suffix == ".pdf":
            return cls._load_pdf(file_path)
        if suffix == ".docx":
            return cls._load_docx(file_path)
        if suffix == ".doc":
            return cls.load_doc(file_path)
        return cls._load_text(file_path)


# ── RAGManager ────────────────────────────────────────────────────

class RAGManager:
    def __init__(self, collection_name: str, persist_dir: str, embedding_model: str):
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._embedding_model = embedding_model

        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._ef = DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._ef,
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

        self._collection.add(documents=chunks, ids=ids, metadatas=metas)
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
            results = self._collection.query(
                query_texts=[query],
                n_results=n,
            )
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
        """Indexe un texte brut directement (sans passer par un fichier)."""
        meta = dict(metadata) if metadata else {}
        try:
            self._collection.upsert(documents=[text], ids=[doc_id], metadatas=[meta])
            logger.info("session_memory — bilan indexé id=%s", doc_id)
        except Exception as exc:
            logger.error("session_memory — erreur indexation id=%s : %s", doc_id, exc)

    def get_collection_info(self) -> dict:
        return {"name": self._collection_name, "count": self._collection.count()}

    def delete_collection(self) -> None:
        self._client.delete_collection(name=self._collection_name)
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
