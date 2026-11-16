# StackOverflow Knowledge Network

Build and analyze a knowledge network from StackOverflow, treating it as a massive, open-source classroom. The project combines social network analysis with text analysis to understand how users interact.

## Plan (1-person option)

1. **Extract data** with the official Stack Exchange API for a tag relevant to university students (e.g. `python`, `java`, `data-structures`) and save it to CSV.
2. **Build a directed graph**: users are nodes; an edge points from the answerer to the asker.
   - Node size reflects questioning plus answering activity.
   - Edge thickness reflects the number of questions answered between a pair of users.
   - Filter by frequency to show ~20 nodes for a clear visualization.
3. **Centrality report** for those nodes: in-degree, out-degree, hub value, and authority value, with an explanation of what they say about the network.
4. **Bloom's taxonomy**: categorize each question into a Bloom's level using the verbs table. Draw one edge per level between a pair of users (or one graph per level if cluttered), with thickness showing frequency.

## Progress

| Week | Task | Status |
|---|---|---|
| 8 | Setup, API access, fetch script | done (`src/fetch.py`) |
| 9 | Pull Q&A, save to CSV, clean | done (`src/clean.py`, `data/questions.csv`, `data/answers.csv`) |
| 10 | Directed user graph, ~20-node filter, drawing | done (`src/graph.py`, `figures/user_graph.png`) |
| 11 | In/out-degree, hub and authority, interpretation | done (`src/centrality.py`, [docs/week11_centrality.md](docs/week11_centrality.md)) |
| 12 | Bloom's classification and per-level graphs | to do |
| 13 | Final write-up and presentation | to do |

## Structure

```
data/       cleaned CSVs (raw API JSON in data/raw/, git-ignored)
src/        fetch.py -> clean.py -> graph.py -> centrality.py
figures/    generated plots
docs/       weekly write-ups
```

## Setup

```
pip install -r requirements.txt
cp .env.example .env   # optional: paste your Stack Exchange API key
python src/fetch.py --tag python --from-date 2025-01-01 --to-date 2026-01-01
python src/clean.py              # raw JSON -> data/questions.csv, data/answers.csv
python src/graph.py              # data/edges.csv, data/top_nodes.csv, figures/user_graph.png
python src/centrality.py         # data/centrality.csv, figures/hits.png
```

`fetch.py` gets the newest questions in the date window that have an accepted answer (up to `--max-questions`, default 3000), then their answers. Raw JSON is written to `data/raw/` (git-ignored). Answers are saved after every batch of 100 questions; if the daily quota runs out, re-run the same command to resume. Without a key the API allows 300 requests/day and refuses pages past 25, so a keyless run stops at 2,500 questions; with a key the limit is 10,000 requests/day.

The current data set is 2,465 questions and 3,452 answers after cleaning (2025, `[python]`).
