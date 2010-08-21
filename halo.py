#!/usr/bin/env python

class Vertex(object):
    __slots__ = ['x', 'y', 'edge']
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edge = None

    def __str__(self):
        return '(%f, %f)' % (self.x, self.y)

class HalfEdge(object):
    __slots__ = ['origin', 'twin', 'next', 'face', 'flag']
    def __init__(self):
        self.next = None
        self.face = None

    def sign(self, v):
        A, B, C = self.coefs()
        C = -(A * self.origin.x + B * self.origin.y)
        return A * v.x + B * v.y + C

    def coefs(self):
        A = self.twin.origin.y - self.origin.y
        B = self.origin.x - self.twin.origin.x
        C = -(A * self.origin.x + B * self.origin.y)
        return (A, B, C)

    def perpendicular(self):
        origin = self.origin
        target = self.twin.origin
        midx = (origin.x + target.x) / 2
        midy = (origin.y + target.y) / 2

        A = origin.x - target.x
        B = origin.y - target.y
        C = -(A * midx + B * midy)
        return (A, B, C)
        

    def __str__(self):
        return '%s -> %s' % (self.origin, self.twin.origin)

class Face(object):
    __slots__ = ['edge', 'data']
    def __init__(self, edge, data=None):
        self.edge = edge
        self.data = data

class Triangle(object):
    def __init__(self, face):
        self.face = face
        self.face.data = self
        self.children = []

        self.coefs = []
        e = self.face.edge
        for i in xrange(3):
            self.coefs.append(e.coefs())
            e = e.next

    def inside(self, v):
        return all(A * v.x + B * v.y + C <= 0 for (A, B, C) in self.coefs)

    def incircle(self, d, limit=0):
        # print 'incircle({0}, {1})'.format(self, d)
        a = self.face.edge.origin
        b = self.face.edge.next.origin
        c = self.face.edge.next.next.origin

        norm_a = a.x * a.x + a.y * a.y
        norm_b = b.x * b.x + b.y * b.y
        norm_c = c.x * c.x + c.y * c.y
        norm_d = d.x * d.x + d.y * d.y

        ab = a.y * norm_b - b.y * norm_a
        ac = a.y * norm_c - c.y * norm_a
        ad = a.y * norm_d - d.y * norm_a
        bc = b.y * norm_c - c.y * norm_b
        bd = b.y * norm_d - d.y * norm_b
        cd = c.y * norm_d - d.y * norm_c

        det_a = b.x * cd - c.x * bd + d.x * bc
        det_b = a.x * cd - c.x * ad + d.x * ac
        det_c = a.x * bd - b.x * ad + d.x * ab
        det_d = a.x * bc - b.x * ac + c.x * ab
        det = -det_a + det_b - det_c + det_d

        # print ab, ac, ad, bc, bd, cd
        # print det_a, det_b, det_c, det_d
        # print det

        return det > limit

    def circumcenter(self):
        A1, B1, C1 = self.face.edge.perpendicular()
        A2, B2, C2 = self.face.edge.next.perpendicular()
        x = (B2 * C1 - B1 * C2) / (A2 * B1 - A1 * B2)
        if B1:
            y = (-A1 * x - C1) / B1
        else:
            y = (-A2 * x - C2) / B2
        error = x * A2 + y * B2 + C2
        assert error < 1e-10 and error > -1e-10
        
        pt = self.face.edge.origin
        import math
        r = (pt.x - x) * (pt.x - x) + (pt.y - y) * (pt.y - y)
        r = math.sqrt(r)

        return x, y, r

    def child(self, v):
        # assert self.inside(v)
        for child in self.children:
            if child.inside(v):
                return child
        assert False
        return None

    def find_leaf(self, v):
        triangle = self
        while triangle.children:
            triangle = triangle.child(v)
        return triangle

    def __str__(self):
        return 'Triangle({0}, {1}, {2})'.format(self.face.edge.origin,
            self.face.edge.next.origin, self.face.edge.next.next.origin)

    def deep_split(self, v):
        leaf = self.find_leaf(v)
        leaf.split(v)
        return leaf

    def split(self, v):
        side0 = self.face.edge
        side1 = side0.next
        side2 = side1.next

        e0 = make_edge_pair(v, side0.origin)
        e1 = make_edge_pair(v, side1.origin)
        e2 = make_edge_pair(v, side2.origin)

        e0.next = side0
        e1.next = side1
        e2.next = side2

        e0.twin.next = e2
        e1.twin.next = e0
        e2.twin.next = e1

        side0.next = e1.twin
        side1.next = e2.twin
        side2.next = e0.twin

        side0.face = Face(side0)
        side1.face = Face(side1)
        side2.face = Face(side2)
        e0.face = side0.face
        e1.twin.face = side0.face
        e1.face = side1.face
        e2.twin.face = side1.face
        e2.face = side2.face
        e0.twin.face = side2.face

        self.face = None
        self.children = [Triangle(side0.face), Triangle(side1.face), Triangle(side2.face)]

        # print [child.incircle(v) for child in self.children]

    def far_edge(self, v):
        assert (v is self.face.edge.origin or
            v is self.face.edge.next.origin or
            v is self.face.edge.next.next.origin)

        edge = self.face.edge
        while edge.origin is not v:
            edge = edge.next
        edge = edge.next
        return edge

    def flip(self, v):
        edge = self.far_edge(v)
        neighbor = edge.twin.face.data
        
        # print 'flip({0}, {1})'.format(self, v)
        # print 'neighbor = {0}'.format(neighbor)

        target = edge.twin.next.next.origin
        # print 'target = {0}'.format(target)

        # Name edges that make up the quadrilateral
        v_cw = edge.next
        v_ccw = v_cw.next
        t_cw = edge.twin.next
        t_ccw = t_cw.next

        # flip edge
        edge.origin = v
        edge.twin.origin = target

        # edges for the new triangles
        v_cw.next = edge
        v_ccw.next = t_cw
        t_cw.next = edge.twin
        t_ccw.next = v_cw
        edge.next = t_ccw
        edge.twin.next = v_ccw

        # faces for the edges
        t_ccw.face = self.face
        v_ccw.face = neighbor.face

        # edges for the faces
        self.face.edge = edge
        neighbor.face.edge = edge.twin

        # update triangle tree
        children = [Triangle(self.face), Triangle(neighbor.face)]
        self.children = children
        neighbor.children = children
        self.face = None
        neighbor.face = None

    def area(self):
        a = self.face.edge.origin
        b = self.face.edge.next.origin
        c = self.face.edge.next.next.origin

        v0x = b.x - a.x
        v0y = b.y - a.y
        v1x = c.x - b.x
        v1y = c.y - b.y

        return v0x * v1y - v0y * v1x

def make_edge_pair(v0, v1):
    e0 = HalfEdge()
    e1 = HalfEdge()
    e0.twin = e1
    e0.origin = v0
    e0.flag = False
    e1.twin = e0
    e1.origin = v1
    e1.flag = True

    return e0

def make_triangle(v0, v1, v2):
    # assumes v0 v1 v2 are counter clockwise
    e0 = make_edge_pair(v0, v1)
    e1 = make_edge_pair(v1, v2)
    e2 = make_edge_pair(v2, v0)
    e0.next = e1
    e1.next = e2
    e2.next = e0
    f = Face(e0)
    return Triangle(f)

def legalize(triangle, v):
    face = triangle.far_edge(v).twin.face
    if face is not None:
        adjacent = face.data
        if adjacent.incircle(v):
            triangle.flip(v)
            assert len(triangle.children) == 2
            legalize(triangle.children[0], v)
            legalize(triangle.children[1], v)

def check_triangulation(triangle):
    triangles = set()
    def add_tris(tri):
        if not tri.children:
            triangles.add(tri)
        else:
            for child in tri.children:
                add_tris(child)
    add_tris(triangle)

    verts = set()
    for triangle in triangles:
        verts.add(triangle.face.edge.origin)
        verts.add(triangle.face.edge.next.origin)
        verts.add(triangle.face.edge.next.next.origin)

    for triangle in triangles:
        # print triangle.area()
        for vert in verts:
            assert not triangle.incircle(vert, limit=1e-10)

