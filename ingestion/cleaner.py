"""Text-level boilerplate scrubbing. Structural nav/footer noise is already
dropped in the HTML parser; this pass handles what survives in the text, while
leaving fenced code blocks byte-for-byte intact (comments and blank lines
inside a fence are content, not noise)."""

import re

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
BADGE_LINE_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def clean(text: str) -> str:
    # soft hyphens split German compounds for BM25 ("Sperr\u00adkonto"); nbsp is just a space
    text = text.replace("\u00ad", "").replace("\u00a0", " ")

    out: list[str] = []
    prose: list[str] = []  # pending non-code lines, scrubbed together so comments can span lines

    def flush_prose():
        if prose:
            for line in COMMENT_RE.sub("", "\n".join(prose)).split("\n"):
                line = line.rstrip()
                if line or (out and out[-1]):  # at most one blank line in a row
                    out.append(line)
            prose.clear()

    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            flush_prose()
            if not in_fence:
                in_fence, fence_marker = True, fence.group(1)
            elif fence.group(1) == fence_marker:
                in_fence = False
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if BADGE_LINE_RE.match(line):
            continue
        prose.append(line)
    flush_prose()

    return "\n".join(out).strip() + "\n"
