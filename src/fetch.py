"""Fetch questions and their answers for one tag from the Stack Exchange API.

Raw API responses are saved as JSON under data/raw/ (week 8). Flattening to CSV
and cleaning happen in week 9.

Usage:
    python src/fetch.py --tag python --max-questions 3000
"""
import argparse
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

API = "https://api.stackexchange.com/2.3"
SITE = "stackoverflow"
PAGE_SIZE = 100
ID_BATCH = 100  # the API accepts up to 100 semicolon-separated ids per call


def get(session, path, params):
    """GET one API page, honoring the `backoff` field the API may return."""
    resp = session.get(f"{API}/{path}", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "backoff" in data:
        time.sleep(data["backoff"])
    if data.get("quota_remaining", 1) <= 0:
        raise RuntimeError("Stack Exchange quota exhausted; add a key or retry tomorrow")
    return data


def fetch_questions(session, tag, max_questions, key):
    """Most-voted questions for `tag` that have an accepted answer."""
    questions, page = [], 1
    while len(questions) < max_questions:
        params = {
            "site": SITE, "tagged": tag, "sort": "votes", "order": "desc",
            "filter": "withbody", "pagesize": PAGE_SIZE, "page": page,
        }
        if key:
            params["key"] = key
        data = get(session, "questions", params)
        questions += [q for q in data["items"] if q.get("accepted_answer_id")]
        print(f"questions page {page}: {len(questions)} kept, quota {data['quota_remaining']}")
        if not data["has_more"]:
            break
        page += 1
    return questions[:max_questions]


def fetch_answers(session, question_ids, key):
    """All answers for the given question ids, batched by ID_BATCH."""
    answers = []
    for i in range(0, len(question_ids), ID_BATCH):
        ids = ";".join(map(str, question_ids[i:i + ID_BATCH]))
        page = 1
        while True:
            params = {
                "site": SITE, "filter": "withbody", "pagesize": PAGE_SIZE, "page": page,
            }
            if key:
                params["key"] = key
            data = get(session, f"questions/{ids}/answers", params)
            answers += data["items"]
            if not data["has_more"]:
                break
            page += 1
        print(f"answers: {len(answers)} fetched, quota {data['quota_remaining']}")
    return answers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="python")
    parser.add_argument("--max-questions", type=int, default=3000)
    parser.add_argument("--out-dir", default="data/raw")
    args = parser.parse_args()

    load_dotenv()
    key = os.getenv("STACKEXCHANGE_KEY") or None
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        questions = fetch_questions(session, args.tag, args.max_questions, key)
        answers = fetch_answers(session, [q["question_id"] for q in questions], key)

    (out / f"{args.tag}_questions.json").write_text(json.dumps(questions), encoding="utf-8")
    (out / f"{args.tag}_answers.json").write_text(json.dumps(answers), encoding="utf-8")
    print(f"saved {len(questions)} questions and {len(answers)} answers to {out}")


if __name__ == "__main__":
    main()
