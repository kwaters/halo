
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

var Animator = function(tricks) {
    this.tricks = tricks
    this.runningTrick = null;
}
Animator.prototype = {
    run: function(now) {
        if (this.runningTrick !== null) {
            this.runningTrick.run(now);
        }
    },
    startTrick: function(now, trickName) {
        this.runningTrick = this.tricks[trickName];
        this.runningTrick.start(now);
    }
}

var Trick = function(actions) {
    this.actions = actions;
    this.animations = [];
    this.startTime = 0;
}
Trick.prototype = {
    start: function(now) {
        this.startTime = now;
        this.animations = [];
        this.actions(this);
    },
    run: function(now) {
        var done = true,
            time = now - this.startTime;

        for (var i = 0, l = this.animations.length; i < l; i++) {
            done = this.animations[i].run(time) && done;
        }
        if (done)
            this.animations = [];
        return done;
    },
    animate: function(obj, property, value, start, stop) {
        var animation = new Animation(obj, property, value, start, stop);
        this.animations.push(animation);
    }
}

var Animation = function(obj, property, value, start, stop) {
    this.obj = obj;
    this.property = property;
    this.right = value;
    this.start = start;
    this.stop = stop;
    this.state = 0;
}
Animation.prototype = {
    run: function(now) {
        if (this.state == 0 && now >= this.start) {
            this.state = 1;
            this.left = this.obj[this.property];
        }
        if (this.state == 1) {
            var alpha = (now - this.start) / (this.stop - this.start);
            if (alpha < 0.) {
                alpha = 0;
            } else if (alpha > 1.) {
                alpha = 1;
                this.state = 2;
            }
            this.obj[this.property] = alpha * (this.right - this.left) +
                this.left;
        }
        if (this.obj[this.property] === undefined) {
            console.log(this);
        }
        return this.state == 2;
    }
}

window.Trick = Trick;
window.Animator = Animator;

})();

(function() {

var timeLog = new TimeLog();

var viewMatrix = new Float32Array(4),
    pixelSize;

var resize = function() {
    var canvas = document.getElementById("c");
        width = canvas.clientWidth,
        height = canvas.clientHeight,
        ratio = width / height;
    canvas.width = width;
    canvas.height = height;

    gl.viewport(0, 0, width, height);

    viewMatrix[1] = viewMatrix[2] = 0.;
    if (ratio > 1.) {
        viewMatrix[0] = 1.;
        viewMatrix[3] = ratio;
        pixelSize = 2. / width;
    } else {
        viewMatrix[0] = 1. / ratio;
        viewMatrix[3] = 1.;
        pixelSize = 2. / height;
    }

    // Anti-aliasing adjustment factor
    pixelSize *= .7;

    // redraw
    setTimeout(draw, 0);
}

var tick = new Date().getTime();

var draw = function() {
    if (timeLog.running()) {
        timeLog.mark('browser');
        if (timeLog.samples() >= 200) {
            // timeLog.log();
            timeLog.reset();
            // clearInterval(interval);
        }
    }

    timeLog.start();

    if (trick.run(new Date().getTime()))
        trick.start(new Date().getTime());

    timeLog.mark('animation');

    var verts = [];
    for (var i = 0; i < points.length; i += 2)
        verts.push(new Vertex(points[i], points[i + 1]));
    var tri = triangulate(verts, 1.2);

    timeLog.mark('triangulation');

    // TODO: These sizes are a bit conservative.
    // One vertex per edge
    // At most one triangle per edge
    var data = new Float32Array(6 * 4 * verts.length),
        idx = new Uint16Array(3 * 6 * verts.length),
        di = 0,
        ii = 0;

    for (var i = 0, l = verts.length; i < l; ++i) {
        var point = verts[i],
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

    timeLog.mark('texture');

    var invWidth = 30.;

    shader.bind();
    shader.position(2, gl.FLOAT, false, 16, 0);
    shader.control_point(2, gl.FLOAT, false, 16, 8);
    shader.view_transform(viewMatrix);
    shader.inv_width(invWidth);
    shader.offset(0.1);
    shader.blur(invWidth * pixelSize);
    shader.tex(0);
    shader.inv_texture_size(1 / 32.);

    gl.drawElements(gl.TRIANGLES, ii, gl.UNSIGNED_SHORT, 0);

    timeLog.mark('draw');
}

var mod = function(x, y) {
    return x - Math.floor( x / y) * y;
}

var hsvToRgb = function(hue, saturation, value) {
    // hue from 0. to 1. instead of the traditional 0 to 360

    hue = mod(hue, 1.);
    var c = value * saturation,
        x = c * (1 - Math.abs(mod(hue * 6., 2.) - 1.)),
        m = value - c,
        rgb;

    switch ((hue * 6.) | 0) {
    case 0: rgb = [c, x, 0]; break;
    case 1: rgb = [x, c, 0]; break;
    case 2: rgb = [0, c, x]; break;
    case 3: rgb = [0, x, c]; break;
    case 4: rgb = [x, 0, c]; break;
    case 5: rgb = [c, 0, x]; break;
    }

    rgb[0] = (255. * (rgb[0] + m) + 0.5) | 0;
    rgb[1] = (255. * (rgb[1] + m) + 0.5) | 0;
    rgb[2] = (255. * (rgb[2] + m) + 0.5) | 0;

    return rgb
}
window.hsvToRgb = hsvToRgb;

var points = [],
    shader,
    texture,
    interval;

var makeColorRamp = function(h1, s1, v1, h2, s2, v2, size, count, limit,
    reflect) {
    var ramp = new Uint8Array(4 * size),
        hDiff = h2 - h1,
        sDiff = s2 - s1,
        vDiff = v2 - v1,
        pos = 0,
        posDir = 1,
        alpha,
        rgb,
        i;

    for (i = 0; i < limit; i++) {
        alpha = pos / (count - 1);

        rgb = hsvToRgb(h1 + alpha * hDiff, s1 + alpha * sDiff,
            v1 + alpha * vDiff);
        ramp[4 * i + 0] = rgb[0];
        ramp[4 * i + 1] = rgb[1];
        ramp[4 * i + 2] = rgb[2];
        ramp[4 * i + 3] = 255;

        pos += posDir;
        if (pos < 0 || pos >= count) {
            if (reflect) {
                posDir = -posDir;
                pos += 2 * posDir;
            } else {
                pos = 0;
            }
        }
    }
    for (; i < size; i++) {
        ramp[4 * i + 0] = ramp[4 * (limit - 1) + 0];
        ramp[4 * i + 1] = ramp[4 * (limit - 1) + 1];
        ramp[4 * i + 2] = ramp[4 * (limit - 1) + 2];
        ramp[4 * i + 3] = 255;
    }

    return ramp;
}

var Texture = function(gl, size) {
    this.gl = gl;
    this.size = size;
    this.textureId = this.gl.createTexture();
    this.target = null;
    this.last = null;

    this.bind();
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);

    this.make(4, this.size);
    this.make(4, this.size);
    this.upload(1.);
}
Texture.prototype = {
    bind: function() {
        this.gl.bindTexture(this.gl.TEXTURE_2D, this.textureId);
    },
    make: function(count, limit) {
        var h1, s1, v1, h2, s2, v2;
        do {
            h1 = 2 * Math.random();
            s1 = Math.random();
            v1 = Math.random();
            h2 = 2 * Math.random();
            s2 = Math.random();
            v2 = Math.random();
        } while (s1 + s2 < .4 && v1 + v2 < .6);

        this.set([h1, s1, v1, h2, s2, v2]);
    },
    set: function(ramp) {
        this.last = this.target;
        this.target = ramp;
    },
    upload: function(alpha) {
        var invAlpha = 1. - alpha,
            i, l, data, v = [];

        for (i = 0; i < 6; i++)
            v.push(invAlpha * this.last[i] + alpha * this.target[i]);

        data = makeColorRamp(v[0], v[1], v[2], v[3], v[4], v[5],
            this.size, 4, this.size, true);

        // this.bind();
        this.gl.texImage2D(this.gl.TEXTURE_2D, 0, this.gl.RGBA, this.size, 1,
            0, this.gl.RGBA, this.gl.UNSIGNED_BYTE, data);
    }
}

var trick;

var initAnimations = function() {
}

var main = function() {
    gl = $("#c")[0].getContext('webgl');
    if (!gl)
      gl = $("#c")[0].getContext('experimental-webgl');
    $(window).resize(resize);
    resize();

    shader = new Shader("halo_vertex", "halo_fragment");
    console.log('main', gl);

    texture = new Texture(gl, 32);
    gl.activeTexture(gl.TEXTURE0);
    texture.bind();
    console.log(texture);

    points = []
    for (var i = 0; i < 20; ++i) {
        // x, y
        points.push(2 * Math.random() - 1);
        points.push(2 * Math.random() - 1);
    }

    /*
    trick = new Trick(function(trick) {
        trick.animate(points, 0, -.8,    0, 3000);
        trick.animate(points, 1, -.8,    0, 3000);
        trick.animate(points, 0,  .8, 3000, 6000);
        trick.animate(points, 0,  0., 6000, 9000);
        trick.animate(points, 1,  .8, 6000, 9000);
    });
    trick.start(new Date().getTime());
    */

    var movePoints = new Trick(function(trick) {
        for (var i = 0, l = points.length; i < l; i++) {
            var cuts = [];
            for (var j = 0; j < 6; j++) {
                cuts.push(10000. * Math.random());
            }
            cuts.sort(function(a, b) { return a - b; });

            var max = .1 + 1. / viewMatrix[3 * (i & 1)],
                min = -max;

            var cv = points[i];
            for (var j = 1, m = cuts.length; j < m; j++) {
                var length = Math.min(1., (cuts[j] - cuts[j - 1]) / 4000.),
                    v = cv + length * (2 * Math.random() - 1);
                v = Math.min(max, Math.max(min, v));
                cv = v;

                trick.animate(points, i, v, cuts[j - 1], cuts[j]);
            }
        }
    });
    trick = movePoints;

    timeLog.reset();
    interval = setInterval(draw, 0);
}


$(document).ready(main);

})();

