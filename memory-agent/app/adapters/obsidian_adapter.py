"""
Memory Agent — Obsidian Adapter

Defines the ObsidianAdapter abstract interface and concrete implementations:
  1. LocalObsidianAdapter — Reads, parses, indexes, and searches the real local Obsidian vault files.
  2. MockObsidianAdapter  — In-memory mock adapter seeded with company knowledge for unit testing.

INTEGRATION POINT
─────────────────
The LocalObsidianAdapter indexes local Markdown vault files (*.md) with YAML frontmatter,
headings, tags, and wikilinks. It uses high-performance lexical indexing with BM25 and
metadata boosting (title, headings, tags, exact phrases).

To configure:
  OBSIDIAN_ADAPTER=local
  OBSIDIAN_VAULT_PATH=C:\\Lordminds\\Multiagent\\memory-agent\\obsedian
"""

from __future__ import annotations

import logging
import math
import os
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.models.memory import ApprovalStatus, MemoryResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Custom Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class ObsidianAdapterError(Exception):
    """Raised when the Obsidian adapter itself is unavailable or errors."""


class ObsidianNoteNotFoundError(Exception):
    """Raised when a specific note cannot be found."""


class ObsidianDuplicateError(Exception):
    """Raised when a write would create a duplicate note."""


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Interface
# ─────────────────────────────────────────────────────────────────────────────


class ObsidianAdapter(ABC):
    """
    Abstract adapter for the company's Obsidian knowledge base.

    Implementations must never assume a specific vault schema, folder structure,
    or proprietary API — those details belong in the concrete class.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[MemoryResult]:
        """
        Search the knowledge base for notes relevant to *query*.

        Returns an empty list if nothing is found.
        Must never raise on an empty result — raise only on adapter failure.
        """
        ...

    @abstractmethod
    async def read(self, note_id: str) -> MemoryResult | None:
        """
        Read a specific note by its ID/path.

        Returns None if the note does not exist.
        Raises ObsidianAdapterError on adapter/IO failure.
        """
        ...

    @abstractmethod
    async def list_notes(self, folder: str | None = None) -> list[str]:
        """
        List note IDs/paths in the vault, optionally filtered by folder.
        """
        ...

    @abstractmethod
    async def write(
        self,
        content: str,
        target_note: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Write *content* to *target_note*.

        Returns the note ID of the written note.
        Raises ObsidianDuplicateError if the note already exists and
        overwrite is not permitted.
        """
        ...

    @abstractmethod
    async def update(self, note_id: str, content: str) -> bool:
        """
        Update an existing note.

        Returns True on success.
        Raises ObsidianAdapterError if the note does not exist.
        """
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Helper Utilities
# ─────────────────────────────────────────────────────────────────────────────


def _tokenize(text: str) -> list[str]:
    """Extract lowercase alphanumeric tokens from text."""
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if len(t) > 1]


def _simple_relevance(query: str, content: str, title: str) -> float:
    """Deterministic keyword-based relevance scoring for mock adapter."""
    query_terms = set(query.lower().split())
    text = (title + " " + content).lower()
    if not query_terms:
        return 0.0
    matches = sum(1 for term in query_terms if term in text)
    return round(min(matches / len(query_terms), 1.0), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Query Decomposition & Conversational Stopwords
# ─────────────────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
    "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them", "their",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "want", "need", "build", "create", "make", "implement", "application", "system",
    "platform", "solution", "project", "company", "client", "modern", "complete",
    "proper", "comprehensive", "requires", "require", "provides", "provide",
    "instructions", "instruction", "guide", "guidelines", "manual", "tutorial",
    "method", "methods", "steps", "details", "information", "info", "overview", "like"
}


_GENERIC_CLAUSE_TOKENS = {"web", "application", "platform", "solution", "system", "service", "services", "software", "app"}


def _decompose_query(query: str) -> list[str]:
    """
    Decompose a natural-language client requirement into distinct sub-intents.
    Splits on punctuation, coordinating conjunctions, and prepositions.
    """
    delimiters = r"[,;\.\n]| and | with | using | for | including | such as | as well as | plus | over | via | across "
    clauses = re.split(delimiters, query, flags=re.IGNORECASE)

    sub_intents: list[str] = []
    for c in clauses:
        clean = c.strip()
        tokens = [t for t in _tokenize(clean) if t not in _STOPWORDS]
        if tokens and not set(tokens).issubset(_GENERIC_CLAUSE_TOKENS):
            sub_intents.append(" ".join(tokens))

    return sub_intents


# ─────────────────────────────────────────────────────────────────────────────
# Local Obsidian Vault Document Model & Index
# ─────────────────────────────────────────────────────────────────────────────


class _ParsedNote:
    """Internal representation of a parsed local Obsidian markdown document."""

    def __init__(self, rel_path: str, abs_path: str, raw_content: str) -> None:
        self.rel_path = rel_path.replace("\\", "/")
        self.abs_path = abs_path
        self.raw_content = raw_content
        self.body = raw_content
        self.title = Path(rel_path).stem
        self.frontmatter: dict[str, Any] = {}
        self.tags: list[str] = []
        self.headings: list[str] = []
        self.wikilinks: list[str] = []
        self.category: str = ""
        self.doc_type: str = ""
        self.is_index_doc: bool = False
        self.updated_at: datetime = datetime.now(timezone.utc)
        self._parse()

    def _parse(self) -> None:
        content = self.raw_content
        # 1. Parse YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1])
                    if isinstance(fm, dict):
                        self.frontmatter = fm
                        if "title" in fm and fm["title"]:
                            self.title = str(fm["title"])
                        if "category" in fm and fm["category"]:
                            self.category = str(fm["category"])
                        if "type" in fm and fm["type"]:
                            self.doc_type = str(fm["type"])
                        if "tags" in fm and fm["tags"]:
                            if isinstance(fm["tags"], list):
                                self.tags = [str(t).lstrip("#") for t in fm["tags"]]
                            else:
                                self.tags = [str(fm["tags"]).lstrip("#")]
                except Exception as exc:
                    logger.debug("Failed parsing frontmatter in %s: %s", self.rel_path, exc)
                self.body = parts[2].strip()

        # 2. Extract Headings (# Heading)
        self.heading_lowers: list[str] = []
        self.heading_tokens: list[set[str]] = []
        for line in self.body.splitlines():
            m = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if m:
                h_text = m.group(2).strip()
                self.headings.append(h_text)
                self.heading_lowers.append(h_text.lower())
                self.heading_tokens.append(set(_tokenize(h_text)))

        # 3. Extract Wikilinks [[target]]
        self.wikilinks = re.findall(r"\[\[(.*?)\]\]", self.raw_content)

        # 4. Extract inline hashtags #tag
        inline_tags = re.findall(r"(?<!\S)#([a-zA-Z0-9_\-]+)", self.body)
        for it in inline_tags:
            if it not in self.tags:
                self.tags.append(it)

        # Precompute title tokens and lowercased tags
        self.title_lower = self.title.lower()
        self.title_tokens = set(_tokenize(self.title))
        self.tag_lowers = [t.lower() for t in self.tags]
        self.body_lower = self.body.lower()

        # 5. Identify whether this is an Index / Glossary / Overview document
        t_low = self.title_lower
        p_low = self.rel_path.lower()
        self.is_index_doc = (
            self.doc_type.lower() == "index"
            or t_low.endswith("index")
            or t_low in (
                "glossary", "master index", "learning path", "roadmap",
                "knowledge base audit", "validation report", "topic directory", "concept map", "readme"
            )
            or "/00-index/" in p_low
            or "/00-indexes/" in p_low
            or "/00-web-development-index/" in p_low
            or "/99-audit/" in p_low
            or p_low.startswith("00-")
            or p_low.startswith("99-")
        )


class _LocalInvertedIndex:
    """Inverted index and BM25 ranker for fast, accurate local search."""

    def __init__(self, notes: list[_ParsedNote]) -> None:
        self.notes = notes
        self.doc_map: dict[str, _ParsedNote] = {n.rel_path: n for n in notes}
        self.title_map: dict[str, _ParsedNote] = {n.title.lower(): n for n in notes}
        self.index: dict[str, list[int]] = {}
        self.title_index: dict[str, list[int]] = {}
        self.tag_index: dict[str, list[int]] = {}
        self.heading_index: dict[str, list[int]] = {}
        self.doc_lengths: list[int] = []
        self.term_freqs: list[dict[str, int]] = []
        self.idfs: dict[str, float] = {}
        self.avg_doc_len: float = 0.0
        self._build()

    def _build(self) -> None:
        total_len = 0
        num_docs = len(self.notes)
        for i, n in enumerate(self.notes):
            b_tokens = _tokenize(n.body)
            self.doc_lengths.append(len(b_tokens))
            total_len += len(b_tokens)

            tf_map: dict[str, int] = {}
            for t in b_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1
            self.term_freqs.append(tf_map)

            for t in tf_map:
                self.index.setdefault(t, []).append(i)

            for t in n.title_tokens:
                self.title_index.setdefault(t, []).append(i)

            for tag in n.tags:
                for t in set(_tokenize(tag)):
                    self.tag_index.setdefault(t, []).append(i)

            for h in n.headings:
                for t in set(_tokenize(h)):
                    self.heading_index.setdefault(t, []).append(i)

        self.avg_doc_len = total_len / max(num_docs, 1)

        # Precompute IDFs
        for t, posting in self.index.items():
            docs_with_t = len(posting)
            self.idfs[t] = math.log(1 + (num_docs - docs_with_t + 0.5) / (docs_with_t + 0.5))

    def _score_single_intent(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[float, _ParsedNote]]:
        q_clean = query.strip()
        if not q_clean:
            return []

        q_tokens = _tokenize(q_clean)
        if not q_tokens:
            return []

        q_lower = q_clean.lower()
        k1 = 1.2
        b = 0.75

        # Retrieve candidate document IDs
        candidate_ids: set[int] = set()
        for t in q_tokens:
            candidate_ids.update(self.title_index.get(t, []))
            candidate_ids.update(self.tag_index.get(t, []))
            candidate_ids.update(self.heading_index.get(t, []))
            candidate_ids.update(self.index.get(t, []))

        scored: list[tuple[float, _ParsedNote]] = []
        for doc_id in candidate_ids:
            note = self.notes[doc_id]

            # ── Apply filters ──────────────────────────────────────────
            if filters:
                if "tags" in filters:
                    req_tags = set(t.lower().lstrip("#") for t in filters["tags"])
                    doc_tags = set(t.lower() for t in note.tags)
                    if not req_tags.issubset(doc_tags):
                        continue
                if "folder" in filters:
                    folder_filter = filters["folder"].replace("\\", "/").rstrip("/")
                    if not note.rel_path.startswith(folder_filter):
                        continue
                if "category" in filters:
                    if filters["category"].lower() not in note.category.lower():
                        continue
                if "type" in filters:
                    if filters["type"].lower() != note.doc_type.lower():
                        continue

            # Check query token coverage across the document
            doc_all_tokens = note.title_tokens | set(note.tag_lowers)
            tf_map = self.term_freqs[doc_id]
            matched_q_tokens = sum(1 for t in q_tokens if t in doc_all_tokens or tf_map.get(t, 0) > 0)
            token_coverage = matched_q_tokens / len(q_tokens)

            q_token_set = set(q_tokens)
            is_title_match = (q_lower == note.title_lower) or (q_lower in note.title_lower) or (note.title_tokens and note.title_tokens.issubset(q_token_set))
            has_phrase_match = (q_lower in note.title_lower) or (q_lower in note.body_lower)
            if len(q_tokens) >= 2 and not has_phrase_match and not is_title_match and token_coverage < 0.5:
                continue

            score = 0.0

            # 1. Title match boost
            if q_lower == note.title_lower:
                score += 50.0
            elif q_lower in note.title_lower:
                score += 30.0
            elif is_title_match:
                # Full title appears within query (e.g. "Frontend" in "responsive frontend interface")
                score += 35.0
            else:
                matched_title = sum(1 for t in q_tokens if t in note.title_tokens)
                if matched_title > 0:
                    score += (matched_title / len(q_tokens)) * 15.0

            # 2. Exact phrase in body
            if q_lower in note.body_lower:
                score += 10.0

            # 4. Heading matches
            for h_lower, h_tokens in zip(note.heading_lowers, note.heading_tokens):
                if q_lower == h_lower:
                    score += 12.0
                    break
                elif q_lower in h_lower:
                    score += 8.0
                    break
                elif all(t in h_tokens for t in q_tokens):
                    score += 6.0
                    break

            # 5. Tag matches
            for tag_lower in note.tag_lowers:
                if q_lower == tag_lower:
                    score += 8.0
                    break
                elif q_lower in tag_lower:
                    score += 5.0
                    break

            # 6. BM25 scoring on body tokens
            doc_len = self.doc_lengths[doc_id]
            for t in q_tokens:
                tf = tf_map.get(t, 0)
                if tf > 0:
                    idf = self.idfs.get(t, 1.0)
                    bm25_tf = (tf * (k1 + 1)) / (
                        tf + k1 * (1 - b + b * (doc_len / (self.avg_doc_len or 1)))
                    )
                    score += idf * bm25_tf * 0.5

            # Quality threshold to filter out weak irrelevant token hits
            if score >= 5.0:
                # Down-rank broad Index/Glossary/Audit documents
                if note.is_index_doc:
                    score *= 0.20
                norm_score = min(round(score / 50.0, 4), 1.0)
                scored.append((norm_score, note))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[float, _ParsedNote]]:
        # 1. Search with full query
        main_results = self._score_single_intent(query, filters)

        # 2. Decompose query into sub-intents
        sub_intents = _decompose_query(query)

        # If not a compound query, return main results directly
        if len(sub_intents) <= 1:
            return main_results

        # 3. Retrieve matches for each detected sub-intent
        sub_matches: list[list[tuple[float, _ParsedNote]]] = []
        for sub_q in sub_intents:
            sub_res = self._score_single_intent(sub_q, filters)
            if sub_res:
                sub_matches.append(sub_res)

        # 4. Interleave top non-index hits from each distinct sub-intent (round-robin)
        seen_paths: set[str] = set()
        merged: list[tuple[float, _ParsedNote]] = []

        max_depth = max((len(r) for r in sub_matches), default=0)
        for depth in range(min(max_depth, 3)):
            for sub_res in sub_matches:
                if depth < len(sub_res):
                    score, note = sub_res[depth]
                    if not note.is_index_doc and note.rel_path not in seen_paths:
                        merged.append((score, note))
                        seen_paths.add(note.rel_path)

        # Then add remaining specific main results
        for score, note in main_results:
            if not note.is_index_doc and note.rel_path not in seen_paths:
                merged.append((score, note))
                seen_paths.add(note.rel_path)

        # Finally append any index results if needed
        for score, note in main_results:
            if note.is_index_doc and note.rel_path not in seen_paths:
                merged.append((score, note))
                seen_paths.add(note.rel_path)

        return merged


# ─────────────────────────────────────────────────────────────────────────────
# Local Obsidian Adapter Implementation
# ─────────────────────────────────────────────────────────────────────────────


class LocalObsidianAdapter(ObsidianAdapter):
    """
    Production-ready Local Obsidian Vault Adapter.

    Recursively discovers markdown files (.md) from the local vault directory,
    parses YAML frontmatter, headings, tags, and wikilinks, and performs
    high-speed, metadata-boosted lexical retrieval.
    """

    def __init__(self, vault_path: str | Path | None = None) -> None:
        self.vault_path = self._resolve_vault_path(vault_path)
        self._notes: list[_ParsedNote] = []
        self._index: _LocalInvertedIndex = _LocalInvertedIndex([])
        self.reindex()

    def _resolve_vault_path(self, raw_path: str | Path | None) -> Path:
        """Resolve vault path, with robust fallback detection."""
        candidates = []
        if raw_path:
            candidates.append(Path(raw_path))

        # Common defaults relative to current working directory and module
        base_dir = Path(__file__).resolve().parent.parent.parent
        candidates.extend([
            base_dir / "obsedian",
            base_dir / "obsidian",
            Path.cwd() / "obsedian",
            Path.cwd() / "obsidian",
            base_dir.parent / "memory-agent" / "obsedian",
            base_dir.parent / "memory-agent" / "obsidian",
        ])

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate.resolve()

        if raw_path:
            p = Path(raw_path)
            p.mkdir(parents=True, exist_ok=True)
            return p.resolve()

        # Fallback to creating local obsidian dir
        default_p = base_dir / "obsidian"
        default_p.mkdir(parents=True, exist_ok=True)
        return default_p.resolve()

    def reindex(self) -> int:
        """Scan vault directory and rebuild the inverted search index."""
        parsed_notes: list[_ParsedNote] = []
        if not self.vault_path.exists():
            raise ObsidianAdapterError(f"Vault directory does not exist: {self.vault_path}")

        for root, dirs, files in os.walk(self.vault_path):
            # Exclude hidden directories and system artifacts
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__MACOSX"]
            for f in files:
                if not f.endswith(".md") or f.startswith("."):
                    continue
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, self.vault_path).replace("\\", "/")
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as file_handle:
                        content = file_handle.read()
                    parsed_notes.append(_ParsedNote(rel_path, abs_path, content))
                except Exception as exc:
                    logger.warning("Failed reading note %s: %s", rel_path, exc)

        self._notes = parsed_notes
        self._index = _LocalInvertedIndex(parsed_notes)
        logger.info(
            "LocalObsidianAdapter: indexed %d notes from %s",
            len(self._notes),
            self.vault_path,
        )
        return len(self._notes)

    def _to_memory_result(self, note: _ParsedNote, query: str, relevance: float) -> MemoryResult:
        return MemoryResult(
            id=str(uuid.uuid4()),
            query=query,
            content=note.raw_content,
            sources=[note.rel_path],
            evidence_refs=[],
            relevance=relevance,
            approval_status=ApprovalStatus.RETRIEVED,
            source_note=note.rel_path,
        )

    # ── ObsidianAdapter Interface ──────────────────────────────────────────

    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[MemoryResult]:
        try:
            results = self._index.search(query, filters)
            return [self._to_memory_result(note, query, score) for score, note in results]
        except Exception as exc:
            logger.error("LocalObsidianAdapter search failed: %s", exc)
            raise ObsidianAdapterError(f"Local Obsidian search error: {exc}") from exc

    async def read(self, note_id: str) -> MemoryResult | None:
        try:
            clean_id = note_id.replace("\\", "/").strip().lstrip("/")
            if clean_id in self._index.doc_map:
                note = self._index.doc_map[clean_id]
                return self._to_memory_result(note, "", 1.0)

            # Try with .md extension
            if not clean_id.endswith(".md") and f"{clean_id}.md" in self._index.doc_map:
                note = self._index.doc_map[f"{clean_id}.md"]
                return self._to_memory_result(note, "", 1.0)

            # Try matching by title
            clean_lower = clean_id.lower()
            if clean_lower in self._index.title_map:
                note = self._index.title_map[clean_lower]
                return self._to_memory_result(note, "", 1.0)

            # Try by filename
            for rel, note in self._index.doc_map.items():
                if Path(rel).name == clean_id or Path(rel).stem == clean_id:
                    return self._to_memory_result(note, "", 1.0)

            return None
        except Exception as exc:
            logger.error("LocalObsidianAdapter read failed for %s: %s", note_id, exc)
            raise ObsidianAdapterError(f"Local Obsidian read error: {exc}") from exc

    async def list_notes(self, folder: str | None = None) -> list[str]:
        try:
            if folder:
                clean_folder = folder.replace("\\", "/").rstrip("/") + "/"
                return [n.rel_path for n in self._notes if n.rel_path.startswith(clean_folder)]
            return [n.rel_path for n in self._notes]
        except Exception as exc:
            raise ObsidianAdapterError(f"Local Obsidian list error: {exc}") from exc

    async def write(
        self,
        content: str,
        target_note: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        try:
            clean_target = target_note.replace("\\", "/").strip().lstrip("/")
            if not clean_target.endswith(".md"):
                clean_target = f"{clean_target}.md"

            target_file = self.vault_path / clean_target
            if target_file.exists():
                raise ObsidianDuplicateError(
                    f"Note '{clean_target}' already exists. Use update() to modify."
                )

            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Format frontmatter if metadata provided
            file_content = content
            if metadata:
                fm_dict: dict[str, Any] = {
                    "title": metadata.get("title", Path(clean_target).stem),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "approval_status": "approved",
                }
                if "tags" in metadata and metadata["tags"]:
                    fm_dict["tags"] = metadata["tags"]
                if "sources" in metadata and metadata["sources"]:
                    fm_dict["sources"] = metadata["sources"]
                if "task_id" in metadata and metadata["task_id"]:
                    fm_dict["task_id"] = metadata["task_id"]

                fm_yaml = yaml.dump(fm_dict, sort_keys=False).strip()
                file_content = f"---\n{fm_yaml}\n---\n\n{content}"

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(file_content)

            # Update index
            self.reindex()
            return clean_target
        except ObsidianDuplicateError:
            raise
        except Exception as exc:
            logger.error("LocalObsidianAdapter write error: %s", exc)
            raise ObsidianAdapterError(f"Local Obsidian write failed: {exc}") from exc

    async def update(self, note_id: str, content: str) -> bool:
        try:
            clean_id = note_id.replace("\\", "/").strip().lstrip("/")
            if not clean_id.endswith(".md"):
                clean_id = f"{clean_id}.md"

            target_file = self.vault_path / clean_id
            if not target_file.exists():
                raise ObsidianNoteNotFoundError(f"Note '{clean_id}' not found.")

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)

            self.reindex()
            return True
        except ObsidianNoteNotFoundError:
            raise
        except Exception as exc:
            logger.error("LocalObsidianAdapter update error: %s", exc)
            raise ObsidianAdapterError(f"Local Obsidian update failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Mock Obsidian Adapter Implementation (for isolated unit tests)
# ─────────────────────────────────────────────────────────────────────────────

_SEED_NOTES: dict[str, dict[str, Any]] = {
    "company/architecture-overview": {
        "title": "Company Architecture Overview",
        "content": (
            "# Autonomous AI Workforce — Architecture Overview\n\n"
            "## Control Loop\n"
            "USER INPUT → PERCEPTION → MODE SELECTOR → MASTER ORCHESTRATOR → "
            "MEMORY + PLANNER → CAPABILITY MANAGER → GUARDRAIL → TWIN / SPECIALIST → "
            "EXECUTION → OBSERVATION → VERIFICATION.\n\n"
            "## Operating Modes\n"
            "- **Basic Mode**: Fast direct assistance. "
            "Input → Perception → Capability → Security → Execution → Verification → Output.\n"
            "- **Advanced Project Mode**: Complex multi-step projects. "
            "Input → Project Initialization → Orchestrator → Memory → Planner → "
            "Capability Manager → Security → Workforce → Execution → Verification → "
            "Reflection/Re-plan → Walkthrough → Memory.\n\n"
            "## Memory Architecture\n"
            "Memory Agent → Internal Obsidian + Controlled External Research → "
            "Evidence Validation → Approved Knowledge → Obsidian.\n"
            "External research must not become trusted company memory merely because "
            "a model retrieved it."
        ),
        "folder": "company",
        "tags": ["architecture", "overview", "ai-workforce"],
        "created_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
    },
    "company/product-guidelines": {
        "title": "Product Guidelines",
        "content": (
            "# Product Guidelines\n\n"
            "## Core Principles\n"
            "1. Local-first: All sensitive operations run on company-owned hardware.\n"
            "2. Evidence-based: Every autonomous action produces verifiable evidence.\n"
            "3. Bounded recovery: Maximum 3 recovery attempts before escalation.\n"
            "4. Memory safety: External research is validated before becoming "
            "approved Obsidian knowledge.\n\n"
            "## User Experience\n"
            "- Basic Mode for bounded, single-capability tasks.\n"
            "- Advanced Project Mode for complex multi-agent projects.\n"
            "- Voice and text input supported.\n"
            "- Final walkthrough presented with files, artifacts and verification.\n\n"
            "## Quality Gates\n"
            "- Independent verification: the model generating a fix cannot be the "
            "sole authority declaring success.\n"
            "- Re-plan Gate: evidence support + scope + expected impact + "
            "verification criteria must all pass."
        ),
        "folder": "company",
        "tags": ["product", "guidelines", "principles"],
        "created_at": datetime(2026, 8, 5, tzinfo=timezone.utc),
    },
    "engineering/standards": {
        "title": "Engineering Standards",
        "content": (
            "# Engineering Standards\n\n"
            "## Code Quality\n"
            "- All Python code must use type hints and pass mypy strict mode.\n"
            "- API contracts must not be broken once locked. "
            "Implementation may differ; interfaces cannot.\n"
            "- Every request must carry a taskId/correlationId.\n"
            "- Every execution returns a structured result + evidence.\n\n"
            "## API Design\n"
            "- Backend: FastAPI + Pydantic.\n"
            "- Real-time: WebSocket for task/workforce updates.\n"
            "- Execution isolation: Docker.\n"
            "- Frontend: existing Next.js application.\n\n"
            "## Testing\n"
            "- Unit tests, integration tests, and E2E tests are required.\n"
            "- Tests must pass before any merge to main.\n"
            "- Typecheck, production build and core integration tests must pass "
            "at Day-7 Definition of Done."
        ),
        "folder": "engineering",
        "tags": ["engineering", "standards", "code-quality"],
        "created_at": datetime(2026, 8, 10, tzinfo=timezone.utc),
    },
    "security/guidelines": {
        "title": "Security Guidelines",
        "content": (
            "# Security Guidelines\n\n"
            "## API Keys and Secrets\n"
            "- API keys must NEVER be placed in source code.\n"
            "- Use environment variables or a secrets manager.\n"
            "- Never commit .env files with real credentials.\n\n"
            "## Execution Security\n"
            "- The Tool Executor must not trust arbitrary model-generated commands.\n"
            "- Approved action context comes from the control/security layer.\n"
            "- Workspace, command and permission restrictions are enforced by the executor.\n\n"
            "## Memory Security\n"
            "- External research is validated before becoming approved Obsidian knowledge.\n"
            "- A language model saying 'this is correct' is NOT sufficient evidence.\n"
            "- All memory writes produce an audit record.\n"
            "- Sensitive/high-risk actions remain guarded even in autonomous mode."
        ),
        "folder": "security",
        "tags": ["security", "guidelines", "secrets"],
        "created_at": datetime(2026, 8, 12, tzinfo=timezone.utc),
    },
}


class MockObsidianAdapter(ObsidianAdapter):
    """
    In-memory Obsidian adapter for development and isolated unit testing.

    Seeded with realistic company knowledge notes.
    Supports search, read, list, write, and update operations against
    an in-memory store.
    """

    def __init__(self, simulate_failure: bool = False) -> None:
        self._store: dict[str, dict[str, Any]] = {
            k: dict(v) for k, v in _SEED_NOTES.items()
        }
        self._simulate_failure = simulate_failure

    def _raise_if_failing(self) -> None:
        if self._simulate_failure:
            raise ObsidianAdapterError("MockObsidianAdapter: simulated failure")

    def _to_memory_result(
        self, note_id: str, note: dict[str, Any], query: str = ""
    ) -> MemoryResult:
        relevance = _simple_relevance(query, note["content"], note["title"]) if query else 0.5
        return MemoryResult(
            query=query,
            content=note["content"],
            sources=[note_id],
            evidence_refs=[],
            relevance=relevance,
            approval_status=ApprovalStatus.RETRIEVED,
            source_note=note_id,
        )

    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[MemoryResult]:
        self._raise_if_failing()

        results: list[MemoryResult] = []
        for note_id, note in self._store.items():
            relevance = _simple_relevance(query, note["content"], note["title"])
            if relevance > 0.0:
                result = self._to_memory_result(note_id, note, query)
                result.relevance = relevance
                results.append(result)

        if filters and "tags" in filters:
            required_tags: set[str] = set(filters["tags"])
            results = [
                r
                for r in results
                if required_tags.issubset(set(self._store[r.source_note or ""].get("tags", [])))
                if r.source_note and r.source_note in self._store
            ]

        results.sort(key=lambda r: r.relevance, reverse=True)
        return results

    async def read(self, note_id: str) -> MemoryResult | None:
        self._raise_if_failing()
        note = self._store.get(note_id)
        if note is None:
            return None
        return self._to_memory_result(note_id, note)

    async def list_notes(self, folder: str | None = None) -> list[str]:
        self._raise_if_failing()
        if folder:
            return [nid for nid in self._store if nid.startswith(folder + "/")]
        return list(self._store.keys())

    async def write(
        self,
        content: str,
        target_note: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self._raise_if_failing()
        if target_note in self._store:
            raise ObsidianDuplicateError(
                f"Note '{target_note}' already exists. Use update() to modify it."
            )
        self._store[target_note] = {
            "title": (metadata or {}).get("title", target_note),
            "content": content,
            "folder": target_note.split("/")[0] if "/" in target_note else "root",
            "tags": (metadata or {}).get("tags", []),
            "created_at": datetime.now(timezone.utc),
            "metadata": metadata or {},
        }
        return target_note

    async def update(self, note_id: str, content: str) -> bool:
        self._raise_if_failing()
        if note_id not in self._store:
            raise ObsidianNoteNotFoundError(f"Note '{note_id}' not found.")
        self._store[note_id]["content"] = content
        self._store[note_id]["updated_at"] = datetime.now(timezone.utc)
        return True

    def inject_note(self, note_id: str, note: dict[str, Any]) -> None:
        self._store[note_id] = note

    def store_size(self) -> int:
        return len(self._store)
