from build_database import load_database
import json
from pprint import pprint
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def load_followings_data():
    ''' Load data dict of user followings for graph analysis '''
    df = load_database(usecols = ['username', 'followings','protected'])

    followings = {}

    for row in df.itertuples():
        if row.protected == False:
            data = set(json.loads(row.followings.replace("'", '"')))

            if len(data) > 0:
                followings[row.username] = data

    return followings

def generate_graph_html(weight_thresh = 0.025):
    followings = load_followings_data()
    users = list(followings.keys())
    num_users = len(followings)

    #build weighted graph
    G = nx.Graph()
    similarities = []

    for user in users:
        G.add_node(user)

    for r in range(num_users):
        for c in range(r + 1, num_users): # c > r
            similarity = jaccard(followings[users[r]], followings[users[c]])
            similarities.append(similarity)

            if similarity > weight_thresh:
                G.add_edge(users[r], users[c], weight = similarity)

    # generate / plot NetworkX graph
    pos = nx.spring_layout(G, seed = 5, iterations = 200) # positions for all nodes - seed for reproducibility
    #pos = nx.kamada_kawai_layout(G)
    html = get_plotly_plot_html(G, pos)
    return html


def jaccard(s1: set, s2: set):
    ''' Computes Jaccard index of 2 sets. Intersection / union '''
    inter = len(s1.intersection(s2))
    union = len(s1.union(s2))

    if union == 0:
        return 0

    return inter/union

def get_plotly_plot_html(G, pos):
    ''' Generate a plot of the Network Graph G with node positions pos and
    return the HTML of this plot for frontend rendering.'''

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='rgba(255,0,0,0.3)'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    text = []
    for node in G.nodes():
        x, y = pos[node]
        text.append(f'{node}'),
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='text+markers',
        hoverinfo='text',
        text = text,
        textposition = 'middle center',
        textfont=dict(
            family="sans serif",
            size=18,
            color="black"
        ),
        marker=dict(
            size=10,
            line_width=1,
            color = 'rgba(0,0,255,0.3)'
            )
        )

    fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                #title='<br>Network graph made with Python',
                #titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=5,l=5,r=5,t=5),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                dragmode='pan',
                )
            )
    plotly_config = {'scrollZoom': True}
    #fig.show(config = plotly_config)
    html = fig.to_html(full_html=False, include_plotlyjs=False, config = plotly_config)
    return html

