from collections import Counter
from math import exp, pi, sqrt

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

        # Dummy values
        self.lambda_factor = 2.
        self.sigma_factor = 30.

        self.calculate_boundary_costs()

    def pixels(self):
        for x in xrange(self.w):
            for y in xrange(self.h):
                yield (x, y)

    def neighbours(self, x, y):
        return ((i, j) for i in xrange(x-1, x+2) for j in xrange(y-1, y+2)
                 if 0 <= i < self.w and 0 <= j < self.h and (i != x or j != y))

    def boundary_penalty(self, p_a, p_b):
        i_delta = self.pixel_values[p_a] - self.pixel_values[p_a]
        distance = abs(p_a[0] - p_b[0]) + abs(p_a[1] - p_b[1])
        return exp(- i_delta**2 / (2 * self.sigma_factor**2)) / distance

    def calculate_boundary_costs(self):
        self.boundary_costs = {}
        for p in self.pixels():
            self.boundary_costs[p] = {}
            for n_p in self.neighbours(*p):
                self.boundary_costs[p][n_p] = self.boundary_penalty(p, n_p)

        # calculating K
        self.k_factor = 1. + max(sum(self.boundary_costs[p].values()) for p in self.pixels())

    def calculate_histogram(self, points):
        values_count = Counter(self.pixel_values[p] for p in points)
        return {value : float(count) / len(points) for value, count in values_count.iteritems()}

    def calculate_normal(self, points):
        values = [self.pixel_values[p] for p in points]
        return np.mean(values), np.std(values) + 0.0001

    def regional_cost(self, point, mean, std):
        return self.lambda_factor * norm_pdf(self.pixel_values[point], mean, std)

    def calculate_costs(self, obj_seeds, bkg_seeds):
        self.obj_seeds, self.bkg_seeds = obj_seeds, bkg_seeds
        obj_mean, obj_std = self.calculate_normal(obj_seeds)
        bkg_mean, bkg_std = self.calculate_normal(bkg_seeds)

        self.regional_penalty_obj = {p: 0 if p in obj_seeds else self.k_factor if p in bkg_seeds else self.regional_cost(p, obj_mean, obj_std)
                                     for p in self.pixels()}
        self.regional_penalty_bkg = {p: self.k_factor if p in obj_seeds else 0 if p in bkg_seeds else self.regional_cost(p, bkg_mean, bkg_std)
                                     for p in self.pixels()}

    def create_graph(self):
        g = gt.Graph(directed=False)
        penalty = g.new_edge_property("double")

        # Properties used for visualization
        position = g.new_vertex_property("vector<float>")
        intensity = g.new_vertex_property("short")
        vertex_label = g.new_vertex_property("string")
        vertex_color = g.new_vertex_property("vector<double>")
        edge_color = g.new_edge_property("vector<double>")

        point_to_vertex = dict()

        # Creating vertice
        for p in self.pixels():
            vertex = g.add_vertex()
            position[vertex] = (p[0], p[1])
            intensity[vertex] = self.pixel_values[p]
            vertex_label[vertex] = str(self.pixel_values[p])
            rel_color = self.pixel_values[p] / 255.
            if p in self.obj_seeds:
                vertex_color[vertex] = OBJ_COLOR
            elif p in self.bkg_seeds:
                vertex_color[vertex] = BKG_COLOR
            else:
                vertex_color[vertex] = [rel_color, rel_color, rel_color, 1]
            point_to_vertex[p] = vertex

        # Boundary costs
        for x in xrange(0, self.w, 2):
            for y in xrange(0, self.h, 2):
                p = (x, y)
                for n_p in self.neighbours(*p):
                    edge = g.add_edge(point_to_vertex[p], point_to_vertex[n_p])
                    penalty[edge] = self.boundary_penalty(p, n_p)
                    edge_color[edge] = NEUTRAL_COLOR

        # Regional costs
        obj_vertex = g.add_vertex()
        bkg_vertex = g.add_vertex()

        for p in self.pixels():
            obj_edge = g.add_edge(point_to_vertex[p], obj_vertex)
            bkg_edge = g.add_edge(point_to_vertex[p], bkg_vertex)

            penalty[obj_edge] = self.regional_penalty_obj[p]
            penalty[bkg_edge] = self.regional_penalty_bkg[p]

            edge_color[obj_edge] = OBJ_COLOR
            edge_color[bkg_edge] = BKG_COLOR

        position[obj_vertex] = (-0.05*self.w, -0.05*self.h)
        position[bkg_vertex] = (1.05*self.w, 1.05*self.h)

        vertex_color[obj_vertex] = OBJ_COLOR
        vertex_label[obj_vertex] = 'Obj'
        vertex_color[bkg_vertex] = BKG_COLOR
        vertex_label[bkg_vertex] = 'Bkg'

        gt.graph_draw(g, vertex_text=vertex_label, pos=position, vertex_font_size=18, edge_pen_width=penalty,
                      vertex_fill_color=vertex_color, edge_color=edge_color,
                      output_size=(800, 800), output="graph.png")

if __name__ == '__main__':
    img = SegmentedImage('mini-test.jpg')

    sorted_pixels = sorted(img.pixel_values.keys(), key=lambda p : img.pixel_values[p])
    dummy_obj_seeds = sorted_pixels[:10]
    dummy_bkg_seeds = sorted_pixels[-10:]

    img.calculate_costs(dummy_obj_seeds, dummy_bkg_seeds)
    img.create_graph()
