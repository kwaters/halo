
var gl;

(function() {

// var gl;

var resize = function() {
}

var loadProgram = function(vtx_id, frag_id) {
    // Cleanup.
    var program = gl.createProgram();

    var vertex = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertex, document.getElementById(vtx_id).text);
    gl.compileShader(vertex);
    console.log('vertex:\n' + gl.getShaderInfoLog(vertex));
    gl.attachShader(program, vertex);
    var fragment = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragment, document.getElementById(frag_id).text);
    gl.compileShader(fragment);
    console.log('fragment:\n' + gl.getShaderInfoLog(fragment));
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    console.log('program:\n' + gl.getProgramInfoLog(program));

    gl.useProgram(program);

    return program;
}

var main = function() {
    gl = $("#c")[0].getContext('webgl');
    if (!gl)
      gl = $("#c")[0].getContext('experimental-webgl');

    var program = loadProgram("halo_vertex", "halo_fragment");

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

    // TODO: These sizes are a bit conservative.
    // One vertex per edge + one vertex per control point.
    var data = new Float32Array(7 * 4 * points.length);
    var di = 0;
    // At most one triangle per edge
    var idx = new Uint16Array(3 * 6 * points.length);
    var ii = 0;

    for (var i = 0, l = points.length; i < l; ++i) {
        var point = points[i];
        var anchor = di;
        var count = 0;
        var edge = point.edge;
        do {
            count += 1;
            var center = edge.face.data.circumcenter();
            data[4 * di + 0] = center[0];
            data[4 * di + 1] = center[1];
            data[4 * di + 2] = point.x;
            data[4 * di + 3] = point.y;
            ++di;

            edge = edge.twin.next;
        } while (edge !== point.edge);

        for (j = 1; j < count - 1; ++j) {
            idx[ii++] = anchor;
            idx[ii++] = anchor + j;
            idx[ii++] = anchor + j + 1;
        }
    }

    console.log(ii, idx.length);
    console.log(4 * di, data.length);

    var vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STREAM_DRAW);

    var ibo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STREAM_DRAW);

    var position = gl.getAttribLocation(program, 'position');
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 16, 0);
    gl.enableVertexAttribArray(position);
    var control_point = gl.getAttribLocation(program, 'control_point');
    gl.vertexAttribPointer(control_point, 2, gl.FLOAT, false, 16, 8);
    gl.enableVertexAttribArray(control_point);

    gl.drawElements(gl.TRIANGLES, ii, gl.UNSIGNED_SHORT, 0);
}


$(document).ready(main);

})();

