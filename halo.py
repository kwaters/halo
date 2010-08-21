#!/usr/bin/env python

import math

class OutsideTriangleError(Exception):
    pass

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
        """Is the vertex v contained in this triangle?"""
        return all(A * v.x + B * v.y + C <= 0 for (A, B, C) in self.coefs)

    def incircle(self, d, limit=0):
        """Is the Vertex d in the circle defined by this triangle?
        
        | a.x a.y (a.x^2 + a.y^2) 1 |
        | b.x b.y (b.x^2 + b.y^2) 1 | > 0
        | c.x c.y (c.x^2 + c.y^2) 1 |
        | d.x d.y (d.x^2 + d.y^2) 1 |

        If the about holds the point d is in the incircle of the triangle abc.
        Reduce the determinate to a 3x3 by row operations on the final column.
        
        """
        a = self.face.edge.origin
        b = self.face.edge.next.origin
        c = self.face.edge.next.next.origin

        norm_a = a.x * a.x + a.y * a.y
        norm_b = b.x * b.x + b.y * b.y
        norm_c = c.x * c.x + c.y * c.y
        norm_d = d.x * d.x + d.y * d.y

        A = a.x - d.x
        B = a.y - d.y
        C = norm_a - norm_d
        D = b.x - d.x
        E = b.y - d.y
        F = norm_b - norm_d
        G = c.x - d.x
        H = c.y - d.y
        I = norm_c - norm_d

        det = A * (E * I - F * H) - D * (B * I - C * H) + G * (B * F - C * E)
        return det > limit

    def circumcenter(self):
        """The circumcenter of this triangle as a tuple (x, y)."""
    
        A1, B1, C1 = self.face.edge.perpendicular()
        A2, B2, C2 = self.face.edge.next.perpendicular()
        # N.B.: If the triangle is not degenerate this cannot cause division
        # by 0.
        x = (B2 * C1 - B1 * C2) / (A2 * B1 - A1 * B2)
        # TODO: if B1 is "small" use the second set of coordinates
        if B1:
            y = (-A1 * x - C1) / B1
        else:
            y = (-A2 * x - C2) / B2
        return x, y

    def circle(self):
        """The circle defined by this triangle as a tuple (x, y, r).
        
        The circle centered at (x, r) of radius r passes through all three
        vertices that define this triangle.

        """
        x, y = self.circumcenter()
        v = self.face.edge.origin
        r = (v.x - x) * (v.x - x) + (v.y - y) * (v.y - y)
        return x, y, math.sqrt(r)


    def child(self, v):
        """The child of this triangle which contains the vertex v.

        Vertex v must be contained in this triangle.

        """
        for child in self.children:
            if child.inside(v):
                return child
        raise OutsideTriangleError()

    def find_leaf(self, v):
        """Returns the leaf triangle containing vertex v"""
        triangle = self
        while triangle.children:
            triangle = triangle.child(v)
        return triangle

    def __repr__(self):
        return 'Triangle({0}, {1}, {2})'.format(self.face.edge.origin,
            self.face.edge.next.origin, self.face.edge.next.next.origin)

    def deep_split(self, v):
        leaf = self.find_leaf(v)
        leaf.split(v)
        return leaf

    def split(self, v):
        """Split this triangle into 3 triangles.

        Vertex v must be inside this triangle.

        """
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

    def far_edge(self, v):
        """Return the edge opposite vertex v.

        Vertex v must be one of the vertices comprising this triangle.

        """
        assert (v is self.face.edge.origin or
            v is self.face.edge.next.origin or
            v is self.face.edge.next.next.origin)

        edge = self.face.edge
        while edge.origin is not v:
            edge = edge.next
        edge = edge.next
        return edge

    def flip(self, v):
        """Flip the diagonal formed by this and the triangle opposite v.

         Vertex v must be part of this triangle.  The two new triangles are
         inserted as children of both original triangles.

        """
        # The edge opposite v.
        edge = self.far_edge(v)
        # The triangle opposite v.
        neighbor = edge.twin.face.data
        # The vertex across from edge.
        target = edge.twin.next.next.origin

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
        """Return twice the signed area of this triangle."""
        a = self.face.edge.origin
        b = self.face.edge.next.origin
        c = self.face.edge.next.next.origin

        v0x = b.x - a.x
        v0y = b.y - a.y
        v1x = c.x - b.x
        v1y = c.y - b.y

        return v0x * v1y - v0y * v1x

def make_edge_pair(v0, v1):
    """Make an edge from v0 to v1."""

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
    """ Make a triangle with vertices v0, v1, and v2.

    Vertices v0 v1 and v2 must be in counter-clockwise order.

    """
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

