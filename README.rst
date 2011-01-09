======
 Halo
======

**This project has been merged into http://code.google.com/p/webglsamples/**

A WebGL demo inspired by the xscreensaver Halo by Jamie Zawinski.

--------
 Effect
--------

We want to draw concentric circles around a collection of points.  Where the
circles intersect give priority to the circle with smaller radius.

JWZ implemented this by drawing screen width radius circles at every point,
then by drawing one size smaller circles at every point, etc.

Since we prefer to draw the circle of smallest radius.  We need only draw
circles for a point within the Voronoi cell containing that point.  I
originally implemented this 5 years ago by using the cone screen space method
for computing the Voronoi cells described in the Red Book.  The overdraw
severely limited the number of points I could process.

This time I'm going to compute the Voronoi cells directly before rendering.

--------
 Status
--------

This has been finished, and merged into a larger repository.  The python
implementation remains here in case it is useful at a later date.

------
 Plan
------

1. Implement Voronoi cell determination in Python.  I'm more familiar with
   python, and find it a nicer environment to debug in.  I decided to use a
   stochastic iterative technique instead of Fortune's algorithm.  It's
   simpler and as fast on average.  I also don't want to implement the
   balanced binary tree and priority queue required for Fortune's algorithm in
   javascript, because I believe they will be quite slow.

2. Implement the shaders and drawing code in Python.

3. Implement Voronoi cell determination in javascript using Canvas2D.

4. Sprinkle in some WebGL.
