#!/usr/bin/env python

import math
import sys
import random

from OpenGL.GL import *
from OpenGL.GLUT import *

import halo

def get_face(triangle):
    while triangle.children:
        triangle = triangle.children[0]
    return triangle.face

def dcel_edges(face):
    working = set((face.edge,))
    edges = set(working)

    while working:
        new = set()
        for edge in working:
            if edge.twin not in edges:
                edges.add(edge.twin)
                new.add(edge.twin)
            if edge.next is not None and edge.next not in edges:
                edges.add(edge.next)
                new.add(edge.next)
        working = new

    return edges

def check_dcel(face):
    edges = dcel_edges(face)
    for edge in edges:
        if edge.next is not None:
            if edge.next.next.next is not edge:
                print edge, 'triangle'
                print '  ', edge.next
                print '  ', edge.next.next
                print '  ', edge.next.next.next
        if edge.face is not None:
            if edge.face is not edge.next.face or edge.face is not edge.next.next.face:
                print edge, 'face'
            if not (edge.face.edge is edge or edge.face.edge is edge.next or edge.face.edge is edge.next.next):
                print edge.face.edge, 'face edge'

def draw_circle(x, y, r):
    glBegin(GL_LINE_LOOP)
    for i in xrange(128):
        ang = i * math.pi / 64
        glVertex(r * math.cos(ang) + x, r * math.sin(ang) + y)
    glEnd()

def draw_dcel(face):
    edges = dcel_edges(face)

    if False:
        glColor(0, 0, 1)
        faces = set(edge.face for edge in edges)
        faces.discard(None)
        for face in faces:
            x, y, r = face.data.circumcenter()
            draw_circle(x, y, r)

    if True:
        glColor(0, 0, 1)
        glBegin(GL_LINES)
        for edge in edges:
            lhs = edge.face
            rhs = edge.twin.face
            if lhs is not None and rhs is not None:
                x, y, r = lhs.data.circumcenter()
                glVertex(x, y)
                x, y, r = rhs.data.circumcenter()
                glVertex(x, y)

        glEnd()
            

    glColor(0, 0, 0)
    glBegin(GL_POINTS)
    for edge in edges:
        glVertex(edge.origin.x, edge.origin.y)
    if True:
        glColor(0, 0, 1)
        faces = set(edge.face for edge in edges)
        faces.discard(None)
        for face in faces:
            x, y, r = face.data.circumcenter()
            glVertex(x, y)
    glEnd()


    glBegin(GL_LINES)
    for edge in edges:
        glColor(0, 0, 0)
        glVertex(edge.origin.x, edge.origin.y)
        glVertex(edge.twin.origin.x, edge.twin.origin.y)

        if False:
            v_x = edge.twin.origin.x - edge.origin.x
            v_y = edge.twin.origin.y - edge.origin.y
            perp_x = -v_x - v_y
            perp_y = v_x - v_y
            length = math.sqrt(perp_x * perp_x + perp_y * perp_y) * 10
            perp_x /= length
            perp_y /= length

            if edge.flag:
                glColor(0, 1, 0)
            else:
                glColor(0, 0, 1)
            glVertex(edge.twin.origin.x, edge.twin.origin.y)
            glVertex(edge.twin.origin.x + perp_x, edge.twin.origin.y + perp_y)
    glEnd()

seed = 5
def paint():
    glClearColor(.7, .2, .2, 1.)
    glClear(GL_COLOR_BUFFER_BIT)

    glColor(0, 0, 0, 1)
    glPointSize(10)
    glLineWidth(1.5)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    t = halo.make_triangle(
        halo.Vertex(-.8, -.8),
        halo.Vertex(.8, -.8),
        halo.Vertex(0, .8))
    # t.split(halo.Vertex(-.2, 0))
    # t.child(halo.Vertex(.2, 0)).split(halo.Vertex(.2, 0))

    def round(v):
        leaf = t.deep_split(v)
        for child in leaf.children:
            halo.legalize(child, v)

    # round(halo.Vertex(-.2, 0))
    # round(halo.Vertex(.2, 0))
    # round(halo.Vertex(.2, -.4))

    global seed
    r = random.Random(seed)
    print 'seed =', seed
    # seed += 1
    for i in xrange(28):
        v = halo.Vertex(r.uniform(-1., 1.), r.uniform(-1., 1.))
        if t.inside(v):
            round(v)
    halo.check_triangulation(t)

    dcel = get_face(t)
    check_dcel(dcel)
    draw_dcel(dcel)

    glutSwapBuffers()
    # glutPostRedisplay()

def resize(width, height):
    glViewport(0, 0, width, height)

def keyboard(key, x, y):
    if key == '\033':
        sys.exit()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DEPTH | GLUT_DOUBLE)
    glutInitWindowSize(640, 480)
    window = glutCreateWindow("triangle")
    glutDisplayFunc(paint)
    glutKeyboardFunc(keyboard)
    glutMainLoop()


if __name__ == '__main__':
    main()

