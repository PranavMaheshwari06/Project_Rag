"""Structure-aware chunker. Splits on headings first, then packs blocks into
chunks of roughly target_tokens (soft cap max_tokens plus carried overlap)
with a small word-level overlap between adjacent chunks. Fenced code blocks
are atomic: a chunk boundary never lands inside one, and overlap never takes
part of one."""

import re
from dataclasses import dataclass

from core.config import ChunkingCfg
from ingestion.parser import ParsedDoc
from schemas.common import Chunk

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)")


def count_tokens(text: str) -> int:
    # whitespace tokens are a fine budget proxy; we don't need exact BPE counts
    return len(text.split())


@dataclass
class Block:
    text: str
    is_code: bool = False

    @property
    def tokens(self) -> int:
        return count_tokens(self.text)


def _parse_blocks(text: str, title: str) -> list[tuple[Block, str, bool]]:
    """Returns (block, section_path, starts_major_section) in document order.
    path[level-1] holds the active heading at that level; the doc title fills
    the h1 slot until a real h1 shows up."""
    lines = text.splitlines()
    items: list[tuple[Block, str, bool]] = []
    path: list[str] = [title]
    para: list[str] = []
    i = 0

    def flush_para():
        nonlocal para
        if para:
            items.append((Block("\n".join(para)), " > ".join(path), False))
            para = []

    while i < len(lines):
        line = lines[i]
        fence = FENCE_RE.match(line)
        if fence:
            flush_para()
            marker = fence.group(1)
            code = [line]
            i += 1
            while i < len(lines):
                code.append(lines[i])
                if FENCE_RE.match(lines[i]) and FENCE_RE.match(lines[i]).group(1) == marker:
                    break
                i += 1
            items.append((Block("\n".join(code), is_code=True), " > ".join(path), False))
            i += 1
            continue
        heading = HEADING_RE.match(line)
        if heading:
            flush_para()
            level = len(heading.group(1))
            text_part = heading.group(2).strip()
            path = path[: level - 1] + [text_part] if level > 1 else [text_part]
            items.append((Block(line.strip()), " > ".join(path), level <= 2))
            i += 1
            continue
        if line.strip():
            para.append(line.rstrip())
        else:
            flush_para()
        i += 1
    flush_para()
    return items


def _overlap_blocks(blocks: list[Block], budget: int) -> list[Block]:
    """Trailing blocks (or a word-level tail of the last paragraph) worth up to
    `budget` tokens. Code blocks are only carried whole."""
    if budget <= 0:
        return []
    picked: list[Block] = []
    used = 0
    for block in reversed(blocks):
        if used + block.tokens <= budget:
            picked.insert(0, block)
            used += block.tokens
            continue
        if not block.is_code:
            remaining = budget - used
            if remaining > 0:
                tail = " ".join(block.text.split()[-remaining:])
                picked.insert(0, Block(tail))
        break
    return picked


def _split_oversized(items: list[tuple[Block, str, bool]], cfg: ChunkingCfg) -> list[tuple[Block, str, bool]]:
    """Prose blocks bigger than max_tokens get sliced at word boundaries.
    Code blocks stay whole no matter their size."""
    out = []
    for block, path, starts in items:
        if block.is_code or block.tokens <= cfg.max_tokens:
            out.append((block, path, starts))
            continue
        words = block.text.split()
        for i in range(0, len(words), cfg.target_tokens):
            out.append((Block(" ".join(words[i:i + cfg.target_tokens])), path, starts and i == 0))
    return out


def chunk_document(parsed: ParsedDoc, cfg: ChunkingCfg) -> list[Chunk]:
    items = _split_oversized(_parse_blocks(parsed.text, parsed.title), cfg)
    overlap_budget = int(cfg.target_tokens * cfg.overlap_ratio)

    pieces: list[tuple[str, str]] = []  # (text, section_path)
    cur: list[Block] = []
    cur_path = parsed.title
    cur_tokens = 0
    has_new = False  # cur holds something beyond carried overlap

    def flush(carry_overlap: bool = False):
        nonlocal cur, cur_tokens, has_new
        if not cur or not has_new:
            return
        pieces.append(("\n\n".join(b.text for b in cur), cur_path))
        cur = _overlap_blocks(cur, overlap_budget) if carry_overlap else []
        cur_tokens = sum(b.tokens for b in cur)
        has_new = False

    for block, path, starts_section in items:
        if starts_section and cur_tokens >= cfg.min_section_tokens:
            flush()
        if cur and cur_tokens + block.tokens > cfg.max_tokens:
            flush(carry_overlap=True)
        # a chunk that so far only holds headings belongs to the incoming section
        if not cur or all(b.text.lstrip().startswith("#") for b in cur):
            cur_path = path
        cur.append(block)
        cur_tokens += block.tokens
        has_new = True
    flush()

    return [
        Chunk(
            chunk_id=f"{parsed.doc_id}::{idx:03d}",
            doc_id=parsed.doc_id,
            source=parsed.source,
            title=parsed.title,
            section_path=path,
            url=parsed.url,
            text=text,
            token_count=count_tokens(text),
        )
        for idx, (text, path) in enumerate(pieces)
    ]
