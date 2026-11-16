"""Build and draw the directed user graph (week 10).

Nodes are users. An edge u -> v means user u answered a question asked by
user v; its weight is the number of v's questions that u answered. Users
answering their own question are skipped (self-loops).

Filtering to ~20 nodes: the most active users are almost all answerers who
rarely answer each other, so a plain "top 20 by activity" leaves the picture
nearly edgeless. Instead the subgraph is grown greedily from the busiest
user, always adding the neighbour with the most links into the current set
(ties broken by activity). The result is the densest connected corner of the
network: the main answerers plus the askers they have in common.

Writes:
    data/edges.csv          full weighted edge list
    data/top_nodes.csv      the selected nodes with activity counts
    figures/user_graph.png  the drawing (node size = questions + answers,
                            edge width = questions answered for that pair)

Usage:
    python src/graph.py --n 20
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
FIGURES = REPO_ROOT / "figures"

ANSWERER_COLOR = "#2a6fdb"
ASKER_COLOR = "#e8833a"
BOTH_COLOR = "#4caf50"


def load_data(data_dir=DATA):
    questions = pd.read_csv(data_dir / "questions.csv")
    answers = pd.read_csv(data_dir / "answers.csv")
    return questions, answers


def interactions(questions, answers):
    """One row per (answer, asker) pair, self-answers removed."""
    pairs = answers.merge(questions[["question_id", "asker_id", "asker_name"]], on="question_id")
    return pairs[pairs["answerer_id"] != pairs["asker_id"]]


def activity(questions, answers):
    """Questions asked, answers given, and display name per user."""
    asked = questions.groupby("asker_id").size().rename("questions_asked")
    answered = answers.groupby("answerer_id").size().rename("answers_given")
    act = pd.concat([asked, answered], axis=1).fillna(0).astype(int)
    act["activity"] = act["questions_asked"] + act["answers_given"]
    names = pd.concat([
        questions.set_index("asker_id")["asker_name"],
        answers.set_index("answerer_id")["answerer_name"],
    ])
    act["name"] = names[~names.index.duplicated()].reindex(act.index)
    act.index.name = "user_id"
    return act


def build_graph(questions, answers):
    pairs = interactions(questions, answers)
    edges = (pairs.groupby(["answerer_id", "asker_id"]).size()
             .rename("weight").reset_index())
    act = activity(questions, answers)

    G = nx.DiGraph()
    for uid, row in act.iterrows():
        G.add_node(uid, name=row["name"], questions_asked=row["questions_asked"],
                   answers_given=row["answers_given"], activity=row["activity"])
    for r in edges.itertuples(index=False):
        G.add_edge(r.answerer_id, r.asker_id, weight=r.weight)
    G.remove_nodes_from([n for n in list(G) if G.degree(n) == 0])
    # Role in the full graph: does the user answer others, get answered, or both?
    for n in G:
        helps, helped = G.out_degree(n) > 0, G.in_degree(n) > 0
        G.nodes[n]["role"] = "both" if helps and helped else ("answerer" if helps else "asker")
    return G, edges


def select_top_nodes(G, n=20):
    """Greedy densest connected subgraph of about n nodes (see module docstring)."""
    U = G.to_undirected()
    act = nx.get_node_attributes(G, "activity")
    wdeg = dict(G.degree(weight="weight"))
    chosen = {max(wdeg, key=lambda u: (wdeg[u], act[u]))}
    while len(chosen) < n:
        frontier = {v for u in chosen for v in U[u]} - chosen
        if not frontier:
            break
        best = max(frontier, key=lambda v: (sum(1 for t in U[v] if t in chosen),
                                             wdeg[v], act[v]))
        chosen.add(best)
    return G.subgraph(chosen).copy()


def role(G, node):
    """Role from the full graph (set in build_graph), so a subgraph keeps it."""
    return G.nodes[node]["role"]


def draw(H, path, title):
    colors = {"answerer": ANSWERER_COLOR, "asker": ASKER_COLOR, "both": BOTH_COLOR}
    act = nx.get_node_attributes(H, "activity")
    sizes = [150 + 25 * act[n] for n in H]
    widths = [1.2 * H[u][v]["weight"] for u, v in H.edges]
    node_colors = [colors[role(H, n)] for n in H]
    labels = {n: f"{H.nodes[n]['name']}\n({act[n]})" for n in H}

    pos = nx.kamada_kawai_layout(H.to_undirected())
    fig, ax = plt.subplots(figsize=(13, 10))
    nx.draw_networkx_edges(H, pos, ax=ax, width=widths, edge_color="#777",
                           arrows=True, arrowstyle="-|>", arrowsize=14,
                           node_size=sizes, connectionstyle="arc3,rad=0.08")
    nx.draw_networkx_nodes(H, pos, ax=ax, node_size=sizes, node_color=node_colors,
                           edgecolors="white", linewidths=1.5)
    nx.draw_networkx_labels(H, pos, labels, ax=ax, font_size=8)
    nx.draw_networkx_edge_labels(
        H, pos, ax=ax, font_size=7,
        edge_labels={(u, v): d["weight"] for u, v, d in H.edges(data=True) if d["weight"] > 1})

    for label, c in [("only answers others", ANSWERER_COLOR), ("only gets answered", ASKER_COLOR),
                     ("both", BOTH_COLOR)]:
        ax.scatter([], [], s=120, c=c, label=label)
    ax.legend(loc="lower left", frameon=False, title="Role in full dataset")
    ax.set_title(title + "\nedge = answerer → asker, width = questions answered; "
                 "node size and (n) = questions asked + answers given", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=20, help="number of nodes to keep")
    args = parser.parse_args()

    questions, answers = load_data()
    G, edges = build_graph(questions, answers)
    print(f"full graph: {G.number_of_nodes()} users, {G.number_of_edges()} edges, "
          f"{int(edges['weight'].sum())} answer interactions")

    H = select_top_nodes(G, args.n)
    print(f"filtered:   {H.number_of_nodes()} users, {H.number_of_edges()} edges")

    edges.to_csv(DATA / "edges.csv", index=False)
    top = pd.DataFrame([{"user_id": n, **H.nodes[n]} for n in H])
    top.sort_values("activity", ascending=False).to_csv(DATA / "top_nodes.csv", index=False)
    draw(H, FIGURES / "user_graph.png",
         f"StackOverflow [python] 2025 — top {H.number_of_nodes()} users")
    print(f"wrote {DATA / 'edges.csv'}, {DATA / 'top_nodes.csv'}, {FIGURES / 'user_graph.png'}")


if __name__ == "__main__":
    main()
