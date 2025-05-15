import osmnx as ox                
import networkx as nx             
from codecarbon import EmissionsTracker
import matplotlib.pyplot as plt

class MinHeap:
    def __init__(self, array):
        # Mapeia cada vértice ao seu índice na heap
        self.vertexMap = {idx: idx for idx in range(len(array))}
        # Constrói a heap a partir do array inicial
        self.heap = self.buildHeap(array)

    def isEmpty(self):
        # Verifica se a heap está vazia
        return len(self.heap) == 0

    def buildHeap(self, array):
        # Constrói a heap em O(n) aplicando siftDown de baixo para cima
        firstParentIdx = (len(array) - 2) // 2
        for currentIdx in reversed(range(firstParentIdx + 1)):
            self.siftDown(currentIdx, len(array) - 1, array)
        return array

    def siftDown(self, currentIdx, endIdx, heap):
        # Move o elemento no índice currentIdx para baixo até satisfazer a propriedade de heap
        childOneIdx = 2 * currentIdx + 1
        while childOneIdx <= endIdx:
            # Identifica o outro filho, se existir
            childTwoIdx = 2 * currentIdx + 2 if 2 * currentIdx + 2 <= endIdx else -1
            # Escolhe o filho de menor valor
            if childTwoIdx != -1 and heap[childTwoIdx][1] < heap[childOneIdx][1]:
                idxToSwap = childTwoIdx
            else:
                idxToSwap = childOneIdx
            # Se o filho escolhido for menor, faz o swap
            if heap[idxToSwap][1] < heap[currentIdx][1]:
                self.swap(currentIdx, idxToSwap, heap)
                currentIdx = idxToSwap
                childOneIdx = 2 * currentIdx + 1
            else:
                return

    def siftUp(self, currentIdx, heap):
        # Move o elemento no índice currentIdx para cima até satisfazer a propriedade de heap
        parentIdx = (currentIdx - 1) // 2
        while currentIdx > 0 and heap[currentIdx][1] < heap[parentIdx][1]:
            self.swap(currentIdx, parentIdx, heap)
            currentIdx = parentIdx
            parentIdx = (currentIdx - 1) // 2

    def remove(self):
        # Remove e retorna o par (vértice, distância) mínimo
        self.swap(0, len(self.heap) - 1, self.heap)
        vertex, distance = self.heap.pop()
        # Remove do mapa de vértices
        self.vertexMap.pop(vertex)
        # Restaura a propriedade de heap
        self.siftDown(0, len(self.heap) - 1, self.heap)
        return vertex, distance

    def swap(self, i, j, heap):
        # Troca dois elementos na heap e atualiza o mapa de vértices
        self.vertexMap[heap[i][0]] = j
        self.vertexMap[heap[j][0]] = i
        heap[i], heap[j] = heap[j], heap[i]

    def update(self, vertex, value):
        # Atualiza a distância de um vértice e reordena a heap
        idx = self.vertexMap[vertex]
        self.heap[idx] = (vertex, value)
        self.siftUp(idx, self.heap)

# implementação do algoritmo de Dijkstra usando a MinHeap
def dijkstrasAlgorithmWithPaths(start, edges):
    """
    Dijkstra usando MinHeap, retorna distâncias mínimas e lista de predecessores.
    """
    n = len(edges)
    # inicializa distâncias com infinito e predecessor com None
    minDist = [float("inf")] * n
    minDist[start] = 0
    prev = [None] * n

    # prepara o heap com todos os vértices em distância infinita
    heapArr = [(i, float("inf")) for i in range(n)]
    heap = MinHeap(heapArr)
    # atualiza o vértice de partida para distância 0
    heap.update(start, 0)

    # extrai vértice de menor distância até o heap esvaziar
    while not heap.isEmpty():
        u, du = heap.remove()
        # se a distância for infinita, não há mais vértices alcançáveis
        if du == float("inf"):
            break
        # relaxa todas as arestas (u → v)
        for v, w in edges[u]:
            newDist = du + w
            if newDist < minDist[v]:
                minDist[v] = newDist
                prev[v] = u
                heap.update(v, newDist)

    return minDist, prev

def reconstructPath(prev, start, end):
    """
    Reconstroi o caminho de start até end usando a lista de predecessores.
    """
    path = []
    at = end
    while at is not None:
        path.append(at)
        at = prev[at]
    return list(reversed(path))


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
G = ox.graph_from_point(dca, dist=25_000, network_type="drive")
G = ox.add_edge_speeds(G)       # Adiciona velocidades estimadas
G = ox.add_edge_travel_times(G) # Calcula tempos de viagem

# mapeia nós do grafo para índices e cria lista de adjacência
nodes = list(G.nodes())
idx = {node: i for i, node in enumerate(nodes)}
edges = [[] for _ in nodes]
for u, v, data in G.edges(data=True):
    i, j = idx[u], idx[v]
    length = data.get("length", 0)
    # grafo não-direcionado: adiciona aresta em ambos sentidos
    edges[i].append((j, length))
    edges[j].append((i, length))

# identifica o índice de partida (DCA)
start_node = ox.distance.nearest_nodes(G, X=dca[1], Y=dca[0])
start_idx = idx[start_node]

# roda Dijkstra com CodeCarbon
tracker = EmissionsTracker()
tracker.start()  # Inicia monitor de emissões

minDist, prev = dijkstrasAlgorithmWithPaths(start_idx, edges)
rotas = []
cores = ['brown','blue','green','orange','purple','pink','cyan','yellow', 'red']

print("=== dist (km) e tempo (min) ===")
for bairro, coord in casas.items():
    node_dest = ox.distance.nearest_nodes(G, X=coord[1], Y=coord[0])
    end_idx   = idx[node_dest]

    dist = minDist[end_idx]
    if dist == float("inf"):
        print(f"{bairro:15s}: sem caminho disponível")
        continue

    # reconstrói o caminho via 'prev'
    path_idx = reconstructPath(prev, start_idx, end_idx)
    rota_nos = [nodes[i] for i in path_idx]
    rotas.append(rota_nos)
    
    dist_m = 0
    for u, v in zip(rota_nos[:-1], rota_nos[1:]):
        edge_data = G.get_edge_data(u, v)
        if edge_data is None:
            edge_data = G.get_edge_data(v, u)
        if isinstance(edge_data, dict) and not "length" in edge_data:
            edge_data = list(edge_data.values())[0]
        dist_m += edge_data.get("length", 0)

    dist_km = dist_m / 1000

    tempo_s = 0
    for u, v in zip(rota_nos[:-1], rota_nos[1:]):
        edge_data = G.get_edge_data(u, v)
        if edge_data is None:
            edge_data = G.get_edge_data(v, u)
        if isinstance(edge_data, dict) and not "travel_time" in edge_data:
            edge_data = list(edge_data.values())[0]
        tempo_s += edge_data.get("travel_time", 0)

    tempo_min = tempo_s / 60

    print(f"{bairro:15s}: {dist_km:6.2f} km, {tempo_min:5.1f} min")

# encerra e exibe emissões de CO₂
emissions = tracker.stop()
print(f"\nEmissões estimadas: {emissions:.6f} kg CO₂")

# calcula coordenadas de todas as rotas para definir zoom
all_x = [G.nodes[n]["x"] for rota in rotas for n in rota]
all_y = [G.nodes[n]["y"] for rota in rotas for n in rota]
marg_x = (max(all_x) - min(all_x)) * 0.5
marg_y = (max(all_y) - min(all_y)) * 0.1
west, east = min(all_x) - marg_x, max(all_x) + marg_x
south, north = min(all_y) - marg_y, max(all_y) + marg_y

# desenha grafo
fig, ax = plt.subplots(figsize=(16, 8))
for u, v in G.edges():
    ax.plot(
        [G.nodes[u]['x'], G.nodes[v]['x']],
        [G.nodes[u]['y'], G.nodes[v]['y']],
        color='black', linewidth=0.5
    )

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

ax.set_title("Rotas de bairros de Natal/Parnamirim para DCA/UFRN: Algoritmo Dijkstra com min-heap", pad=12, fontsize=16)

# formatação final
ax.set_aspect('equal', adjustable='box')
ax.axis('off')
plt.tight_layout()
plt.show()
