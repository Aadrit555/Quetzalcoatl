/**
 * Quantum Dither WebGL Engine
 * Inspired by ReactBits (https://reactbits.dev/backgrounds/dither)
 * 
 * Features:
 * - Fractional Brownian Motion (FBM) wave noise
 * - 8x8 Bayer matrix spatial dithering filter
 * - Real-time interactive mouse ripple disturbance
 * - High performance single-pass GPU execution
 * - Theme-reactive presets (Cyber Cyan, Deep Violet, Threat Crimson)
 * - Auto-pauses when tab is hidden for zero battery waste
 */

(function (window) {
  'use strict';

  // 8x8 Bayer Matrix threshold values
  const BAYER_8X8 = new Uint8Array([
    0, 48, 12, 60, 3, 51, 15, 63,
    32, 16, 44, 28, 35, 19, 47, 31,
    8, 56, 4, 52, 11, 59, 7, 55,
    40, 24, 36, 20, 43, 27, 39, 23,
    2, 50, 14, 62, 1, 49, 13, 61,
    34, 18, 46, 30, 33, 17, 45, 29,
    10, 58, 6, 54, 9, 57, 5, 53,
    42, 26, 38, 22, 41, 25, 37, 21
  ].map(v => Math.round((v / 64.0) * 255)));

  const VS_SOURCE = `
    attribute vec2 a_position;
    varying vec2 v_uv;
    void main() {
      v_uv = (a_position + 1.0) * 0.5;
      gl_Position = vec4(a_position, 0.0, 1.0);
    }
  `;

  const FS_SOURCE = `
    precision highp float;
    uniform vec2 resolution;
    uniform float time;
    uniform float waveSpeed;
    uniform float waveFrequency;
    uniform float waveAmplitude;
    uniform vec3 waveColor;
    uniform vec3 backgroundColor;
    uniform vec2 mousePos;
    uniform int enableMouseInteraction;
    uniform float mouseRadius;
    uniform float colorNum;
    uniform float pixelSize;
    uniform sampler2D bayerTex;

    vec4 mod289(vec4 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
    vec2 fade(vec2 t) { return t*t*t*(t*(t*6.0-15.0)+10.0); }

    float cnoise(vec2 P) {
      vec4 Pi = floor(P.xyxy) + vec4(0.0,0.0,1.0,1.0);
      vec4 Pf = fract(P.xyxy) - vec4(0.0,0.0,1.0,1.0);
      Pi = mod289(Pi);
      vec4 ix = Pi.xzxz;
      vec4 iy = Pi.yyww;
      vec4 fx = Pf.xzxz;
      vec4 fy = Pf.yyww;
      vec4 i = permute(permute(ix) + iy);
      vec4 gx = fract(i * (1.0/41.0)) * 2.0 - 1.0;
      vec4 gy = abs(gx) - 0.5;
      vec4 tx = floor(gx + 0.5);
      gx = gx - tx;
      vec2 g00 = vec2(gx.x, gy.x);
      vec2 g10 = vec2(gx.y, gy.y);
      vec2 g01 = vec2(gx.z, gy.z);
      vec2 g11 = vec2(gx.w, gy.w);
      vec4 norm = taylorInvSqrt(vec4(dot(g00,g00), dot(g01,g01), dot(g10,g10), dot(g11,g11)));
      g00 *= norm.x; g01 *= norm.y; g10 *= norm.z; g11 *= norm.w;
      float n00 = dot(g00, vec2(fx.x, fy.x));
      float n10 = dot(g10, vec2(fx.y, fy.y));
      float n01 = dot(g01, vec2(fx.z, fy.z));
      float n11 = dot(g11, vec2(fx.w, fy.w));
      vec2 fade_xy = fade(Pf.xy);
      vec2 n_x = mix(vec2(n00, n01), vec2(n10, n11), fade_xy.x);
      return 2.3 * mix(n_x.x, n_x.y, fade_xy.y);
    }

    const int OCTAVES = 4;
    float fbm(vec2 p) {
      float value = 0.0;
      float amp = 1.0;
      float freq = waveFrequency;
      for (int i = 0; i < OCTAVES; i++) {
        value += amp * abs(cnoise(p));
        p *= freq;
        amp *= waveAmplitude;
      }
      return value;
    }

    float pattern(vec2 p) {
      vec2 p2 = p - time * waveSpeed;
      return fbm(p + fbm(p2)); 
    }

    vec3 dither(vec2 coord, vec3 color) {
      vec2 bayerUV = floor(coord / pixelSize) / 8.0;
      float threshold = texture2D(bayerTex, bayerUV).r - 0.25;
      float stepVal = 1.0 / (colorNum - 1.0);
      color += threshold * stepVal;
      float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
      float bias = mix(0.2, 0.0, smoothstep(0.45, 0.8, luminance));
      color = clamp(color - bias, 0.0, 1.0);
      return floor(color * (colorNum - 1.0) + 0.5) / (colorNum - 1.0);
    }

    void main() {
      vec2 normalizedPixelSize = pixelSize / resolution;
      vec2 uv = gl_FragCoord.xy / resolution.xy;
      vec2 uvPixel = normalizedPixelSize * floor(uv / normalizedPixelSize);
      
      uvPixel -= 0.5;
      uvPixel.x *= resolution.x / resolution.y;
      
      float f = pattern(uvPixel);
      if (enableMouseInteraction == 1) {
        vec2 mouseNDC = (mousePos / resolution - 0.5) * vec2(1.0, -1.0);
        mouseNDC.x *= resolution.x / resolution.y;
        float dist = length(uvPixel - mouseNDC);
        float effect = 1.0 - smoothstep(0.0, mouseRadius, dist);
        f -= 0.5 * effect;
      }
      vec3 col = mix(backgroundColor, waveColor, clamp(f, 0.0, 1.0));
      vec3 dithered = dither(gl_FragCoord.xy, col);
      gl_FragColor = vec4(dithered, 1.0);
    }
  `;

  const PRESETS = {
    monochrome: {
      name: 'Monochrome',
      waveColor: [0.60, 0.60, 0.60],
      backgroundColor: [0.01, 0.01, 0.02],
      waveSpeed: 0.035,
      waveFrequency: 2.8,
      waveAmplitude: 0.28,
      pixelSize: 2.5,
      colorNum: 4.0
    },
    stealthGrey: {
      name: 'Stealth Grey',
      waveColor: [0.42, 0.42, 0.45],
      backgroundColor: [0.0, 0.0, 0.0],
      waveSpeed: 0.03,
      waveFrequency: 2.5,
      waveAmplitude: 0.25,
      pixelSize: 2.5,
      colorNum: 3.0
    },
    highContrast: {
      name: '1-Bit Retro',
      waveColor: [0.92, 0.92, 0.92],
      backgroundColor: [0.0, 0.0, 0.0],
      waveSpeed: 0.04,
      waveFrequency: 3.0,
      waveAmplitude: 0.35,
      pixelSize: 3.0,
      colorNum: 2.0
    },
    threatAlert: {
      name: 'Threat Alert',
      waveColor: [0.95, 0.95, 0.95],
      backgroundColor: [0.02, 0.02, 0.02],
      waveSpeed: 0.08,
      waveFrequency: 3.8,
      waveAmplitude: 0.45,
      pixelSize: 2.5,
      colorNum: 4.0
    }
  };

  class DitherEngine {
    constructor(canvasId = 'dither-canvas') {
      this.canvasId = canvasId;
      this.canvas = null;
      this.gl = null;
      this.program = null;
      this.uniforms = {};
      this.bayerTexture = null;
      this.animId = null;
      this.startTime = performance.now();
      this.enabled = true;
      this.currentPresetKey = 'monochrome';
      this.currentPreset = { ...PRESETS.monochrome };
      this.mouse = { x: -9999, y: -9999, active: 0 };
      this.pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);

      this.init();
    }

    init() {
      this.canvas = document.getElementById(this.canvasId);
      if (!this.canvas) {
        this.canvas = document.createElement('canvas');
        this.canvas.id = this.canvasId;
        document.body.prepend(this.canvas);
      }

      this.gl = this.canvas.getContext('webgl', {
        antialias: false,
        depth: false,
        stencil: false,
        alpha: true,
        preserveDrawingBuffer: false,
        powerPreference: 'low-power'
      }) || this.canvas.getContext('experimental-webgl');

      if (!this.gl) {
        console.warn('[DitherEngine] WebGL not supported on this platform.');
        return;
      }

      this.compileShaders();
      this.setupGeometry();
      this.setupBayerTexture();
      this.bindEvents();
      this.resize();

      if (this.enabled) {
        this.start();
      }
    }

    compileShaders() {
      const gl = this.gl;
      const vs = gl.createShader(gl.VERTEX_SHADER);
      gl.shaderSource(vs, VS_SOURCE);
      gl.compileShader(vs);
      if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
        console.error('[DitherEngine] VS compile error:', gl.getShaderInfoLog(vs));
        return;
      }

      const fs = gl.createShader(gl.FRAGMENT_SHADER);
      gl.shaderSource(fs, FS_SOURCE);
      gl.compileShader(fs);
      if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
        console.error('[DitherEngine] FS compile error:', gl.getShaderInfoLog(fs));
        return;
      }

      this.program = gl.createProgram();
      gl.attachShader(this.program, vs);
      gl.attachShader(this.program, fs);
      gl.linkProgram(this.program);
      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
        console.error('[DitherEngine] Program link error:', gl.getProgramInfoLog(this.program));
        return;
      }

      gl.useProgram(this.program);

      // Collect uniform locations
      const uniformNames = [
        'resolution', 'time', 'waveSpeed', 'waveFrequency', 'waveAmplitude',
        'waveColor', 'backgroundColor', 'mousePos', 'enableMouseInteraction',
        'mouseRadius', 'colorNum', 'pixelSize', 'bayerTex'
      ];
      uniformNames.forEach(name => {
        this.uniforms[name] = gl.getUniformLocation(this.program, name);
      });
    }

    setupGeometry() {
      const gl = this.gl;
      const quad = new Float32Array([
        -1.0, -1.0,
        1.0, -1.0,
        -1.0, 1.0,
        -1.0, 1.0,
        1.0, -1.0,
        1.0, 1.0
      ]);

      const buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);

      const posAttr = gl.getAttribLocation(this.program, 'a_position');
      gl.enableVertexAttribArray(posAttr);
      gl.vertexAttribPointer(posAttr, 2, gl.FLOAT, false, 0, 0);
    }

    setupBayerTexture() {
      const gl = this.gl;
      this.bayerTexture = gl.createTexture();
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.bayerTexture);
      gl.texImage2D(
        gl.TEXTURE_2D, 0, gl.LUMINANCE, 8, 8, 0,
        gl.LUMINANCE, gl.UNSIGNED_BYTE, BAYER_8X8
      );
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
    }

    resize() {
      if (!this.canvas || !this.gl) return;
      const width = Math.floor(window.innerWidth * this.pixelRatio);
      const height = Math.floor(window.innerHeight * this.pixelRatio);

      if (this.canvas.width !== width || this.canvas.height !== height) {
        this.canvas.width = width;
        this.canvas.height = height;
        this.gl.viewport(0, 0, width, height);
      }
    }

    bindEvents() {
      window.addEventListener('resize', () => this.resize(), { passive: true });

      const onPointerMove = (e) => {
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        this.mouse.x = clientX * this.pixelRatio;
        this.mouse.y = (window.innerHeight - clientY) * this.pixelRatio;
        this.mouse.active = 1;
      };

      window.addEventListener('mousemove', onPointerMove, { passive: true });
      window.addEventListener('touchmove', onPointerMove, { passive: true });

      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          this.stop();
        } else if (this.enabled) {
          this.start();
        }
      });

      // Keyboard shortcut: 'D' to toggle dither
      window.addEventListener('keydown', (e) => {
        const tag = (e.target.tagName || '').toUpperCase();
        if (tag === 'INPUT' || tag === 'TEXTAREA' || e.ctrlKey || e.metaKey || e.altKey) return;
        if (e.key === 'd' || e.key === 'D') {
          e.preventDefault();
          this.toggle();
        }
      });
    }

    start() {
      if (this.animId) return;
      const loop = (timestamp) => {
        this.render(timestamp);
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }

    stop() {
      if (this.animId) {
        cancelAnimationFrame(this.animId);
        this.animId = null;
      }
    }

    toggle() {
      this.enabled = !this.enabled;
      if (this.canvas) {
        this.canvas.style.display = this.enabled ? 'block' : 'none';
      }
      if (this.enabled) {
        this.start();
      } else {
        this.stop();
      }
      this.updateToggleButton();
      return this.enabled;
    }

    setPreset(presetKey) {
      if (PRESETS[presetKey]) {
        this.currentPresetKey = presetKey;
        this.currentPreset = { ...PRESETS[presetKey] };
      }
    }

    setThreatMode(isThreat) {
      if (isThreat) {
        this.setPreset('threatAlert');
        if (this.canvas) this.canvas.style.opacity = '0.45';
      } else {
        this.setPreset('monochrome');
        if (this.canvas) this.canvas.style.opacity = '0.28';
      }
    }

    cyclePreset() {
      const keys = Object.keys(PRESETS);
      const nextIdx = (keys.indexOf(this.currentPresetKey) + 1) % keys.length;
      this.setPreset(keys[nextIdx]);
      this.updateToggleButton();
      return this.currentPresetKey;
    }

    updateToggleButton() {
      const btn = document.getElementById('btn-toggle-dither');
      if (btn) {
        const label = btn.querySelector('.dither-label');
        if (label) {
          label.textContent = this.enabled ? `Dither: ON (${PRESETS[this.currentPresetKey].name})` : 'Dither: OFF';
        }
        btn.classList.toggle('text-white', this.enabled);
        btn.classList.toggle('border-zinc-500', this.enabled);
      }
    }

    render(timestamp) {
      const gl = this.gl;
      if (!gl || !this.program) return;

      const p = this.currentPreset;
      const elapsedTime = (timestamp - this.startTime) * 0.001;

      gl.useProgram(this.program);

      // Uniforms
      gl.uniform2f(this.uniforms.resolution, this.canvas.width, this.canvas.height);
      gl.uniform1f(this.uniforms.time, elapsedTime);
      gl.uniform1f(this.uniforms.waveSpeed, p.waveSpeed);
      gl.uniform1f(this.uniforms.waveFrequency, p.waveFrequency);
      gl.uniform1f(this.uniforms.waveAmplitude, p.waveAmplitude);
      gl.uniform3f(this.uniforms.waveColor, p.waveColor[0], p.waveColor[1], p.waveColor[2]);
      gl.uniform3f(this.uniforms.backgroundColor, p.backgroundColor[0], p.backgroundColor[1], p.backgroundColor[2]);
      gl.uniform2f(this.uniforms.mousePos, this.mouse.x, this.mouse.y);
      gl.uniform1i(this.uniforms.enableMouseInteraction, this.mouse.active);
      gl.uniform1f(this.uniforms.mouseRadius, 0.45);
      gl.uniform1f(this.uniforms.colorNum, p.colorNum);
      gl.uniform1f(this.uniforms.pixelSize, p.pixelSize);

      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.bayerTexture);
      gl.uniform1i(this.uniforms.bayerTex, 0);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }
  }

  // Auto-initialize when DOM is ready
  function autoInit() {
    if (!window.QuantumDither) {
      window.QuantumDither = new DitherEngine('dither-canvas');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

})(window);

