
var gl = null;

(function() {

// static "class members" for vertex array and shader tracking.
var boundShader = null,
    enabledArrays = 0,
    shaderTypes = {
        'float': [1, 'f'],
        'vec2': [2, 'f'],
        'vec3': [3, 'f'],
        'vec4': [4, 'f'],
        'int': [1, 'i'],
        'ivec2': [2, 'i'],
        'ivec3': [3, 'i'],
        'ivec4': [4, 'i'],
        'mat2': [2, 'm'],
        'mat3': [3, 'm'],
        'mat4': [4, 'm'],
        'sampler2D': [1, 'i']
    };

var Shader = function(vertexId, fragmentId) {
    var vertexSource = document.getElementById(vertexId).text,
        fragmentSource = document.getElementById(fragmentId).text,
        re = /(uniform|attribute)\s+\S+\s+(\S+)\s+(\S+)\s*;/g,
        match = null,
        loadShaderSucceeded = false;

    this._arrays = 0;
    this._program = gl.createProgram();

    try {
        this.loadShader(gl.VERTEX_SHADER, vertexId);
        this.loadShader(gl.FRAGMENT_SHADER, fragmentId);
        loadShaderSucceeded = true;
    } finally {
        // Javascript doesn't have a real rethrow, do this terrible flag based
        // hack.
        if (!loadShaderSucceeded)
            gl.deleteProgram(this._program);
    }

    gl.linkProgram(this._program);
    if (!gl.getProgramParameter(this._program, gl.LINK_STATUS)) {
        console.log("prgoramInfoLog:", gl.getProgramInfoLog(this._program));
        gl.deleteProgram(this._program);
        throw "Program " + vertexId + ", " + fragmentId + " didn't link."
    }

    while ((match = re.exec(vertexSource + '\n' + fragmentSource)) !== null) {
        var name = match[3],
            type = match[2],
            qualifier = match[1];
        if (qualifier == 'uniform')
            this.makeUniformFunction(name, type);
        else
            this.makeAttributeFunction(name);
    }
}
Shader.prototype = {
    loadShader: function(type, shaderId) {
        var shaderSource = document.getElementById(shaderId).text,
            shader = gl.createShader(type);

        gl.shaderSource(shader, shaderSource);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.log(gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            throw "Shader " + shaderId + " didn't compile.";
        }

        gl.attachShader(this._program, shader);
        gl.deleteShader(shader);
    },
    makeAttributeFunction: function(name) {
        var loc = gl.getAttribLocation(this._program, name);
        if (loc >= 0) {
            this._arrays |= 1 << loc;
            this[name] = function(size, type, normalized, stride,
                    ofs) {
                this.bind();
                gl.vertexAttribPointer(loc, size, type, normalized, stride, ofs);
            }
        } else {
            this[name] = function() {};
        }
    },
    makeUniformFunction: function(name, typeName) {
        var size = shaderTypes[typeName][0],
            type = shaderTypes[typeName][1],
            loc = gl.getUniformLocation(this._program, name);
        switch (type) {
        case 'i':
        case 'f':
            this[name] = function() {
                // TODO: It feels wrong to have to copy arguments to prepend to
                // it
                this.bind();
                var args = [loc], i;
                for (i = 0; i < arguments.length; i++)
                    args.push(arguments[i]);
                gl['uniform' + size + type].apply(gl, args);
            };
            break;

        case 'm':
            this[name] = function(matrix) {
                this.bind();
                gl['uniformMatrix' + size + 'fv'](loc, gl.FALSE, matrix);
            }
            break;
        }
    },
    bind: function() {
        if (boundShader === this)
            return;

        boundShader = this;
        gl.useProgram(this._program);

        // Enable the correct vertex arrays
        var diff = enabledArrays ^ this._arrays,
            enable = diff & this._arrays,
            disable = diff & enabledArrays,
            i;

        for (i = 0; enable; i++, enable >>= 1)
            if (enable & 1)
                gl.enableVertexAttribArray(i);
        for (i = 0; disable; i++, disable >>= 1)
            if (disable & 1)
                gl.disableVertexAttribArray(i);
        enabledArrays = this._arrays;
    },
    free: function() {
        gl.deleteProgram(this._program);
    }
}

window.Shader = Shader;

})();

(function(window) {

var TimeLog = function() {
    this.events = []
    this.times = {}
    this.reset();
}
TimeLog.prototype = {
    mark: function(name) {
        if (this.times[name] === undefined) {
            this.events.push(name);
            this.times[name] = [];
        }
        this.times[name].push(new Date().getTime());
    },
    reset: function() {
        this.events = [];
        this.times = {};
    },
    start: function() {
        this.mark('_start');
    },
    running: function() {
        return this.events.length > 0;
    },
    log: function() {
        console.log('Time log');
        for (var i = 1; i < this.events.length; i++) {
            var last_times = this.times[this.events[i - 1]],
                current_times = this.times[this.events[i]];
            var average = 0.;
            for (var j = 0, l = last_times.length; j < l; j++) {
                average += current_times[j] - last_times[j];
            }
            average /= last_times.length;
            console.log(this.events[i], average, 'ms');
        }
    },
    samples: function() {
        return this.times['_start'].length;
    }
}

window.TimeLog = TimeLog;

})(window);

(function() {

var timeLog = new TimeLog();

var resize = function() {
}

var draw = function() {
    timeLog.start();

    var tri = triangulate(points, 1);

    timeLog.mark('triangulation');

    // TODO: These sizes are a bit conservative.
    // One vertex per edge
    // At most one triangle per edge
    var data = new Float32Array(6 * 4 * points.length),
        idx = new Uint16Array(3 * 6 * points.length),
        di = 0,
        ii = 0;

    for (var i = 0, l = points.length; i < l; ++i) {
        var point = points[i],
            anchor = di,
            count = 0,
            edge = point.edge,
            center;
        do {
            count += 1;
            center = edge.face.data.circumcenter();
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

    timeLog.mark('vbo creation');

    var vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STREAM_DRAW);

    var ibo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STREAM_DRAW);

    shader.bind();
    shader.position(2, gl.FLOAT, false, 16, 0);
    shader.control_point(2, gl.FLOAT, false, 16, 8);
    shader.view_transform([1, 0, 0, 1]);
    shader.inv_width(20.);
    shader.offset(0.1);
    shader.blur(0.1);
    shader.tex(0);
    shader.inv_texture_size(.25);

    gl.drawElements(gl.TRIANGLES, ii, gl.UNSIGNED_SHORT, 0);

    timeLog.mark('draw');

    setTimeout(function() {
        if (timeLog.running()) {
            // timeLog.mark('browser');
            if (timeLog.samples() >= 20) {
                timeLog.log();
                timeLog.reset();
                clearInterval(interval);
            }
        }
    });
}

var points = [],
    shader,
    interval;

var main = function() {
    gl = $("#c")[0].getContext('webgl');
    if (!gl)
      gl = $("#c")[0].getContext('experimental-webgl');

    shader = new Shader("halo_vertex", "halo_fragment");

    var texture = gl.createTexture(),
        textureData = new Uint8Array(4 * 4);

    textureData[0] = 255;
    textureData[1] = 0;
    textureData[2] = 0;
    textureData[3] = 255;
    textureData[4] = 0;
    textureData[5] = 255;
    textureData[6] = 0;
    textureData[7] = 255;
    textureData[8] = 0;
    textureData[9] = 0;
    textureData[10] = 255;
    textureData[11] = 255;
    textureData[12] = 0;
    textureData[13] = 0;
    textureData[14] = 0;
    textureData[15] = 255;

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 4, 1, 0, gl.RGBA,
        gl.UNSIGNED_BYTE, textureData);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_WRAP_S, gl.REPEAT);

    for (var i = 0; i < 20; ++i) {
        points.push(new Vertex(2 * Math.random() - 1, 2 * Math.random() - 1));
    }

    timeLog.reset();
    interval = setInterval(draw, 0);
}


$(document).ready(main);

})();

