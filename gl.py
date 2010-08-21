#!/usr/bin/env python

import math
import sys
import random

from OpenGL.GL import *
from OpenGL.GLUT import *

import voronoi

def good_face(face):
    bad = False
    edge = face.edge
    while True:
        bad = bad or edge.origin.artificial
        edge = edge.next
        if edge is face.edge:
            break
    return not bad

def draw_circle(x, y, r):
    glBegin(GL_LINE_LOOP)
    for i in xrange(128):
        ang = i * math.pi / 64
        glVertex(r * math.cos(ang) + x, r * math.sin(ang) + y)
    glEnd()

def draw_dcel(face):
    edges = face.edge_set()

    if False:
        glColor(0, 0, 1)
        faces = set(edge.face for edge in edges)
        faces.discard(None)
        for face in faces:
            if good_face(face):
                x, y, r = face.data.circle()
                draw_circle(x, y, r)

    if True:
        glColor(0, 0, 1)
        glBegin(GL_LINES)
        for edge in edges:
            lhs = edge.face
            rhs = edge.twin.face
            if not edge.origin.artificial and not edge.twin.origin.artificial:
            # if lhs is not None and rhs is not None:
                # if lhs.data.area() > 0 and rhs.data.area() > 0:
                    x, y = lhs.data.circumcenter()
                    glVertex(x, y)
                    x, y = rhs.data.circumcenter()
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
            if good_face(face):
                x, y = face.data.circumcenter()
                glVertex(x, y)
    glEnd()


    glBegin(GL_LINES)
    for edge in edges:
        glColor(0, 0, 0)
        if not edge.origin.artificial and not edge.twin.origin.artificial:
            glVertex(edge.origin.x, edge.origin.y)
            glVertex(edge.twin.origin.x, edge.twin.origin.y)

    glEnd()

seed = 72
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

    global seed
    r = random.Random(seed)
    print 'seed =', seed
    # seed += 1

    points = [voronoi.Vertex(r.uniform(-1., 1.), r.uniform(-1., 1.))
        for i in xrange(25)]

    t = voronoi.triangulate(points)
    voronoi.check_triangulation(t)

    dcel = t.get_face()
    try:
        voronoi.check_dcel(t)
    except Exception, e:
        print e
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

