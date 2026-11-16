"""Centrality report for the filtered user graph (week 11).

For each of the ~20 nodes selected in graph.py, computes:

  in-degree    number of distinct users who answered this user's questions
  out-degree   number of distinct users whose questions this user answered
  (weighted versions count questions instead of distinct users)
  hub          HITS hub score: high when the user answers people who are
               themselves strong authorities
  authority    HITS authority score: high when the user is answered by
               strong hubs

Edges point answerer -> asker, so in this network a hub is a helper and an
authority is a well-served asker. HITS uses the edge weights (questions
answered), and scores are normalised to sum to 1.

Writes data/centrality.csv and figures/hits.png, and prints a Markdown table.

Usage:
    python src/centrality.py --n 20
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from graph import DATA, FIGURES, build_graph, load_data, role, select_top_nodes


def centrality_table(H, G):
    hubs, auths = nx.hits(H, max_iter=1000, normalized=True)
    full_hubs, full_auths = nx.hits(G, max_iter=1000, normalized=True)
    hub_rank = {n: i + 1 for i, n in enumerate(sorted(G, key=full_hubs.get, reverse=True))}
    auth_rank = {n: i + 1 for i, n in enumerate(sorted(G, key=full_auths.get, reverse=True))}
    rows = []
    for n in H:
        rows.append({
            "user_id": n,
            "name": H.nodes[n]["name"],
            "role": role(H, n),
            "in_degree": H.in_degree(n),
            "out_degree": H.out_degree(n),
            "in_degree_w": H.in_degree(n, weight="weight"),
            "out_degree_w": H.out_degree(n, weight="weight"),
            "hub": hubs[n],
            "authority": auths[n],
            # Context from the whole 2025 graph, not just the 20-node view.
            "full_in_degree": G.in_degree(n),
            "full_out_degree": G.out_degree(n),
            "full_hub_rank": hub_rank[n],
            "full_authority_rank": auth_rank[n],
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["hub", "authority"], ascending=False).reset_index(drop=True)


def plot_hits(df, path):
    d = df.sort_values("hub")
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    axes[0].barh(d["name"], d["hub"], color="#2a6fdb")
    axes[0].set_title("Hub score (answers good authorities)")
    axes[1].barh(d["name"], d["authority"], color="#e8833a")
    axes[1].set_title("Authority score (answered by good hubs)")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("HITS score (sums to 1)")
    fig.suptitle("HITS scores for the filtered user graph (edge = answerer → asker)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def markdown(df):
    cols = ["name", "role", "in_degree", "out_degree", "in_degree_w", "out_degree_w",
            "hub", "authority"]
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    body = ""
    for r in df[cols].itertuples(index=False):
        cells = [f"{v:.3f}" if isinstance(v, float) else str(v) for v in r]
        body += "| " + " | ".join(cells) + " |\n"
    return head + body


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    G, _ = build_graph(*load_data())
    H = select_top_nodes(G, args.n)
    df = centrality_table(H, G)
    df.to_csv(DATA / "centrality.csv", index=False)
    plot_hits(df, FIGURES / "hits.png")
    print(markdown(df))
    print(f"wrote {DATA / 'centrality.csv'} and {FIGURES / 'hits.png'}")


if __name__ == "__main__":
    main()
