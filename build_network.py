#!/usr/bin/env python3
"""
build_network.py: 
Generates an interactive inventor collaboration network visualization as index.html.
Usage: python build_network.py [Patent_final.xlsx]
"""
import sys
import pandas as pd
import networkx as nx
import community.community_louvain as community_louvain
import json

def build_graph(df):
    """
    Builds an undirected graph where nodes are inventors and edges indicate co-inventorship.
    Edge weights count the number of patents two inventors share.
    """
    G = nx.Graph()
    for inv in df['Inventors'].dropna():
        # Split semicolon-delimited inventor list
        inventors = [n.strip() for n in inv.split(';') if n.strip()]
        for i in range(len(inventors)):
            for j in range(i+1, len(inventors)):
                u, v = inventors[i], inventors[j]
                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)
    return G

def filter_top_nodes(G, top_n=80):
    """
    Keeps only the subgraph induced by the top_n nodes sorted by degree.
    """
    top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:top_n]
    keep = {n for n,_ in top_nodes}
    return G.subgraph(keep).copy()

def detect_communities(G):
    """
    Applies the Louvain method to find collaboration communities.
    Returns a dict mapping node -> community ID.
    """
    return community_louvain.best_partition(G)

def graph_to_json(G, partition):
    """
    Converts the graph and partition into JSON-serializable node and edge lists
    suitable for vis.js rendering.
    """
    nodes = []
    for n in G.nodes():
        nodes.append({
            'id': n,
            'label': n,
            'value': G.degree(n),  # size ~ number of collaborators
            'title': f"{n}<br>Connections: {G.degree(n)}",  # hover-popup info
            'group': partition[n],
            'color': f"hsl({(partition[n]*40)%360},70%,50%)"
        })
    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            'from': u,
            'to': v,
            'value': d['weight'],      # thickness ~ joint patents
            'label': str(d['weight']), # small number along edge
            'title': f"Collaboration between {u} and {v}<br>Patents: {d['weight']}"
        })
    return nodes, edges

def generate_html(nodes, edges, output_file='index.html'):
    """
    Writes the interactive HTML file, embedding nodes and edges JSON,
    plus an on-screen explanation overlay.
    """
    html_template = """<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>Inventor Collaboration Network</title>
  <link href=\"https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css\" rel=\"stylesheet\" />
  <script src=\"https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js\"></script>
  <style>
    html, body {{ margin:0; padding:0; height:100%; width:100%; overflow:hidden; }}
    #network {{ width:100%; height:100%; position:relative; z-index:1; }}
    #explanation {{
      position:absolute; top:10px; left:10px; z-index:2;
      background: rgba(255,255,255,0.8); padding:10px;
      border-radius:5px; max-width:300px;
      font-family:Arial, sans-serif; font-size:14px;
    }}
  </style>
</head>
<body>
  <div id=\"explanation\">
    <strong>Inventor Collaboration Network</strong><br>
    Each node is an inventor (size ∝ number of collaborators).<br>
    Node color = collaboration community.<br>
    Edge thickness ∝ number of joint patents.<br>
    Hover on a node to see “Connections: N”.<br>
    Hover on an edge to see exact patent count.
  </div>
  <div id=\"network\"></div>
  <script>
    var nodes = new vis.DataSet(NODES_JSON_PLACEHOLDER);
    var edges = new vis.DataSet(EDGES_JSON_PLACEHOLDER);

    var container = document.getElementById("network");
    var data = {{ nodes: nodes, edges: edges }};
    var options = {{
      physics: {{
        barnesHut: {{
          gravitationalConstant: -5000,
          centralGravity: 0.3,
          springLength: 250,
          damping: 0.95
        }}
      }},
      interaction: {{ hover: true, tooltipDelay: 100 }}
    }};
    var network = new vis.Network(container, data, options);
    network.addControl("physics");
  </script>
</body>
</html>"""
    # Embed JSON data into template
    html = html_template.replace('NODES_JSON_PLACEHOLDER', json.dumps(nodes, indent=2)) \
                        .replace('EDGES_JSON_PLACEHOLDER', json.dumps(edges, indent=2))
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✔ {output_file} generated!")

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'Patent_final.xlsx'
    df = pd.read_excel(input_file)
    G = build_graph(df)
    G_sub = filter_top_nodes(G, top_n=80)
    partition = detect_communities(G_sub)
    nodes, edges = graph_to_json(G_sub, partition)
    generate_html(nodes, edges)

if __name__ == "__main__":
    main()
