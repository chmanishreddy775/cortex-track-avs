import { Renderer, Program, Mesh, Triangle } from 'https://cdn.jsdelivr.net/npm/ogl@1.0.11/src/index.js';

const vertex = `
attribute vec2 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}`;

// I kept your exact fragment shader here
const fragment = `
precision highp float;
uniform vec3  iResolution;
uniform vec2  iMouse;
uniform float iTime;
uniform vec3  uColor0; uniform vec3  uColor1; uniform vec3  uColor2;
uniform vec3  uBgColor; uniform vec3  uMouseColor;
uniform float uSpeed; uniform int   uStreakCount; uniform float uStreakWidth;
uniform float uStreakLength; uniform float uGlow; uniform float uDensity;
uniform float uTwinkle; uniform float uZoom; uniform float uBgGlow;
uniform float uOpacity; uniform float uMouseEnabled; uniform float uMouseStrength;
uniform float uMouseRadius;
varying vec2 vUv;

vec3 palette(float h) {
  int idx = int(floor(clamp(h, 0.0, 0.999999) * 3.0));
  if (idx <= 0) return uColor0;
  if (idx == 1) return uColor1;
  return uColor2;
}

vec3 tanhv(vec3 x) {
  vec3 e = exp(-2.0 * x);
  return (1.0 - e) / (1.0 + e);
}

vec2 sceneC(vec2 frag, vec2 r) {
  vec2 P = (frag + frag - r) / r.x;
  float z = 0.0; float d = 1e3; vec4 O = vec4(0.0);
  for (int k = 0; k < 39; k++) {
    if (d <= 1e-4) break;
    O = z * normalize(vec4(P, uZoom, 0.0)) - vec4(0.0, 4.0, 1.0, 0.0) / 4.5;
    d = 1.0 - sqrt(length(O * O)); z += d;
  }
  return vec2(O.x, atan(O.z, O.y));
}

void mainImage(out vec4 o, vec2 C) {
  vec2 r = iResolution.xy; vec2 uv0 = (C + C - r) / r.x;
  float T = 0.1 * iTime * uSpeed + 9.0;
  float angRings = max(1.0, floor(6.28318530718 * max(uDensity, 0.05) + 0.5));
  vec2 Y = vec2(5e-3, 6.28318530718 / angRings);
  vec2 c0 = sceneC(C, r); vec2 cdx = sceneC(C + vec2(1.0, 0.0), r); vec2 cdy = sceneC(C + vec2(0.0, 1.0), r);
  vec2 dCx = cdx - c0; vec2 dCy = cdy - c0;
  dCx.y -= 6.28318530718 * floor(dCx.y / 6.28318530718 + 0.5);
  dCy.y -= 6.28318530718 * floor(dCy.y / 6.28318530718 + 0.5);
  vec2 fw = abs(dCx) + abs(dCy); C = c0;
  vec2 P = vec2(2.0, 1.0) * uv0 - (r / r.x) * vec2(0.0, 1.0);
  vec4 O = vec4(uBgColor * 90.0 * uBgGlow / (1e3 * dot(P, P) + 6.0), 0.0);

  float mGlow = 0.0;
  if (uMouseEnabled > 0.5) {
    vec2 mN = (iMouse + iMouse - r) / r.x;
    float md = length(uv0 - mN);
    mGlow = exp(-md * md / max(uMouseRadius * uMouseRadius, 1e-4)) * uMouseStrength;
    O.rgb += uMouseColor * mGlow * 0.25;
  }

  float zr = 5e-4 * uStreakWidth; vec2 rr = vec2(max(length(fw), 1e-5));
  float tail = 19.0 / max(uStreakLength, 0.05);

  for (int m = 0; m < 16; m++) {
    if (m >= uStreakCount) break;
    float jf = float(m) + 1.0;
    float ic = fract(sin(dot(vec2(jf, floor(C.x / Y.x + 0.5)), vec2(7.0, 11.0)) * 73.0));
    vec2 Pp = C - (T + T * ic) * vec2(0.0, 1.0); Pp -= floor(Pp / Y + 0.5) * Y;
    float h = fract(8663.0 * ic); vec3 col = palette(h);
    float weight = mix(1.5, 1.0 + sin(T + 7.0 * h + 4.0), uTwinkle);
    weight *= (1.0 + mGlow * 2.0);
    vec2 inner = vec2(length(max(Pp, vec2(-1.0, 0.0))), length(Pp) - zr) - zr;
    vec2 sm = vec2(1.0) - smoothstep(-rr, rr, inner);
    O.rgb += dot(sm, vec2(exp(tail * Pp.y), 3.0)) * col * weight;
    C.x += Y.x / 8.0;
  }
  vec3 colr = sqrt(tanhv(max(O.rgb * uGlow - vec3(0.04, 0.08, 0.02), 0.0)));
  o = vec4(colr, uOpacity);
}

void main() { vec4 color; mainImage(color, vUv * iResolution.xy); gl_FragColor = color; }
`;

export function initLightfall(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const renderer = new Renderer({ dpr: window.devicePixelRatio || 1, alpha: true, antialias: true });
  const gl = renderer.gl;
  gl.canvas.style.width = '100%';
  gl.canvas.style.height = '100%';
  gl.canvas.style.display = 'block';
  container.appendChild(gl.canvas);

  // Default colors from your configuration
  const hexToRGB = hex => {
    const c = hex.replace('#', '');
    return [parseInt(c.slice(0, 2), 16) / 255, parseInt(c.slice(2, 4), 16) / 255, parseInt(c.slice(4, 6), 16) / 255];
  };

  const uniforms = {
    iResolution: { value: [gl.drawingBufferWidth, gl.drawingBufferHeight, 1] },
    iMouse: { value: [0, 0] },
    iTime: { value: 0 },
    uColor0: { value: hexToRGB('#A6C8FF') },
    uColor1: { value: hexToRGB('#5227FF') },
    uColor2: { value: hexToRGB('#FF9FFC') },
    uBgColor: { value: hexToRGB('#0A29FF') },
    uMouseColor: { value: [0.5, 0.5, 1.0] },
    uSpeed: { value: 0.3 },
    uStreakCount: { value: 8 },
    uStreakWidth: { value: 0.2 },
    uStreakLength: { value: 0.8 },
    uGlow: { value: 0.3 },
    uDensity: { value: 0.5 },
    uTwinkle: { value: 0.15 },
    uZoom: { value: 1.5 },
    uBgGlow: { value: 0.3 },
    uOpacity: { value: 1 },
    uMouseEnabled: { value: 1 },
    uMouseStrength: { value: 1 },
    uMouseRadius: { value: 0.6 }
  };

  const program = new Program(gl, { vertex, fragment, uniforms });
  const mesh = new Mesh(gl, { geometry: new Triangle(gl), program });

  const resize = () => {
    const rect = container.getBoundingClientRect();
    renderer.setSize(rect.width, rect.height);
    uniforms.iResolution.value = [gl.drawingBufferWidth, gl.drawingBufferHeight, 1];
  };
  window.addEventListener('resize', resize);
  resize();

  container.addEventListener('pointermove', e => {
    const rect = gl.canvas.getBoundingClientRect();
    uniforms.iMouse.value = [(e.clientX - rect.left) * renderer.dpr, (rect.height - (e.clientY - rect.top)) * renderer.dpr];
  });

  requestAnimationFrame(function loop(t) {
    requestAnimationFrame(loop);
    uniforms.iTime.value = t * 0.001;
    renderer.render({ scene: mesh });
  });
}