import osmnx as sm       
import networkx as nx
from codecarbon import EmissionsTracker
import matplotlib.pyplot as plt

# ponto central: DCA/UFRN
dca = (-5.842670739741108, -35.19741424605443)

# bairros de Natal/Parnamirim e suas coords (lat, lon)
casas = {
    "Candelária":(-5.844528713666761, -35.221554590449806),
    "Nova Parnamirim":(-5.895888968709289, -35.20185937510485),
    "Praia do Meio":(-5.775552158030685, -35.194558261614475),
    "Nova Descoberta":(-5.821881324253735, -35.19754531743318),
    "Alecrim":(-5.796163414530586, -35.21495410394186),
    "Coophab":(-5.927382950179012, -35.204966446268195),
    "Ponta Negra":(-5.885624620814022, -35.18163073277702),
    "Lagoa Seca":(-5.805198065560546, -35.211873930925066),
    "Cajupiranga":(-5.950008534051496, -35.26116298674303),
}

# constrói o grafo de ruas num raio de 25 km ao redor do DCA
G = sm.graph_from_point(dca, dist=25_000, network_type="drive")
G = sm.add_edge_speeds(G)
G = sm.add_edge_travel_times(G)

# prepara lista de adjacência para Dijkstra
nodes = list(G.nodes())
idx   = {node: i for i, node in enumerate(nodes)}
edges = [[] for _ in nodes]
for u, v, data in G.edges(data=True):
    i, j = idx[u], idx[v]
    length = data.get("length", 0)
    edges[i].append((j, length))
    edges[j].append((i, length))

# encontra índice de partida
node_dca  = sm.distance.nearest_nodes(G, X=dca[1], Y=dca[0])
start_idx = idx[node_dca]

# funções de Dijkstra
def dijkstrasAlgorithmWithPaths(start, edges):
    n = len(edges)
    dist = [float("inf")]*n; dist[start]=0
    visited=set(); prev=[None]*n
    while len(visited)<n:
        u, du = getVertexWithMinDistance(dist, visited)
        if du==float("inf"): break
        visited.add(u)
        for v, w in edges[u]:
            if v in visited: continue
            nd = du + w
            if nd < dist[v]:
                dist[v]=nd
                prev[v]=u
    return dist, prev

def getVertexWithMinDistance(distances, visited):
    mv, vi = float("inf"), None
    for i, d in enumerate(distances):
        if i in visited: continue
        if d < mv:
            mv, vi = d, i
    return vi, mv

def reconstructPath(prev, start, end):
    path=[]
    at=end
    while at is not None:
        path.append(at)
        at=prev[at]
    return list(reversed(path))

# roda Dijkstra com CodeCarbon
tracker = EmissionsTracker(); tracker.start()
minDist, prev = dijkstrasAlgorithmWithPaths(start_idx, edges)

rotas = []; 
cores = ['brown','blue','green','orange','purple','pink','cyan','yellow', 'red']
print("=== dist (km) e tempo (min) ===")
for bairro, coord in casas.items():
    node_dest = sm.distance.nearest_nodes(G, X=coord[1], Y=coord[0])
    end_idx   = idx[node_dest]
    if minDist[end_idx]==float("inf"):
        print(f"{bairro:15s}: sem caminho")
        continue
    path_idx = reconstructPath(prev, start_idx, end_idx)
    rota_nos = [nodes[i] for i in path_idx]
    rotas.append(rota_nos)

    dist_km   = minDist[end_idx]/1000
    time_s    = nx.shortest_path_length(G, node_dca, node_dest, weight="travel_time")
    time_min  = time_s/60
    print(f"{bairro:15s}: {dist_km:6.2f} km, {time_min:5.1f} min")


# encerra e exibe emissões de CO₂
emissions = tracker.stop()
print(f"\nEmissões estimadas: {emissions:.6f} kg CO₂")


# calcula coordenadas de todas as rotas para definir zoom
all_x = [G.nodes[n]["x"] for rota in rotas for n in rota]
all_y = [G.nodes[n]["y"] for rota in rotas for n in rota]
m_x, m_y = (max(all_x)-min(all_x))*0.5, (max(all_y)-min(all_y))*0.1
west, east   = min(all_x)-m_x, max(all_x)+m_x
south, north = min(all_y)-m_y, max(all_y)+m_y

# desenha grafo
fig, ax = plt.subplots(figsize=(16,8))
for u, v in G.edges():
    ax.plot([G.nodes[u]['x'],G.nodes[v]['x']],
            [G.nodes[u]['y'],G.nodes[v]['y']],
            color='black', linewidth=0.5)

# sobrepõe rotas coloridas com label para a legenda
for rota, cor, bairro in zip(rotas, cores, casas.keys()):
    xs = [G.nodes[n]['x'] for n in rota]
    ys = [G.nodes[n]['y'] for n in rota]
    ax.plot(xs, ys, color=cor, linewidth=3, label=bairro)

# zoom e acabamento
ax.set_xlim(west, east)
ax.set_ylim(south, north)

# coloca estrela no DCA/UFRN
ax.scatter(
    dca[1],          
    dca[0],          
    c='pink',         
    s=200,           
    marker='*',      
    label='DCA/UFRN',
    zorder=5
)

# exibe a legenda
ax.legend(loc='lower right', fontsize='small', frameon=True, ncol=2)

ax.set_title("Rotas de bairros de Natal/Parnamirim para DCA/UFRN: Algoritmo Dijkstra", pad=12, fontsize=16)

# formatação final
ax.set_aspect('equal', adjustable='box')
ax.axis('off')
plt.tight_layout()
plt.show()
