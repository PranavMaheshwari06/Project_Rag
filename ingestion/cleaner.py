"""Text-level boilerplate scrubbing. Structural nav/footer noise is already
dropped in the HTML parser; this pass handles what survives in the text, while
leaving fenced code blocks byte-for-byte intact."""

import re

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
BADGE_LINE_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def clean(text: str) -> str:
    text = COMMENT_RE.sub("", text)

    out: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        fence = FENCE_RE.match(line)
        if fence:
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
        out.append(line.rstrip())

    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() + "\n"
