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

## Structure

```
data/       extracted CSVs
src/        extraction, graph building, analysis
notebooks/  exploration and figures
```

## Setup

```
pip install -r requirements.txt
cp .env.example .env   # optional: paste your Stack Exchange API key
python src/fetch.py --tag python --max-questions 3000
```

Raw JSON is written to `data/raw/` (git-ignored). Without a key the API allows 300 requests/day; with a key, 10,000.
