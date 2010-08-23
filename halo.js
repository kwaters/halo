

var twod;

(function() {

var resize = function(twod) {
    twod.setTransform(1., 0., 0., 1., 0., 0.);
    twod.scale(256., -256.)
    twod.translate(1., -1.);
}

var main = function() {
    twod = $("#c")[0].getContext('2d');
    resize(twod);

    twod.fillStyle = "rgb(37, 174, 158)";
    twod.fillRect(-1., -1., 2., 2.);

    var points = [
        new Vertex(-.5, .5),
        new Vertex(.5, .5),
        new Vertex(-.5, -.5),
        new Vertex(.2, -.3)
        ];

    for (var i = 0; i < 20; ++i) {
        points.push(new Vertex(2 * Math.random() - 1, 2 * Math.random() - 1));
    }

    var tri = triangulate(points, 1);

    twod.lineCap = "round";
    twod.lineWidth = .05;
    twod.beginPath();
    for (var i = 0, l = points.length; i < l; ++i) {
        var point = points[i];
        twod.moveTo(point.x, point.y);
        // WAR, Chrome doesn't correctly handle 0 length lines. Boo.
        twod.lineTo(point.x + 0.005, point.y);
    }
    twod.stroke();

    twod.lineCap = "butt";
    twod.lineWidth = 0.015;

    twod.strokeStyle = "red";
    twod.beginPath();
    for (var i = 0, l = points.length; i < l; ++i) {
        var vertex = points[i],
            final_edge = vertex.edge,
            edge = final_edge,
            center = edge.face.data.circumcenter();
        twod.moveTo(center[0], center[1]);
        edge = edge.twin.next;
        while (edge !== final_edge) {
            var center = edge.face.data.circumcenter();
            twod.lineTo(center[0], center[1]);
            edge = edge.twin.next;
        }
        twod.closePath();
        var center = edge.face.data.circumcenter();
        twod.lineTo(center[0], center[1]);
    }
    twod.stroke();

}


$(document).ready(main);

})();

