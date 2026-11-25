# 1,325 combinatorial types of 8-face polyhedra that cannot be convex

How many different shapes (combinatorial types) of polyhedra with 8 faces cannot be realised by
a convex polyhedron? M. Gardner (1983) quotes 277, with neither source nor definition;
B. Grünbaum ("Acoptic polyhedra", 1999) writes that he does not know what this number counts,
lists 17 non-convex types with 7 faces and poses the enumeration problem. This repository
contains one exact realisation of each of **1,325 pairwise different types with 8 faces**, found
by a computer search, and an independent exact verifier.

| Genus | Vertices | Edges | Types |
|---|---|---|---|
| 0 (no hole) | 12 | 18 | 13 |
| 1 (torus) | 16 | 24 | 973 |
| 2 | 20 | 30 | 339 |

> **Status.** Not checked by a third party; novelty not confirmed (unpublished or overlooked
> enumerations may exist). This is a **lower bound, not a complete count**: plane arrangements
> were sampled at random, and the setting is restricted (see below). In particular the two known
> 8-face polyhedra of genus 3 (Mizhaev; Röst and Vígh, 2026) were not reached by the sampling
> and are not among the 1,325. Every listed shape is checked by the program in `verification/`,
> which was written independently of the search. Corrections and pointers to prior work are
> welcome: please open an issue.

*Résumé en français : un exemple exact de chacune de 1 325 formes (types combinatoires)
différentes de polyèdres à 8 faces qui ne peuvent pas être convexes : 13 sans trou, 973 tores,
339 à deux trous, avec un vérificateur exact indépendant. C'est une borne inférieure obtenue par
échantillonnage, pas un décompte complet. Pas encore vérifié par un tiers ; nouveauté non
confirmée.*

Interactive figures (French): https://totocaedres.fransys.io/octaedres

## What is counted

- A *polyhedron* is a closed surface embedded in space (no self-intersection), made of 8 planar
  faces, each a simple polygon (not necessarily convex), each edge shared by exactly two faces.
- **Setting.** Exactly three faces meet at every vertex, and the 8 faces lie in 8 different
  planes. Shapes with vertices of higher degree, or with two faces in one plane, are not counted.
- The *type* of a polyhedron is its combinatorial map (vertices, edges, faces and their
  incidences), up to mirror image.
- A type *cannot be convex* when no convex polyhedron has it. This is clear for genus 1 and 2.
  Each of the 13 types of genus 0 has two faces sharing two or three edges, which is impossible
  for a convex polyhedron (two faces of a convex polyhedron share at most one edge).

Some observations:

- three tori have 8 hexagonal faces; in one of them (`5b99445f278c00ba1bda`) every face shares
  exactly one edge with 6 of the 7 others, and the 4 pairs of faces that do not touch form a
  perfect matching;
- 7 tori have no pair of faces sharing more than one edge; all types of genus 0 and 2 have one;
- the same search recovers all 14 convex types with 8 faces and three faces per vertex, which
  is the known number of simple polyhedra with 8 faces.

## Files

- `results/octahedra_genus0.jsonl`, `octahedra_genus1.jsonl`, `octahedra_genus2.jsonl` — one
  polyhedron per line (JSON), grouped by genus. Fields:
  - `key` — identifier of the type (arbitrary hash);
  - `genus`;
  - `planes` — the 8 planes `[a, b, c, d]` (integers), meaning `a x + b y + c z = d`; face `i`
    lies in plane `i`;
  - `vertices` — exact rational coordinates, as strings such as `"-47/43"`;
  - `faces` — for each face, the cyclic list of its vertices (0-indexed).
- `results/index.csv` — one row per type: key, genus, numbers of vertices and edges, numbers of
  sides of the 8 faces, number of pairs of faces sharing an edge, number of pairs sharing at
  least two edges.
- `verification/verify.py` — the verifier (Python 3, standard library only, rational arithmetic).
- `verification/controls/` — control cases; `verification/run_all.sh` runs everything.

## Verify

```bash
verification/run_all.sh
```

For each polyhedron, `verify.py` checks with exact arithmetic that:

1. every vertex of a face lies in the plane of that face, the 8 planes are distinct, and the
   three planes meeting at a vertex are independent;
2. every edge belongs to exactly two faces, every vertex to exactly three faces and three
   edges, the surface is connected and orientable;
3. every face is a simple polygon without flat corner;
4. any two faces intersect exactly along their common edges (for each pair, the traces of both
   faces on the line common to their planes are computed as unions of intervals and compared);
5. the genus computed from the Euler characteristic is the stated one, and there are 8 faces;
6. the type cannot be convex: genus at least 1, or two faces sharing at least two edges;
7. the 1,325 types are pairwise different (canonical form of the map, up to mirror image).

Output (about 25 s):

```
genus 0: 13 shapes (12 vertices, 18 edges, 8 faces)
genus 1: 973 shapes (16 vertices, 24 edges, 8 faces)
genus 2: 339 shapes (20 vertices, 30 edges, 8 faces)
1325 shapes read, 1325 valid, 1325 pairwise distinct combinatorial types, 0 invalid
mizhaev.json: VALID, 8 faces, 24 vertices, 36 edges, genus 3, 28 pairs of faces share an edge
rostvigh.json: VALID, 8 faces, 24 vertices, 36 edges, genus 3, 28 pairs of faces share an edge
szilassi.json: VALID, 7 faces, 14 vertices, 21 edges, genus 1, 21 pairs of faces share an edge
neg_razorcross.json: INVALID (faces 0 and 8 meet outside their common edges)
neg_swapped_vertices.json: INVALID (face 2: vertex 0 not in its plane)
ALL CHECKS PASS
```

Control cases and their sources (given by planes and vertex triples; vertices are recomputed):

- `mizhaev.json` — 8 faces, genus 3: R. Mizhaev, arXiv:2609.17700;
- `rostvigh.json` — 8 faces, genus 3: G. Röst and V. Vígh, arXiv:2609.32998;
- `szilassi.json` — Szilassi polyhedron, coordinates from Wikimedia Commons (CMG Lee);
- `neg_razorcross.json` — self-intersecting candidate from HackerPoet's NeighborlyPolyhedra
  (must be rejected);
- `neg_swapped_vertices.json` — a shape of the census with two vertices swapped (must be rejected).

The verifier does not prove that the list is complete, and it does not re-derive how the shapes
were found.

## Search method

Arrangements of 8 planes in general position with integer coefficients are drawn at
random, each combinatorial arrangement type being kept once. For each arrangement, all closed
surfaces that are the boundary of a union of bounded cells and have exactly one polygonal face
in each plane are enumerated and classified by type. The search code is not published; the data
and the verifier are sufficient to check every shape independently of it.

## Acknowledgements

The search and verification code was written with the help of Claude (Anthropic).

## Licence

Code: MIT (`LICENSE`). Data in `results/`: CC BY 4.0 (`LICENSE-DATA.md`).
