"""Phase 5 ablation: hybrid+rerank with no filter, oracle filters and the
rule-based detector. Writes evaluation/results/ablation.json and the README
section between <!-- ABLATION:START --> and <!-- ABLATION:END -->."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import get_settings  # noqa: E402
from core.logging import setup_logging  # noqa: E402
from evaluation.ablation import render_markdown, run_ablation, write  # noqa: E402

START, END = "<!-- ABLATION:START -->", "<!-- ABLATION:END -->"


def main():
    setup_logging()
    settings = get_settings()
    result = run_ablation(settings)
    write(result, settings.resolve(settings.evaluation.ablation_out))
    table = render_markdown(result)
    readme = settings.resolve(settings.evaluation.readme_path)
    content = readme.read_text(encoding="utf-8")
    if START in content and END in content:
        pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.DOTALL)
        readme.write_text(pattern.sub(lambda _: f"{START}\n{table}\n{END}", content), encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
