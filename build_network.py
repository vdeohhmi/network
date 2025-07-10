import pandas as pd
import networkx as nx
import community.community_louvain as community_louvain
import json

# 1) Read your Excel file
df = pd.read_excel('Patent_final.xlsx')

# 2) Build the co-inventor graph
G = nx.Graph()
for inv in df['Inventors'].dropna():
    inventors = [n.strip() for n in inv.split(';') if n.strip()]
    for i in range(len(inventors)):
        for j in range(i+1, len(inventors)):
            u, v = inventors[i], inventors[j]
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1)

# 3) Keep only top N inventors by degree
N = 80
top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:N]
sub_nodes = {n for n, _ in top_nodes}
G_sub = G.subgraph(sub_nodes).copy()

# 4) Compute Louvain communities
partition = community_louvain.best_partition(G_sub)

# 5) Build JSON-serializable nodes & edges lists
nodes = [{
    'id': node,
    'label': node,
    'value': G_sub.degree(node),
    'title': f"{node}<br>Connections: {G_sub.degree(node)}",
    'color': f"hsl({(partition[node] * 40) % 360}, 70%, 50%)"
} for node in G_sub.nodes()]

edges = [{
    'from': u,
    'to': v,
    'value': data['weight'],
    'title': f"Collaboration between {u} and {v}<br>Patents: {data['weight']}"
} for u, v, data in G_sub.edges(data=True)]

# 6) Load HTML template
with open('template.html', 'r', encoding='utf-8') as f:
    template = f.read()

# 7) Inject nodes & edges
html = template.replace(
    'var nodes = new vis.DataSet([]);',
    'var nodes = new vis.DataSet(' + json.dumps(nodes, indent=2) + ');'
).replace(
    'var edges = new vis.DataSet([]);',
    'var edges = new vis.DataSet(' + json.dumps(edges, indent=2) + ');'
)

# 8) Write out final page
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✔ index.html generated!")
