#!/usr/bin/env python

import math
import sys
import random

from OpenGL.GL import *
from OpenGL.GLUT import *

import voronoi

vertex_shader_source = """
varying vec2 distance;
void main() {
    distance = gl_Vertex.xy - gl_MultiTexCoord0.st;
    gl_Position = gl_Vertex;
}
"""

fragment_shader_source = """
uniform float offset;
varying vec2 distance;
void main() {
    float c = length(distance);

    c = 10. * c;
    c = c - offset;
    c = smoothstep(.45, .55, abs(fract(c) * 2. - 1.));
    // c = abs(frac(c) * 2. - 1.);

    gl_FragColor = vec4(c, c, c, 1.);
}
"""

program = 0
def init():
    global program
    program = glCreateProgram()
    vertex = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex, vertex_shader_source)
    glCompileShader(vertex)
    glAttachShader(program, vertex)
    print 'vertex log:', glGetShaderInfoLog(vertex)
    fragment = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment, fragment_shader_source)
    glCompileShader(fragment)
    glAttachShader(program, fragment)
    print 'fragment log:', glGetShaderInfoLog(fragment)
    glLinkProgram(program)
    # print 'program log:', glGetShaderInfoLog(program)
    

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

    if False:
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
            

    if False:
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


    if False:
        glBegin(GL_LINES)
        for edge in edges:
            glColor(0, 0, 0)
            if not edge.origin.artificial and not edge.twin.origin.artificial:
                glVertex(edge.origin.x, edge.origin.y)
                glVertex(edge.twin.origin.x, edge.twin.origin.y)
        glEnd()

seed = 74
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
    # print 'seed =', seed
    # seed += 1

    points = [voronoi.Vertex(r.uniform(-1., 1.), r.uniform(-1., 1.))
        for i in xrange(25)]

    t = voronoi.triangulate(points, max_coord=1)
    
    triangles(points)

    draw_dcel(t.get_face())

    glutSwapBuffers()
    # glutPostRedisplay()

which = 0
def triangles(points):
    
    color = .3

    import time
    now = time.time()
    offset = 1 * (now - int(now))
    glutPostRedisplay()

    glUseProgram(program)
    glUniform1f(glGetUniformLocation(program, "offset"), offset)

    # for vertex in points[which:which + 1]:
    for vertex in points:
        glTexCoord(vertex.x, vertex.y)
        glBegin(GL_TRIANGLE_FAN)
        glColor(color, color, color)
        color += .7 / (len(points) - 1)
        glVertex(vertex.x, vertex.y)
        edge = vertex.edge
        while True:
            # assert edge.origin is vertex
            glVertex(*edge.face.data.circumcenter())
            edge = edge.twin.next
            if edge is vertex.edge:
                break
        glVertex(*edge.face.data.circumcenter())
        glEnd()
    glUseProgram(0)

def resize(width, height):
    glViewport(0, 0, width, height)

def keyboard(key, x, y):
    if key == '\033':
        sys.exit()
    elif True:
        global seed
        seed += 1
        glutPostRedisplay()
    else:
        global which
        which += 1
        if which >= 20:
            which = 0
        glutPostRedisplay()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DEPTH | GLUT_DOUBLE)
    glutInitWindowSize(768, 768)
    window = glutCreateWindow("triangle")
    glutDisplayFunc(paint)
    glutKeyboardFunc(keyboard)
    init()
    glutMainLoop()


if __name__ == '__main__':
    main()

