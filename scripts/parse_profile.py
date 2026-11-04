"""Pasted text -> unconfirmed draft profile JSON (the same function as POST
/profile/parse). Needs GEMINI_API_KEY; use synthetic text only, because the
free-tier provider may keep prompts. Review and edit the draft before checking it.

Usage: parse_profile.py --input text.txt [--out draft.json]"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from eligibility.parse import ParseError, parse_profile  # noqa: E402
from generation.llm_client import LLMClient  # noqa: E402


def main(argv: list[str] | None = None, llm=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    settings = get_settings()
    text = Path(args.input).read_text(encoding="utf-8")
    if len(text) > settings.eligibility.parse_max_chars:
        print(f"the text is longer than {settings.eligibility.parse_max_chars} characters")
        return 1
    llm = llm or LLMClient(settings)
    if not llm.available:
        print("no LLM key configured (GEMINI_API_KEY); write the profile JSON by hand instead")
        return 1
    try:
        parsed = parse_profile(text, llm)
    except ParseError as e:
        print(e)
        return 1
    out = parsed.model_dump_json(indent=2)
    if args.out:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
        print(f"unconfirmed draft -> {args.out}; dropped without a supporting span: {parsed.dropped or 'none'}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
