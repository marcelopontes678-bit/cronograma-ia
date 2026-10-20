// Mesa de luz: um mundo (mm), uma câmera, uma lupa. WebGL2 para a imagem, canvas 2D para as marcas.
// Tudo é função de t (determinístico): o roteiro (film.js) entrega o estado de cada quadro.

export const LAYER = 1600;          // lado de cada camada do texture array (px)
export const MAXOBJ = 12;

const VS = `#version 300 es
in vec2 p; void main(){ gl_Position = vec4(p,0.,1.); }`;

const FS = `#version 300 es
precision highp float;
precision highp sampler2DArray;
uniform sampler2DArray uTex;
uniform vec2 uRes;
uniform vec4 uCam;          // cx, cy (mm), zoom (px/mm), roll (rad)
uniform float uOn;          // mesa ligada 0..1
uniform vec2 uTable;        // meia largura / meia altura da mesa (mm)
uniform int uN;
uniform vec4 uObj[${MAXOBJ}];    // cx, cy, cos, sin
uniform vec4 uDim[${MAXOBJ}];    // meia largura, meia altura (mm), escala uv x, y
uniform vec4 uMat[${MAXOBJ}];    // tipo (0 papel, 1 slide), moldura (mm), opacidade, apagar o resto 0..1
uniform vec4 uBand[${MAXOBJ}];   // linha acesa: u0, v0, u1, v1 (uv do objeto)
uniform float uBandOn[${MAXOBJ}];
uniform vec4 uLens;         // centro na tela (px), raio (px), aumento
uniform vec4 uLens2;        // presença 0..1, elevação 0..1, abertura (lente -> fotografia) 0..1, k
uniform float uVig;
out vec4 o;

float h21(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); vec2 u=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),u.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),u.x), u.y); }

mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,s,-s,c); }
vec2 s2w(vec2 px){ return uCam.xy + rot(-uCam.w) * ((px - uRes*.5) / uCam.z); }

vec3 table(vec2 w){
  vec2 q = abs(w) - uTable;
  float inside = step(max(q.x,q.y), 0.);
  vec2 n = w / uTable;
  float fall = 1. - .07*dot(n,n);
  float diff = (vn(w*.35)-.5)*.010 + (vn(w*2.7)-.5)*.006;
  float lit = mix(.035, 1., uOn);
  vec3 glow = vec3(.965,.976,.988) * (fall + diff) * lit;
  // moldura de alumínio (14 mm) e mesa escura além
  float fr = max(q.x,q.y);
  vec3 alu = vec3(.55,.57,.60) * (.85 + .25*smoothstep(14.,0.,fr)) * mix(.35, 1., uOn*.6+.4);
  alu *= .92 + .08*vn(vec2(w.x*.05, w.y*3.));
  vec3 desk = vec3(.045,.046,.05) * (.9 + .2*vn(w*.02 + vec2(0., w.x*.004)));
  desk += vec3(.06,.065,.07) * uOn * exp(-max(fr-14.,0.)*.035);   // luz que vaza da mesa
  vec3 c = fr < 0. ? glow : (fr < 14. ? alu : desk);
  return c;
}

// devolve cor sobre a mesa no ponto w; g = mm por pixel (para o mip)
vec3 scene(vec2 w, float g){
  vec3 c = table(w);
  float lit = mix(.035, 1., uOn);
  float dimAll = 0.;
  for (int i = 0; i < ${MAXOBJ}; i++){
    if (i >= uN) break;
    float op = uMat[i].z;
    if (op <= 0.) continue;
    vec2 d = w - uObj[i].xy;
    vec2 l = vec2(dot(d, uObj[i].zw), dot(d, vec2(-uObj[i].w, uObj[i].z)));
    vec2 hs = uDim[i].xy;
    vec2 q = abs(l) - hs;
    float edge = -max(q.x, q.y);                 // mm até a borda (positivo = dentro)
    // sombra de contato muito leve fora do objeto
    if (edge < 0.) { c *= 1. - .10*op*exp(edge*.9)*step(-3., edge); continue; }
    float kind = uMat[i].x, mount = uMat[i].y;
    vec2 uv = (l + hs) / (2.*hs);
    vec3 col;
    if (kind < .5) {
      // papel retroiluminado: a cor é transmissão
      vec2 tuv = vec2(uv.x, uv.y) * uDim[i].zw;
      vec2 gx = vec2(g/(2.*hs.x)*uDim[i].z, 0.), gy = vec2(0., g/(2.*hs.y)*uDim[i].w);
      vec3 s = textureGrad(uTex, vec3(tuv, float(i)), gx, gy).rgb;
      float ink = 1. - dot(s, vec3(.299,.587,.114));
      vec4 b = uBand[i];
      float inBand = step(b.x, uv.x)*step(uv.x, b.z)*step(b.y, uv.y)*step(uv.y, b.w);
      float bon = uBandOn[i];
      float dim = bon * (1. - inBand) * .55;
      ink = mix(ink, pow(ink, .7), bon*inBand);
      vec3 paper = vec3(1., .968, .915) * mix(1., 1.045, bon*inBand);
      col = paper * (1. - ink*.92) ;
      col = mix(col, vec3(.86,.84,.80) - ink*.25, dim);           // o resto da página recua
      col *= lit * (.93 + .05*vn(l*.6));
      col += vec3(.06,.042,.0) * lit * exp(-edge*.9);              // borda quente
    } else {
      // diapositivo: moldura opaca + filme colorido
      vec2 inner = hs - vec2(mount);
      vec2 qi = abs(l) - inner;
      if (max(qi.x, qi.y) > 0.) {
        float bev = smoothstep(0., 1.2, -max(qi.x,qi.y) + mount) ;
        col = vec3(.16,.165,.17) * (.55 + .45*lit) * (.85 + .15*bev) + vec3(.02)*vn(l*1.7);
      } else {
        vec2 iuv = (l + inner) / (2.*inner);
        vec2 tuv = iuv * uDim[i].zw;
        vec2 gx = vec2(g/(2.*inner.x)*uDim[i].z, 0.), gy = vec2(0., g/(2.*inner.y)*uDim[i].w);
        vec3 s = textureGrad(uTex, vec3(tuv, float(i)), gx, gy).rgb;
        col = s * lit * 1.02 + vec3(.012)*lit;
        float ed = -max(qi.x, qi.y);
        col *= .9 + .1*smoothstep(0., 1.5, ed);
      }
    }
    c = mix(c, col, op);
    dimAll = max(dimAll, uMat[i].w);
  }
  return c;
}

void main(){
  vec2 px = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);
  float g = 1. / uCam.z;
  vec3 col;
  float on = uLens2.x, lift = uLens2.y, open = uLens2.z, k = uLens2.w;
  vec2 Ls = uLens.xy; float R = uLens.z, M = uLens.w;
  vec2 dv = px - Ls; float r = length(dv) / max(R, 1.);
  vec2 Lw = s2w(Ls);
  if (on > 0. && r < 1.) {
    float kk = k * (1. - open);
    vec2 base = rot(-uCam.w) * dv / (uCam.z * M);
    float gl = g / M;
    vec3 cr = scene(Lw + base * (1. + (kk+.012)*r*r), gl);
    vec3 cg = scene(Lw + base * (1. + kk*r*r), gl);
    vec3 cb = scene(Lw + base * (1. + (kk-.012)*r*r), gl);
    col = vec3(cr.r, cg.g, cb.b);
    col *= 1. - .18*(1.-open)*smoothstep(.75, 1., r);              // escurece junto ao aro
    col += vec3(.05) * (1.-open) * smoothstep(.55,.0, length(dv/R - vec2(-.35,-.42)));  // reflexo
  } else {
    col = scene(s2w(px), g);
    if (on > 0.) {
      float ring = 1.07, skirt = 1.34;
      if (r < ring) {
        float a = atan(dv.y, dv.x);
        float bev = smoothstep(1., 1.035, r) * (1. - smoothstep(1.035, ring, r));
        col = vec3(.035,.036,.04) + vec3(.28)*bev*(.5+.5*cos(a + 2.2)) ;
      } else if (r < skirt) {
        // saia de acrílico: refrata a mesa e brilha no pé
        vec2 dir = dv / max(length(dv), 1e-3);
        vec3 t = scene(s2w(px - dir * R * .06 * (skirt - r)), g);
        float foot = smoothstep(skirt - .06, skirt, r);
        col = mix(t, vec3(.98,.99,1.), .07) + vec3(.06,.07,.08) * foot * (1.-lift);
        col *= 1. - .10 * smoothstep(skirt - .015, skirt, r) + .10 * smoothstep(skirt - .03, skirt - .015, r);
      } else {
        // sombra suave da lupa quando levantada
        vec2 so = vec2(14., 22.) * (.3 + lift);
        float rs = length(px - Ls - so) / (R * skirt);
        col *= 1. - (.16 + .12*lift) * on * (1. - smoothstep(.85, 1.25 + lift*.3, rs));
      }
    }
  }
  // vinheta leve
  vec2 uvs = px / uRes - .5;
  col *= 1. - uVig * dot(uvs*vec2(1., .8), uvs*vec2(1., .8)) * 1.6;
  o = vec4(pow(max(col, 0.), vec3(1.)), 1.);
}`;

export function createEngine(gl, W, H) {
  const sh = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x);
    if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(x)); return x; };
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const U = n => gl.getUniformLocation(prog, n);
  const u = {};
  for (const n of ['uTex','uRes','uCam','uOn','uTable','uN','uObj','uDim','uMat','uBand','uBandOn','uLens','uLens2','uVig']) u[n] = U(n);

  function upload(images) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, tex);
    gl.texStorage3D(gl.TEXTURE_2D_ARRAY, 6, gl.RGBA8, LAYER, LAYER, images.length);
    const cv = document.createElement('canvas'); cv.width = cv.height = LAYER;
    const cx = cv.getContext('2d');
    const scales = images.map((img, i) => {
      const s = Math.min(1, LAYER / Math.max(img.width, img.height));
      const w = Math.round(img.width * s), h = Math.round(img.height * s);
      cx.clearRect(0, 0, LAYER, LAYER); cx.fillStyle = '#fff'; cx.fillRect(0, 0, LAYER, LAYER);
      cx.drawImage(img, 0, 0, w, h);
      gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, i, LAYER, LAYER, 1, gl.RGBA, gl.UNSIGNED_BYTE, cv);
      return [w / LAYER, h / LAYER];
    });
    gl.generateMipmap(gl.TEXTURE_2D_ARRAY);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.uniform1i(u.uTex, 0);
    return scales;
  }

  // st = { cam:{x,y,z,roll}, on, table:[hw,hh], objs:[{x,y,r,hw,hh,su,sv,kind,mount,op,band,bandOn}], lens:{x,y,R,M,on,lift,open,k}, vig }
  function draw(st) {
    gl.viewport(0, 0, W, H);
    gl.uniform2f(u.uRes, W, H);
    gl.uniform4f(u.uCam, st.cam.x, st.cam.y, st.cam.z, st.cam.roll || 0);
    gl.uniform1f(u.uOn, st.on);
    gl.uniform2f(u.uTable, st.table[0], st.table[1]);
    gl.uniform1i(u.uN, st.objs.length);
    const A = (n, f) => { const a = new Float32Array(MAXOBJ * n); st.objs.forEach((o, i) => a.set(f(o), i * n)); return a; };
    gl.uniform4fv(u.uObj, A(4, o => [o.x, o.y, Math.cos(o.r), Math.sin(o.r)]));
    gl.uniform4fv(u.uDim, A(4, o => [o.hw, o.hh, o.su, o.sv]));
    gl.uniform4fv(u.uMat, A(4, o => [o.kind, o.mount || 0, o.op, 0]));
    gl.uniform4fv(u.uBand, A(4, o => o.band || [0, 0, 0, 0]));
    gl.uniform1fv(u.uBandOn, A(1, o => [o.bandOn || 0]));
    const L = st.lens;
    gl.uniform4f(u.uLens, L.x, L.y, L.R, L.M);
    gl.uniform4f(u.uLens2, L.on, L.lift, L.open, L.k ?? .16);
    gl.uniform1f(u.uVig, st.vig ?? .18);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  return { upload, draw };
}
