import graph_tool.all as gt

from numpy.random import seed, random
from scipy.linalg import norm

def test1():
    gt.seed_rng(42)
    seed(42)
    NUMBER_OF_NODES = 20
    points = random((NUMBER_OF_NODES, 2))
    points[0] = [0, 0]
    points[1] = [1, 1]
    g, pos = gt.triangulation(points, type="delaunay")
    g.set_directed(True)
    edges = list(g.edges())
    # reciprocate edges
    for e in edges:
       g.add_edge(e.target(), e.source())
    # The capacity will be defined as the inverse euclidean distance
    cap = g.new_edge_property("double")
    for e in g.edges():
        cap[e] = min(1.0 / norm(pos[e.target()].a - pos[e.source()].a), 10)
    g.edge_properties["cap"] = cap
    g.vertex_properties["pos"] = pos
    g.save("flow-example.xml.gz")
    gt.graph_draw(g, pos=pos, edge_pen_width=gt.prop_to_size(cap, mi=0, ma=3, power=1),
                  output="flow-example.pdf")

if __name__ == '__main__':
    test1()