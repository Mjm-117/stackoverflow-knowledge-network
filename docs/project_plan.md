# Project plan

**Option 4: StackOverflow Knowledge, working solo** (I am responsible for every task).

## Spec (as given)

> Build and analyze a knowledge network from StackOverflow. Treat StackOverflow as a massive, open-source classroom and consider how users on the platform interact with each other by combining social network analysis concepts and text analysis to better understand the context.
>
> 1-person option: Extract data from StackOverflow using the official Stack Exchange API. Focus on a specific tag relevant to university students (e.g., #python, #java, or #datastructures) and extract the data into a CSV. Using the data you have, build a directed graph with users as nodes and directed edges from a user who answers another user who asked a question. The size of the node should reflect the amount of questioning and answering activity the user is involved in (more activity means bigger node) and the thickness of the edges should reflect the number of questions answered between a pair of users. If your graph has a lot of nodes, filter it by frequency so it only shows ~20 nodes so the visualization is clear. Calculate and report on these nodes' in-degree centrality, out-degree centrality, hub value, and authority value (explain what they say about your network). From the same dataset, analyze each question and categorize it at a Bloom's taxonomy level (use the verbs in the verbs table). The Bloom's level will then be incorporated into the edges of the graph, and you will want a separate edge for each level of the Bloom's taxonomy. For example, user A answers 10 questions from user B. In the original graph, there is 1 edge between A and B that is 10 "units" thick. Let's say 3 of these questions are Remembering, 2 are Analyzing, and 5 are Evaluating. Then in the Bloom's version of the graph, there are 3 edges between A and B corresponding to the 3 types of questions with appropriate thicknesses representing the frequency of each question type. If it gets too cluttered, you may choose to draw them as separate graphs so you have an original, full picture graph, then a separate graph for each of the Bloom's levels.

## Key decisions

- **Tag:** `[python]`. Questions created in 2025 that have an accepted answer, newest first.
- **Edge direction:** **answerer → asker**, as the spec says ("from a user who answers another user who asked a question").
- **Node size:** questions asked + answers given.
- **Edge width:** number of the asker's questions that the answerer answered.
- **~20-node filter:** grow a connected subgraph from the busiest user, always adding the neighbour with the most links into the group. A plain top-20-by-activity filter leaves almost no edges, because the most active answerers rarely answer each other.
- **Bloom's edges:** one edge per (answerer, asker, Bloom's level), with width equal to the number of questions at that level. If the combined drawing is cluttered, draw the original full graph plus one graph per level.

## Weekly plan

Calendar: Week 8 ends Fri Oct 30. Week 10 is midterm break. The presentation video is due in Week 13, and all deliverables are due in Week 14.

| Week | Tasks | Output | Status |
|---|---|---|---|
| 8 | Set up the repo and environment. Get Stack Exchange API access. Pick the `[python]` tag. Write a resumable fetch script. | `src/fetch.py` | Done |
| 9 | Pull the questions and their answers. Flatten them to CSV. Clean the data: strip HTML and code blocks, drop deleted users and questions without answers. | `src/clean.py`, `data/questions.csv`, `data/answers.csv` | Done |
| 10 *(midterm break)* | Build the directed user graph (answerer → asker, weighted). Filter it to ~20 nodes. Draw it with node size for activity and edge width for the number of questions answered. | `src/graph.py`, `data/edges.csv`, `figures/user_graph.png` | Done |
| 11 | Compute in-degree, out-degree, hub and authority (weighted HITS) for the 20 nodes. Compare with full-graph ranks. Write the interpretation. | `src/centrality.py`, `data/centrality.csv`, `figures/hits.png`, `docs/week11_centrality.md` | Done |
| 12 | Classify every question into a Bloom's level by matching the verbs table against its title and body (rules for ties and for questions with no verb match). Spot-check a sample by hand. Build the Bloom's graph with one edge per (pair, level) and width = frequency. Draw it combined, or as the original graph plus one graph per level if cluttered. Summarise which levels the top answerers handle. | `src/blooms.py`, `data/question_blooms.csv`, `figures/blooms_*.png`, `docs/week12_blooms.md` | To do |
| 13 | Finalise the results and write the report (data, method, graphs, centrality, Bloom's findings, limitations). Prepare the slides and record the presentation video. | `docs/report.md`, presentation video | To do |
| 14 | Final check: re-run the pipeline from scratch, tidy the README and figures, and submit all deliverables (code, data, figures, report). | Submission | To do |

## Reproduce

```
python src/fetch.py --tag python --from-date 2025-01-01 --to-date 2026-01-01
python src/clean.py
python src/graph.py
python src/centrality.py
```
