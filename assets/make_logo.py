"""Generates assets/logo.svg: a neon 3D tetrahedron ("Δ") spinning in place.

GitHub strips JavaScript from READMEs, so the 3D is precomputed here: every
frame of the rotation is projected in Python and the SVG plays the frames back
with SMIL <animate>, which interpolates smoothly between them.

Run:  python assets/make_logo.py
"""
import math
from pathlib import Path

# ── tunables ────────────────────────────────────────────────────────────────
FRAMES = 60            # frames per loop
DURATION = 6           # seconds per loop
SIZE = 400             # svg canvas
CENTER = (200, 185)
SCALE = 520            # projection focal length (px)
CAM_DIST = 4.2         # camera distance from origin
PITCH = math.radians(18)   # camera looks slightly down
LIGHT = (-0.5, 0.7, 0.6)   # light direction (towards the light)

RED, HOT, DARK = "#FF4444", "#FF2A2A", "#8B0000"

# ── geometry ────────────────────────────────────────────────────────────────
# Regular tetrahedron, apex up, centred on the origin.
r = math.sqrt(8) / 3
VERTS = [(0.0, 1.0, 0.0)] + [
    (r * math.cos(math.radians(90 + 120 * k)), -1 / 3, r * math.sin(math.radians(90 + 120 * k)))
    for k in range(3)
]
EDGES = [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3), (3, 1)]
FACES = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


LIGHT = norm(LIGHT)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def transform(p, yaw):
    """Spin around Y, then pitch the world so the camera looks down on it."""
    x, y, z = p
    x, z = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)
    y, z = y * math.cos(PITCH) - z * math.sin(PITCH), y * math.sin(PITCH) + z * math.cos(PITCH)
    return (x, y, z)


def project(p):
    x, y, z = p
    k = SCALE / (CAM_DIST - z)
    return (CENTER[0] + x * k, CENTER[1] - y * k)


def lerp(a, b, t):
    return a + (b - a) * t


def fmt(n):
    return f"{n:.1f}".rstrip("0").rstrip(".")


# ── precompute every frame ──────────────────────────────────────────────────
# A tetrahedron has 3-fold symmetry around Y, so 120° of spin loops seamlessly.
cam = (0, 0, CAM_DIST)
edge_d = [[] for _ in EDGES]
edge_op = [[] for _ in EDGES]
edge_w = [[] for _ in EDGES]
face_d = [[] for _ in FACES]
face_op = [[] for _ in FACES]
vert_x = [[] for _ in VERTS]
vert_y = [[] for _ in VERTS]
vert_r = [[] for _ in VERTS]

for f in range(FRAMES + 1):
    yaw = math.radians(120) * f / FRAMES
    world = [transform(v, yaw) for v in VERTS]
    screen = [project(v) for v in world]

    for i, (a, b) in enumerate(EDGES):
        depth = (world[a][2] + world[b][2]) / 2          # -1 (back) .. +1 (front)
        t = max(0.0, min(1.0, (depth + 0.9) / 1.6))
        (x1, y1), (x2, y2) = screen[a], screen[b]
        edge_d[i].append(f"M{fmt(x1)} {fmt(y1)}L{fmt(x2)} {fmt(y2)}")
        edge_op[i].append(f"{lerp(0.18, 1.0, t):.2f}")
        edge_w[i].append(f"{lerp(1.5, 5.5, t):.2f}")

    for i, (a, b, c) in enumerate(FACES):
        n = norm(cross(sub(world[b], world[a]), sub(world[c], world[a])))
        centroid = tuple(sum(world[j][k] for j in (a, b, c)) / 3 for k in range(3))
        # Make sure the normal points outwards (away from the origin).
        if dot(n, centroid) < 0:
            n = tuple(-c_ for c_ in n)
        facing = dot(n, norm(sub(cam, centroid)))
        lit = max(0.0, dot(n, LIGHT))
        op = 0.04 + 0.42 * lit if facing > 0 else 0.03
        pts = [screen[j] for j in (a, b, c)]
        face_d[i].append("M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z")
        face_op[i].append(f"{op:.2f}")

    for i, v in enumerate(world):
        t = max(0.0, min(1.0, (v[2] + 1) / 2))
        vert_x[i].append(fmt(screen[i][0]))
        vert_y[i].append(fmt(screen[i][1]))
        vert_r[i].append(f"{lerp(2.0, 5.5, t):.2f}")


def anim(attr, values):
    return (f'<animate attributeName="{attr}" dur="{DURATION}s" repeatCount="indefinite" '
            f'calcMode="linear" values="{";".join(values)}"/>')


# ── floor grid (static, in perspective) ─────────────────────────────────────
FLOOR_Y = -1.0   # below the base, so the pyramid hovers
grid = []
for i in range(-6, 7):
    a = project(transform((i * 0.4, FLOOR_Y, -2.4), 0))
    b = project(transform((i * 0.4, FLOOR_Y, 2.4), 0))
    grid.append(f'<path d="M{fmt(a[0])} {fmt(a[1])}L{fmt(b[0])} {fmt(b[1])}"/>')
for j in range(-6, 7):
    a = project(transform((-2.4, FLOOR_Y, j * 0.4), 0))
    b = project(transform((2.4, FLOOR_Y, j * 0.4), 0))
    grid.append(f'<path d="M{fmt(a[0])} {fmt(a[1])}L{fmt(b[0])} {fmt(b[1])}"/>')
shadow_c = project(transform((0, FLOOR_Y, 0), 0))

# ── assemble ────────────────────────────────────────────────────────────────
faces_svg = "\n".join(
    f'      <path fill="{HOT}">{anim("d", face_d[i])}{anim("fill-opacity", face_op[i])}</path>'
    for i in range(len(FACES))
)
edges_svg = "\n".join(
    f'      <path fill="none" stroke="{RED}" stroke-linecap="round">'
    f'{anim("d", edge_d[i])}{anim("stroke-opacity", edge_op[i])}{anim("stroke-width", edge_w[i])}</path>'
    for i in range(len(EDGES))
)
verts_svg = "\n".join(
    f'      <circle fill="#ffffff">{anim("cx", vert_x[i])}{anim("cy", vert_y[i])}{anim("r", vert_r[i])}</circle>'
    for i in range(len(VERTS))
)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}">
  <!-- generated by assets/make_logo.py — edit that, not this -->
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#ffffff" opacity="0.035"/>
    </pattern>
    <radialGradient id="vignette" cx="50%" cy="50%" r="60%">
      <stop offset="0%" stop-color="#3d0000" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="floorfade" cx="50%" cy="{shadow_c[1] / SIZE * 100:.0f}%" r="45%">
      <stop offset="0%" stop-color="#fff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <mask id="floormask"><rect width="{SIZE}" height="{SIZE}" fill="url(#floorfade)"/></mask>
  </defs>

  <style>
    .intro {{ opacity: 0; transform-box: view-box; transform-origin: 200px 220px;
             animation: intro 1.4s cubic-bezier(.2,.9,.3,1.2) forwards; }}
    .late  {{ opacity: 0; animation: fadein 1s 1s forwards; }}
    .bob   {{ animation: bob 3s ease-in-out infinite; }}
    .shadow {{ transform-box: fill-box; transform-origin: center;
              animation: shadow 3s ease-in-out infinite; }}
    .shake {{ animation: shake 5s 3s steps(1) infinite; }}
    .ghost-a {{ opacity: 0; animation: ghostA 5s 3s steps(1) infinite; }}
    .ghost-b {{ opacity: 0; animation: ghostB 5s 3s steps(1) infinite; }}

    @keyframes intro  {{ from {{ opacity: 0; transform: scale(.3) rotate(-25deg); }}
                        to   {{ opacity: 1; transform: scale(1) rotate(0); }} }}
    @keyframes fadein {{ to {{ opacity: 1; }} }}
    @keyframes bob    {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes shadow {{ 0%, 100% {{ opacity: .75; transform: scale(1); }} 50% {{ opacity: .35; transform: scale(.75); }} }}
    @keyframes shake  {{ 0% {{ transform: translate(0,0); }} 90% {{ transform: translate(-4px,1px); }}
                        91% {{ transform: translate(5px,-2px); }} 92% {{ transform: translate(-2px,0); }}
                        93% {{ transform: translate(0,0); }} }}
    @keyframes ghostA {{ 0% {{ opacity: 0; }} 90% {{ opacity: .6; transform: translate(-9px,2px); }}
                        91% {{ opacity: .6; transform: translate(7px,-3px); }} 92% {{ opacity: 0; }} }}
    @keyframes ghostB {{ 0% {{ opacity: 0; }} 90% {{ opacity: .45; transform: translate(8px,-1px); }}
                        91% {{ opacity: .45; transform: translate(-6px,3px); }} 92% {{ opacity: 0; }} }}
  </style>

  <!-- background -->
  <rect width="{SIZE}" height="{SIZE}" rx="24" fill="#0d1117"/>
  <rect width="{SIZE}" height="{SIZE}" rx="24" fill="url(#vignette)"/>

  <!-- synthwave floor -->
  <g class="late" mask="url(#floormask)" stroke="{DARK}" stroke-width="1" opacity=".9">
    {"".join(grid)}
  </g>
  <g class="late"><ellipse class="shadow" cx="{fmt(shadow_c[0])}" cy="{fmt(shadow_c[1])}" rx="80" ry="12" fill="{HOT}" filter="url(#soft)"/></g>

  <!-- the spinning pyramid -->
  <g class="intro">
    <g class="bob"><g id="pyr" class="shake">
{faces_svg}
      <g filter="url(#glow)">
{edges_svg}
      </g>
      <g filter="url(#glow)">
{verts_svg}
      </g>
    </g></g>
  </g>

  <!-- glitch ghosts -->
  <use href="#pyr" class="ghost-a" style="filter: hue-rotate(0deg) saturate(3)"/>
  <use href="#pyr" class="ghost-b" style="filter: grayscale(1) brightness(3)"/>

  <!-- label -->
  <text class="late" x="200" y="378" text-anchor="middle" fill="#c9d1d9"
        font-family="JetBrains Mono, Fira Code, Consolas, monospace" font-size="18" letter-spacing="6">DELTA<tspan fill="{RED}">AT</tspan></text>

  <!-- CRT scanlines -->
  <rect width="{SIZE}" height="{SIZE}" rx="24" fill="url(#scan)"/>
</svg>
'''

out = Path(__file__).with_name("logo.svg")
out.write_text(svg, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(svg) / 1024:.0f} KB)")
