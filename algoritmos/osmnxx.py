import osmnx as ox
import networkx as nx
from codecarbon import EmissionsTracker

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
G = ox.add_edge_speeds(G) # estima speed_kph onde faltar
G = ox.add_edge_travel_times(G) # calcula travel_time em cada aresta

# nó do DCA
node_dca = ox.distance.nearest_nodes(G, X=dca[1], Y=dca[0])

# inicia rastreamento de emissões
tracker = EmissionsTracker()
tracker.start()

rotas = [] # lista para guardar cada rota calculada
cores = ['brown','blue','green','orange','purple','pink','cyan','yellow', 'red']

print("=== Distâncias e tempos ===")
for i, (bairro, coord) in enumerate(casas.items()):
    # encontra nó destino mais próximo do bairro
    node_dest = ox.distance.nearest_nodes(G, X=coord[1], Y=coord[0])
    try:
        # calcula rota mais curta (peso = length)
        rota = nx.shortest_path(G, node_dca, node_dest, weight="length")
    except nx.NetworkXNoPath:
        print(f"{bairro:15s}: sem caminho disponível")
        continue

    rotas.append(rota)

    # converte a rota em GeoDataFrame para somar comprimentos
    gdf = ox.routing.route_to_gdf(G, rota)
    dist = gdf["length"].sum() # distância em metros
    dist_km = dist/1000 # converte dist para km


    # tempo de viagem em minutos
    time_s = nx.shortest_path_length(G, node_dca, node_dest, weight="travel_time")
    time_min = time_s / 60

    print(f"{bairro:15s}: {dist_km:6.2f} km, {time_min:5.1f} min")
    
    
# plota com OSMnx
fig, ax = ox.plot_graph_routes(
    G,
    rotas,
    route_colors=cores,
    route_linewidth=4,
    node_size=0,
    figsize=(16, 8),
    bgcolor='white',        
    edge_color='black',     
    edge_linewidth=0.5,     
    show=False,
    close=False
)

# calcula coordenadas de todas as rotas para definir zoom
all_xs = [G.nodes[n]["x"] for rota in rotas for n in rota]
all_ys = [G.nodes[n]["y"] for rota in rotas for n in rota]
marg_x = (max(all_xs) - min(all_xs)) * 0.5
marg_y = (max(all_ys) - min(all_ys)) * 0.1

# aplica limites do eixo para zoom automático
ax.set_xlim(min(all_xs) - marg_x, max(all_xs) + marg_x)
ax.set_ylim(min(all_ys) - marg_y, max(all_ys) + marg_y)

fig.tight_layout()
fig.show()


# encera coleta de emissões
emissions = tracker.stop()
print(f"\nEmissões estimadas: {emissions:.6f} kg CO₂")