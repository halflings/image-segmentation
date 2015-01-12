import sys
from collections import Counter
from math import exp, log, pi, sqrt

import numpy as np
import graph_tool.all as gt
from PIL import Image

OBJ_COLOR = [0.7, 0.2, 0.2, 0.8]
BKG_COLOR = [0.2, 0.8, 0.2, 0.8]
NEUTRAL_COLOR = [0.5, 0.5, 0.5, 1.]

def norm_pdf(x, mu, sigma):
    return (1/(sqrt(2*pi)*abs(sigma)))*exp(-x**2/2)

class SegmentedImage(object):
    def __init__(self, image_path):
        self.img = Image.open(image_path)
        self.w, self.h = self.img.size
        # Caching the pixel values because Image.getpixel is really slow
        self.pixel_values = {p: self.img.getpixel(p)[0] for p in self.pixels()}

        # Seeds
        self.obj_seeds = []
        self.bkg_seeds = []

        # Factors
        self.lambda_factor = 2.
        self.sigma_factor = 30.

        self.calculate_boundary_costs()
        self.create_graph()

    def pixels(self):
        for x in xrange(self.w):
            for y in xrange(self.h):
                yield (x, y)

    def special_neighbours(self, x, y):
        return ((i, j) for (i, j) in [(x+1, y), (x, y+1), (x+1, y+1), (x+1, y-1)]
                 if 0 <= i < self.w and 0 <= j < self.h and (i != x or j != y))

    def boundary_penalty(self, p_a, p_b):
        i_delta = self.pixel_values[p_a] - self.pixel_values[p_a]
        distance = abs(p_a[0] - p_b[0]) + abs(p_a[1] - p_b[1])
        return exp(- i_delta**2 / (2 * self.sigma_factor**2)) / distance

    def calculate_boundary_costs(self):
        self.boundary_costs = {}
        for p in self.pixels():
            self.boundary_costs[p] = {}
            for n_p in self.special_neighbours(*p):
                self.boundary_costs[p][n_p] = self.boundary_penalty(p, n_p)

        # calculating K
        self.k_factor = 1. + max(sum(self.boundary_costs[p].values()) for p in self.pixels())

    def calculate_histogram(self, points):
        values_count = Counter(self.pixel_values[p] for p in points)
        return {value : float(count) / len(points) for value, count in values_count.iteritems()}

    def calculate_normal(self, points):
        values = [self.pixel_values[p] for p in points]
        return np.mean(values), np.std(values) + 0.0001 # HOTFIX: ugly ugly fix to avoid a nil deviation

    def regional_cost(self, point, mean, std):
        return self.lambda_factor * log(norm_pdf(self.pixel_values[point], mean, std) + 0.00000001)

    def calculate_costs(self, obj_seeds, bkg_seeds):
        self.obj_seeds, self.bkg_seeds = obj_seeds, bkg_seeds
        obj_mean, obj_std = self.calculate_normal(obj_seeds)
        bkg_mean, bkg_std = self.calculate_normal(bkg_seeds)

        self.regional_penalty_obj = {p: 0 if p in obj_seeds else self.k_factor if p in bkg_seeds else self.regional_cost(p, obj_mean, obj_std)
                                     for p in self.pixels()}
        self.regional_penalty_bkg = {p: self.k_factor if p in obj_seeds else 0 if p in bkg_seeds else self.regional_cost(p, bkg_mean, bkg_std)
                                     for p in self.pixels()}

        self.update_graph()

    def create_graph(self):
        self.graph = gt.Graph(directed=False)
        g = self.graph
        self.graph_penalty = g.new_edge_property("double")

        # Properties used for visualization
        self.graph_position = g.new_vertex_property("vector<float>")
        self.graph_intensity = g.new_vertex_property("short")
        self.graph_vertex_label = g.new_vertex_property("string")
        self.graph_vertex_color = g.new_vertex_property("vector<double>")
        self.graph_edge_color = g.new_edge_property("vector<double>")

        # Mapping points to vertices/edges
        self.point_to_vertex = dict()
        self.tuple_to_edge = dict()
        self.obj_edges = dict()
        self.bkg_edges = dict()

        # Creating vertice
        for p in self.pixels():
            vertex = g.add_vertex()
            self.point_to_vertex[p] = vertex
            self.graph_position[vertex] = (p[0], p[1])
            self.graph_intensity[vertex] = self.pixel_values[p]
            self.graph_vertex_label[vertex] = "%03d" % self.pixel_values[p]
            rel_color = self.pixel_values[p] / 255.
            self.graph_vertex_color[vertex] = [rel_color, rel_color, rel_color, 1]

        # Creating inter-pixel edges
        for x in xrange(0, self.w):
            for y in xrange(0, self.h):
                p = (x, y)
                for n_p in self.special_neighbours(*p):
                    edge = g.add_edge(self.point_to_vertex[p], self.point_to_vertex[n_p])
                    self.tuple_to_edge[(p, n_p)] = edge
                    self.graph_edge_color[edge] = NEUTRAL_COLOR

        # Creating obj/Bkg edges
        self.obj_vertex = g.add_vertex()
        self.bkg_vertex = g.add_vertex()

        for p in self.pixels():
            obj_edge = g.add_edge(self.point_to_vertex[p], self.obj_vertex)
            bkg_edge = g.add_edge(self.point_to_vertex[p], self.bkg_vertex)

            self.obj_edges[p] = obj_edge
            self.bkg_edges[p] = bkg_edge

            self.graph_edge_color[obj_edge] = OBJ_COLOR
            self.graph_edge_color[bkg_edge] = BKG_COLOR

        self.graph_position[self.obj_vertex] = (-0.05*self.w, -0.05*self.h)
        self.graph_position[self.bkg_vertex] = (1.05*self.w, 1.05*self.h)

        self.graph_vertex_color[self.obj_vertex] = OBJ_COLOR
        self.graph_vertex_label[self.obj_vertex] = 'Obj'
        self.graph_vertex_color[self.bkg_vertex] = BKG_COLOR
        self.graph_vertex_label[self.bkg_vertex] = 'Bkg'

    def update_graph(self):
        # Update vertices colors (seeds)
        for p in self.pixels():
            vertex = self.point_to_vertex[p]
            rel_color = self.pixel_values[p] / 255.
            if p in self.obj_seeds:
                self.graph_vertex_color[vertex] = OBJ_COLOR
            elif p in self.bkg_seeds:
                self.graph_vertex_color[vertex] = BKG_COLOR
            else:
                self.graph_vertex_color[vertex] = [rel_color, rel_color, rel_color, 1]

        # Boundary costs
        for x in xrange(0, self.w, 2):
            for y in xrange(0, self.h, 2):
                p = (x, y)
                for n_p in self.special_neighbours(*p):
                    edge = self.tuple_to_edge.get((p, n_p)) or self.tuple_to_edge.get((n_p, p))
                    self.graph_penalty[edge] = self.boundary_costs[p][n_p] # self.boundary_penalty(p, n_p)

        # Regional costs
        for p in self.pixels():
            obj_edge = self.obj_edges[p]
            bkg_edge = self.bkg_edges[p]

            self.graph_penalty[obj_edge] = self.regional_penalty_obj[p]
            self.graph_penalty[bkg_edge] = self.regional_penalty_bkg[p]

    def save_graph(self, graph_path):
        gt.graph_draw(self.graph, vertex_text=self.graph_vertex_label, pos=self.graph_position, vertex_font_size=18,
                      edge_pen_width=gt.prop_to_size(self.graph_penalty, mi=0, ma=8, power=1),
                      vertex_fill_color=self.graph_vertex_color, edge_color=self.graph_edge_color,
                      output_size=(self.w * 50, self.h * 50), output=graph_path)

if __name__ == '__main__':
    image_path = sys.argv[1] if len(sys.argv) > 1 else 'mini-test.jpg'
    img = SegmentedImage(image_path)

    sorted_pixels = sorted(img.pixel_values.keys(), key=lambda p : img.pixel_values[p])
    dummy_obj_seeds = sorted_pixels[:10]
    dummy_bkg_seeds = sorted_pixels[-10:]

    img.calculate_costs(dummy_obj_seeds, dummy_bkg_seeds)
    img.save_graph('graph.png')
