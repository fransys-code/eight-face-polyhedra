#!/usr/bin/env python3
"""Exact check of polyhedra given by planes, rational vertices and faces.

Usage:
  verify.py FILE.jsonl [FILE.jsonl ...]     check every shape of a census file
  verify.py --one FILE.json [--expect-invalid]   check a single polyhedron

Standard library only; all tests use exact rational arithmetic.
"""
import json
import os
import sys
from collections import Counter
from fractions import Fraction as Fr
from itertools import combinations


class Invalid(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise Invalid(msg)


def det3(a, b, c):
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def side(plane, v):
    return plane[0] * v[0] + plane[1] * v[1] + plane[2] * v[2] - plane[3]


def meet(p, q, r):
    d = det3(p[:3], q[:3], r[:3])
    need(d != 0, "three planes of a vertex do not meet in a point")
    rows = (p, q, r)
    return tuple(det3(*[[row[3] if j == k else row[j] for j in range(3)] for row in rows]) / d for k in range(3))


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a, b, p):
    return (orient(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def segments_meet(a, b, c, d):
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    return on_segment(a, b, c) or on_segment(a, b, d) or on_segment(c, d, a) or on_segment(c, d, b)


def in_closed_polygon(poly, p):
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if on_segment(a, b, p):
            return True
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                inside = not inside
    return inside


def drop_axis(normal):
    k = max(range(3), key=lambda i: abs(normal[i]))
    return [i for i in range(3) if i != k]


def merge(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def intersect(xs, ys):
    out = []
    for a, b in xs:
        for c, d in ys:
            lo, hi = max(a, c), min(b, d)
            if lo <= hi:
                out.append((lo, hi))
    return merge(out)


def trace(face3, face2, other_plane, direction, k):
    """Intersection of a face with the line where its plane meets other_plane, as closed intervals of coordinate k."""
    s = [side(other_plane, v) for v in face3]
    n = len(face3)
    crit = {}
    for i in range(n):
        v, w = face3[i], face3[(i + 1) % n]
        if s[i] == 0:
            crit[v[k]] = v
        elif s[i] * s[(i + 1) % n] < 0:
            t = s[i] / (s[i] - s[(i + 1) % n])
            p = tuple(v[j] + t * (w[j] - v[j]) for j in range(3))
            crit[p[k]] = p
    ts = sorted(crit)
    out = [(t, t) for t in ts]
    poly, ax = face2
    for t0, t1 in zip(ts, ts[1:]):
        p0 = crit[t0]
        lam = (t1 - t0) / 2 / direction[k]
        mid = tuple(p0[j] + lam * direction[j] for j in range(3))
        if in_closed_polygon(poly, (mid[ax[0]], mid[ax[1]])):
            out.append((t0, t1))
    return merge(out)


def canonical_map(faces):
    best = None
    for cyc in (faces, [c[::-1] for c in faces]):
        nxt = {}
        for c in cyc:
            m = len(c)
            for i in range(m):
                nxt[(c[i], c[(i + 1) % m])] = (c[(i + 1) % m], c[(i + 2) % m])
        for start in nxt:
            label, order, code, i = {start: 0}, [start], [], 0
            while i < len(order):
                d = order[i]
                for e in (nxt[d], (d[1], d[0])):
                    if e not in label:
                        label[e] = len(order)
                        order.append(e)
                    code.append(label[e])
                i += 1
            code = tuple(code)
            if best is None or code < best:
                best = code
    return best


def check(d):
    planes = [tuple(Fr(x) for x in p) for p in d["planes"]]
    faces = [list(f) for f in d["faces"]]
    if "vertices" in d:
        verts = [tuple(Fr(x) for x in v) for v in d["vertices"]]
    else:
        verts = [meet(*(planes[i] for i in t)) for t in d["tri"]]
    F, V = len(faces), len(verts)
    need(len(planes) == F, "one plane per face expected")
    need(len(set(verts)) == V, "repeated vertex")
    for a, b in combinations(range(F), 2):
        n = cross(planes[a][:3], planes[b][:3])
        if n == (0, 0, 0):
            i = max(range(3), key=lambda j: abs(planes[a][j]))
            need(planes[a][3] * planes[b][i] != planes[b][3] * planes[a][i], f"faces {a} and {b} are coplanar")

    edge_faces = {}
    directed = set()
    at_vertex = [set() for _ in range(V)]
    for f, cyc in enumerate(faces):
        need(len(cyc) >= 3 and len(set(cyc)) == len(cyc), f"face {f}: not a simple cycle")
        need(any(planes[f][:3]), f"face {f}: null plane")
        for i, v in enumerate(cyc):
            need(0 <= v < V, "vertex index out of range")
            need(side(planes[f], verts[v]) == 0, f"face {f}: vertex {v} not in its plane")
            w = cyc[(i + 1) % len(cyc)]
            edge_faces.setdefault(frozenset((v, w)), []).append(f)
            directed.add((v, w))
            at_vertex[v].add(f)
    need(all(len(fs) == 2 and fs[0] != fs[1] for fs in edge_faces.values()), "an edge is not in exactly two faces")
    E = len(edge_faces)

    degree = Counter(v for e in edge_faces for v in e)
    for v in range(V):
        need(degree[v] == 3 and len(at_vertex[v]) == 3, f"vertex {v}: not exactly three faces and three edges")
        need(det3(*(planes[f][:3] for f in at_vertex[v])) != 0, f"vertex {v}: its three planes are not independent")

    flip = {0: False}
    stack = [0]
    while stack:
        f = stack.pop()
        cyc = faces[f]
        for i, v in enumerate(cyc):
            w = cyc[(i + 1) % len(cyc)]
            g = [x for x in edge_faces[frozenset((v, w))] if x != f][0]
            same_direction = any(faces[g][j] == v and faces[g][(j + 1) % len(faces[g])] == w for j in range(len(faces[g])))
            want = flip[f] if not same_direction else not flip[f]
            if g not in flip:
                flip[g] = want
                stack.append(g)
            else:
                need(flip[g] == want, "surface is not orientable")
    need(len(flip) == F, "surface is not connected")
    chi = V - E + F
    need(chi % 2 == 0 and chi <= 2, "bad Euler characteristic")
    genus = (2 - chi) // 2

    flat = []
    for f, cyc in enumerate(faces):
        ax = drop_axis(planes[f][:3])
        poly = [(verts[v][ax[0]], verts[v][ax[1]]) for v in cyc]
        n = len(poly)
        for i in range(n):
            need(orient(poly[i - 1], poly[i], poly[(i + 1) % n]) != 0, f"face {f}: flat corner")
            for j in range(i + 1, n):
                if j == i + 1 or (i == 0 and j == n - 1):
                    continue
                need(not segments_meet(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]),
                     f"face {f}: boundary crosses itself")
        flat.append((poly, ax))

    shared = Counter()
    for e, (a, b) in edge_faces.items():
        shared[(min(a, b), max(a, b))] += 1
    for a, b in combinations(range(F), 2):
        direction = cross(planes[a][:3], planes[b][:3])
        if direction == (0, 0, 0):
            continue
        k = max(range(3), key=lambda j: abs(direction[j]))
        ia = trace([verts[v] for v in faces[a]], flat[a], planes[b], direction, k)
        ib = trace([verts[v] for v in faces[b]], flat[b], planes[a], direction, k)
        common = intersect(ia, ib)
        expected = merge([tuple(sorted((verts[v][k], verts[w][k])))
                          for e, fs in edge_faces.items() if set(fs) == {a, b} for v, w in [tuple(e)]])
        need(common == expected, f"faces {a} and {b} meet outside their common edges")

    multi = sum(1 for c in shared.values() if c >= 2)
    return {
        "V": V, "E": E, "F": F, "genus": genus,
        "sides": sorted(len(c) for c in faces),
        "pairs_sharing_edges": len(shared),
        "pairs_sharing_2plus": multi,
        "not_convex": genus > 0 or multi > 0,
        "map": canonical_map([c[::-1] if flip[f] else c for f, c in enumerate(faces)]),
    }


def run_census(paths):
    maps, per_genus, bad = {}, Counter(), 0
    total = 0
    for path in paths:
        with open(path) as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                total += 1
                try:
                    r = check(d)
                    need(r["F"] == 8, "not 8 faces")
                    need(r["genus"] == d["genus"], f"genus {r['genus']} differs from the stated {d['genus']}")
                    need(r["not_convex"], "convex realisation not excluded")
                    need(r["map"] not in maps, f"same combinatorial type as {maps.get(r['map'])}")
                    maps[r["map"]] = d["key"]
                    per_genus[(r["genus"], r["V"], r["E"])] += 1
                except Invalid as e:
                    bad += 1
                    print(f"INVALID {d.get('key')}: {e}")
    for (g, v, e), n in sorted(per_genus.items()):
        print(f"genus {g}: {n} shapes ({v} vertices, {e} edges, 8 faces)")
    print(f"{total} shapes read, {total - bad} valid, {len(maps)} pairwise distinct combinatorial types, {bad} invalid")
    return bad == 0


def run_one(path, expect_invalid):
    d = json.load(open(path))
    path = os.path.basename(path)
    try:
        r = check(d)
        print(f"{path}: VALID, {r['F']} faces, {r['V']} vertices, {r['E']} edges, genus {r['genus']}, "
              f"{r['pairs_sharing_edges']} pairs of faces share an edge")
        return not expect_invalid
    except Invalid as e:
        print(f"{path}: INVALID ({e})")
        return expect_invalid


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--one":
        ok = run_one(args[1], "--expect-invalid" in args)
    else:
        ok = run_census(args)
    sys.exit(0 if ok else 1)
