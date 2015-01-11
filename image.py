from collections import Counter
from math import exp, pi, sqrt

import numpy as np
from PIL import Image

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
        return np.mean(values), np.std(values)

    def regional_cost(self, point, mean, std):
        return self.lambda_factor * norm_pdf(self.pixel_values[point], mean, std)

    def calculate_costs(self, obj_seeds, bkg_seeds):
        obj_mean, obj_std = self.calculate_normal(obj_seeds)
        bkg_mean, bkg_std = self.calculate_normal(bkg_seeds)

        self.regional_penalty_obj = {p: 0 if p in obj_seeds else self.k_factor if p in bkg_seeds else self.regional_cost(p, obj_mean, obj_std)
                                     for p in self.pixels()}
        self.regional_penalty_bkg = {p: self.k_factor if p in obj_seeds else 0 if p in bkg_seeds else self.regional_cost(p, bkg_mean, bkg_std)
                                     for p in self.pixels()}


if __name__ == '__main__':
    img = SegmentedImage('cat-bw.jpg')

    dummy_obj_seeds = {(50 + i, 50 + j) for i in xrange(5) for j in xrange(5)}
    dummy_bkg_seeds = {(110 + i, 110 + j) for i in xrange(5) for j in xrange(5)}
    img.calculate_costs(dummy_obj_seeds, dummy_bkg_seeds)
