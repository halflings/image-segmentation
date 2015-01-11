from collections import Counter
from math import exp, pi, sqrt
import scipy
import scipy.stats
from PIL import Image

def norm_pdf(x, mu, sigma):
    return (1/(sqrt(2*pi)*abs(sigma)))*exp(-x**2/2)

def dist(p_a, p_b):
    return sqrt((p_a[0] - p_b[0]) ** 2 + (p_a[1] - p_b[1]) ** 2)

class SegmentedImage(object):
    def __init__(self, image_path):
        self.img = Image.open(image_path)
        self.w, self.h = self.img.size

        # Dummy values
        self.lambda_factor = 2.
        self.k_factor = 3.
        self.sigma_factor = 30.

    def print_pixels(self):
        for x in xrange(self.w):
            for y in xrange(self.h):
                val = self.img.getpixel((x, y))[0]
                print val,
            print

    def pixels(self):
        for x in xrange(self.w):
            for y in xrange(self.h):
                yield (x, y)

    def pixel_value(self, point):
        return self.img.getpixel(point)[0]

    def neighbours(self, x, y):
        return ((i, j) for i in xrange(x-1, x+2) for j in xrange(y-1, y+2)
                 if 0 <= i < self.w and 0 <= j < self.h and (i != x or j != y))

    def calculate_histogram(self, points):
        values_count = Counter(self.pixel_value(p) for p in points)
        return {value : float(count) / len(points) for value, count in values_count.iteritems()}

    def calculate_normal(self, points):
        values = [self.pixel_value(p) for p in points]
        return scipy.mean(values), scipy.std(values)

    def regional_cost(self, point, mean, std):
        return norm_pdf(self.pixel_value(point), mean, std)

    def boundary_penalty(self, p_a, p_b):
        i_delta = self.pixel_value(p_a) - self.pixel_value(p_a)
        return exp(- i_delta**2 / (2 * self.sigma_factor**2)) / dist(p_a, p_b)

    def calculate_costs(self, obj_seeds, bkg_seeds):
        obj_mean, obj_std = self.calculate_normal(obj_seeds)
        bkg_mean, bkg_std = self.calculate_normal(bkg_seeds)

        regional_penalty_obj = {p: 0 if p in obj_seeds else self.k_factor if p in bkg_seeds else self.regional_cost(p, obj_mean, obj_std)
                                   for p in self.pixels()}
        regional_penalty_bkg = {p: self.k_factor if p in obj_seeds else 0 if p in bkg_seeds else self.regional_cost(p, bkg_mean, bkg_std)
                                   for p in self.pixels()}


if __name__ == '__main__':
    img = SegmentedImage('cat-bw.jpg')

    dummy_obj_seeds = {(50 + i, 50 + j) for i in xrange(5) for j in xrange(5)}
    dummy_bkg_seeds = {(110 + i, 110 + j) for i in xrange(5) for j in xrange(5)}
    img.calculate_costs(dummy_obj_seeds, dummy_bkg_seeds)
