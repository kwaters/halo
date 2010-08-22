#!/usr/bin/env python

import random

import voronoi

def test_one(seed):
    r = random.Random(seed)
    print 'seed =', seed

    points = [voronoi.Vertex(r.uniform(-1., 1.), r.uniform(-1., 1.))
        for i in xrange(100)]

    t = voronoi.triangulate(points)
    voronoi.check_triangulation(t)
    voronoi.check_dcel(t)

def main():
    for i in xrange(6000, 8000):
        test_one(i)

if __name__ == '__main__':
    main()


