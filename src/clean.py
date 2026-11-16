"""Flatten and clean the raw API JSON into CSVs (week 9).

Reads data/raw/<stem>_questions.json and <stem>_answers.json written by
fetch.py and writes:

    data/questions.csv   one row per question
    data/answers.csv     one row per answer

Cleaning:
  * HTML is stripped from bodies. Code blocks are removed from `body_text`
    (they hold no Bloom's verbs) but counted in `n_code_blocks`.
  * HTML entities in titles and display names are unescaped.
  * Posts by missing users (deleted accounts, no user_id) are dropped.
  * Questions left with no answers after that are dropped, and answers to
    dropped questions go with them.

Usage:
    python src/clean.py --tag python --from-date 2025-01-01 --to-date 2026-01-01
"""
import argparse
import html
import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parent.parent


def strip_html(body):
    """Return (prose text without code blocks, number of code blocks)."""
    soup = BeautifulSoup(body or "", "html.parser")
    blocks = soup.find_all("pre")
    for pre in blocks:
        pre.decompose()
    text = soup.get_text(" ")
    return re.sub(r"\s+", " ", text).strip(), len(blocks)


def owner_fields(owner):
    return {
        "user_id": owner.get("user_id"),
        "display_name": html.unescape(owner.get("display_name", "")),
        "reputation": owner.get("reputation"),
    }


def flatten_questions(raw):
    rows = []
    for q in raw:
        text, n_code = strip_html(q.get("body"))
        o = owner_fields(q["owner"])
        rows.append({
            "question_id": q["question_id"],
            "asker_id": o["user_id"],
            "asker_name": o["display_name"],
            "asker_reputation": o["reputation"],
            "title": html.unescape(q["title"]),
            "body_text": text,
            "n_code_blocks": n_code,
            "tags": ";".join(q["tags"]),
            "score": q["score"],
            "view_count": q["view_count"],
            "answer_count": q["answer_count"],
            "accepted_answer_id": q.get("accepted_answer_id"),
            "creation_date": pd.to_datetime(q["creation_date"], unit="s", utc=True),
            "link": q["link"],
        })
    return pd.DataFrame(rows)


def flatten_answers(raw):
    rows = []
    for a in raw:
        text, n_code = strip_html(a.get("body"))
        o = owner_fields(a["owner"])
        rows.append({
            "answer_id": a["answer_id"],
            "question_id": a["question_id"],
            "answerer_id": o["user_id"],
            "answerer_name": o["display_name"],
            "answerer_reputation": o["reputation"],
            "body_text": text,
            "n_code_blocks": n_code,
            "is_accepted": a["is_accepted"],
            "score": a["score"],
            "creation_date": pd.to_datetime(a["creation_date"], unit="s", utc=True),
        })
    return pd.DataFrame(rows)


def clean(questions, answers):
    n_q, n_a = len(questions), len(answers)
    questions = questions.drop_duplicates("question_id")
    answers = answers.drop_duplicates("answer_id")

    questions = questions.dropna(subset=["asker_id"])
    answers = answers.dropna(subset=["answerer_id"])
    answers = answers[answers["question_id"].isin(questions["question_id"])]
    questions = questions[questions["question_id"].isin(answers["question_id"])]

    questions = questions.astype({"asker_id": "int64"})
    answers = answers.astype({"answerer_id": "int64"})
    questions["accepted_answer_id"] = questions["accepted_answer_id"].astype("Int64")

    print(f"questions: {n_q} -> {len(questions)}  (dropped {n_q - len(questions)})")
    print(f"answers:   {n_a} -> {len(answers)}  (dropped {n_a - len(answers)})")
    return questions.reset_index(drop=True), answers.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tag", default="python")
    parser.add_argument("--from-date", default="2025-01-01")
    parser.add_argument("--to-date", default="2026-01-01")
    parser.add_argument("--raw-dir", type=Path, default=REPO_ROOT / "data" / "raw")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data")
    args = parser.parse_args()

    stem = f"{args.tag}_{args.from_date}_{args.to_date}"
    raw_q = json.loads((args.raw_dir / f"{stem}_questions.json").read_text(encoding="utf-8"))
    raw_a = json.loads((args.raw_dir / f"{stem}_answers.json").read_text(encoding="utf-8"))

    questions, answers = clean(flatten_questions(raw_q), flatten_answers(raw_a))
    questions.to_csv(args.out_dir / "questions.csv", index=False)
    answers.to_csv(args.out_dir / "answers.csv", index=False)
    print(f"wrote {args.out_dir / 'questions.csv'} and {args.out_dir / 'answers.csv'}")


if __name__ == "__main__":
    main()
