"""Fetch questions and their answers for one tag from the Stack Exchange API.

Pulls recent questions (newest first, within a date window) that have an
accepted answer, then all answers to those questions. Recent questions give
more repeat asker/answerer pairs than all-time top-voted ones, which suits the
user graph.

Raw API responses are saved as JSON under data/raw/ (week 8). Answers are saved
after every batch, so a run stopped by the daily quota resumes where it left
off when re-run with the same arguments. Flattening to CSV and cleaning happen
in week 9.

Usage:
    python src/fetch.py --tag python --from-date 2025-01-01 --to-date 2026-01-01
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

API = "https://api.stackexchange.com/2.3"
SITE = "stackoverflow"
PAGE_SIZE = 100
ID_BATCH = 100  # the API accepts up to 100 semicolon-separated ids per call
RETRIES = 3
REPO_ROOT = Path(__file__).resolve().parent.parent


class QuotaExhausted(RuntimeError):
    pass


def get(session, path, params, key):
    """GET one API page, retrying transient failures and honoring `backoff`."""
    if key:
        params = {**params, "key": key}
    for attempt in range(1, RETRIES + 1):
        try:
            resp = session.get(f"{API}/{path}", params=params, timeout=30)
        except requests.ConnectionError:
            if attempt == RETRIES:
                raise
            time.sleep(5 * attempt)
            continue
        if resp.ok:
            break
        # Errors come back as JSON with error_id / error_name / error_message.
        try:
            err = resp.json()
            detail = f"{err.get('error_name')}: {err.get('error_message')}"
        except ValueError:
            detail = resp.text[:200]
        if resp.status_code >= 503 and attempt < RETRIES:
            time.sleep(5 * attempt)
            continue
        raise RuntimeError(f"Stack Exchange API error {resp.status_code} on {path}: {detail}")

    data = resp.json()
    if "backoff" in data:
        time.sleep(data["backoff"])
    return data


def check_quota(data):
    if data.get("quota_remaining", 1) <= 0:
        raise QuotaExhausted("daily quota used up; re-run tomorrow (or with a key) to resume")


def to_epoch(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def fetch_questions(session, tag, from_date, to_date, max_questions, key):
    """Newest questions for `tag` in the window that have an accepted answer."""
    questions, page = [], 1
    while len(questions) < max_questions:
        data = get(session, "search/advanced", {
            "site": SITE, "tagged": tag, "accepted": "True",
            "fromdate": to_epoch(from_date), "todate": to_epoch(to_date),
            "sort": "creation", "order": "desc", "filter": "withbody",
            "pagesize": PAGE_SIZE, "page": page,
        }, key)
        questions += data["items"]
        print(f"questions page {page}: {len(questions)} total, quota {data['quota_remaining']}")
        if not data["has_more"]:
            break
        check_quota(data)
        page += 1
    return questions[:max_questions]


def fetch_answers(session, question_ids, answers, answers_path, key):
    """Append answers for question ids not already in `answers`, saving per batch."""
    done = {a["question_id"] for a in answers}
    todo = [qid for qid in question_ids if qid not in done]
    print(f"answers: {len(done)} questions already fetched, {len(todo)} to go")
    for i in range(0, len(todo), ID_BATCH):
        ids = ";".join(map(str, todo[i:i + ID_BATCH]))
        batch, page = [], 1
        while True:
            data = get(session, f"questions/{ids}/answers", {
                "site": SITE, "filter": "withbody", "pagesize": PAGE_SIZE, "page": page,
            }, key)
            batch += data["items"]
            if not data["has_more"]:
                break
            check_quota(data)
            page += 1
        # Only save complete batches, so a question is either fully fetched or not at all.
        answers += batch
        save(answers_path, answers)
        print(f"answers: {len(answers)} saved, quota {data['quota_remaining']}")
        check_quota(data)
    return answers


def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save(path, items):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(items), encoding="utf-8")
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tag", default="python")
    parser.add_argument("--from-date", default="2025-01-01", help="YYYY-MM-DD, inclusive")
    parser.add_argument("--to-date", default="2026-01-01", help="YYYY-MM-DD, exclusive")
    parser.add_argument("--max-questions", type=int, default=3000)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "raw")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    key = os.getenv("STACKEXCHANGE_KEY") or None
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.tag}_{args.from_date}_{args.to_date}"
    questions_path = args.out_dir / f"{stem}_questions.json"
    answers_path = args.out_dir / f"{stem}_answers.json"

    with requests.Session() as session:
        try:
            questions = load(questions_path)
            if questions is None:
                questions = fetch_questions(session, args.tag, args.from_date, args.to_date,
                                            args.max_questions, key)
                save(questions_path, questions)
            else:
                print(f"reusing {len(questions)} questions from {questions_path}")
            answers = fetch_answers(session, [q["question_id"] for q in questions],
                                    load(answers_path) or [], answers_path, key)
        except QuotaExhausted as e:
            raise SystemExit(f"stopped: {e}")

    print(f"done: {len(questions)} questions and {len(answers)} answers in {args.out_dir}")


if __name__ == "__main__":
    main()
