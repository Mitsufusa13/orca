import math
from orca.ghutil import _unwrap, _as_brep

try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import scriptcontext as sc
except ImportError:
    raise ImportError('scriptcontext could not import.')

def face_normal_outward(surface, brep):
    face = surface.Faces[0]
    u = face.Domain(0).Mid
    v = face.Domain(1).Mid
    pt = face.PointAt(u, v)
    n = face.NormalAt(u, v)
    amp = rg.AreaMassProperties.Compute(brep)
    cen = amp.Centroid
    to_out = pt - cen
    if n * to_out < 0:
        n.Reverse()
    return n

def split_brep(Target, Cutters, Tol=None):
    tol = float(Tol) if Tol is not None else 1e-6
    tgt = _as_brep(Target)
    if tgt is None or not tgt.IsValid:
        raise ValueError("Target には有効な Brep/Surface/Extrusion を渡してください。")
    planes, brep_cutters = [], []
    for c in (Cutters or []):
        c = _unwrap(c)
        if isinstance(c, rg.Plane):
            planes.append(c)
        else:
            b = _as_brep(c)
            if b and b.IsValid:
                brep_cutters.append(b)
    pieces = [tgt]
    for pl in planes:
        tmp = []
        for p in pieces:
            r = p.Split(pl, tol)
            tmp.extend(r or [p])
        pieces = tmp
    for cutter in brep_cutters:
        tmp = []
        for p in pieces:
            r = p.Split(cutter, tol)
            tmp.extend(r or [p])
        pieces = tmp
    return pieces

def join_breps(parts, Tol=None, cap=False, rebuild=False, merge=True):
    tol = float(Tol) if Tol is not None else 1e-6

    breps = []
    for x in (parts or []):
        b = _as_brep(x)
        if b and b.IsValid:
            if cap:
                b_cap = rg.Brep.CapPlanarHoles(b, tol)
                if b_cap: b = b_cap
            if rebuild:
                b.RebuildEdges(tol, True, True)
            breps.append(b)

    if not breps:
        return [], [], "No valid Breps."

    joined = rg.Brep.JoinBreps(breps, tol)
    retried = False
    if not joined or len(joined) == len(breps):
        joined = rg.Brep.JoinBreps(breps, tol * 10.0) or breps
        retried = True

    out = []
    for b in joined:
        if merge:
            b.MergeCoplanarFaces(tol)
        out.append(b)

    naked = []
    for b in out:
        for c in b.DuplicateNakedEdgeCurves(True, True):
            if c and c.GetLength() > tol * 0.5:
                naked.append(c)

    msg = "Input: {} → Joined: {}{}".format(
        len(breps), len(out), " (retry tol*10)" if retried else ""
    )
    return out

def centroid_of_brep(brep):
    if brep is None:
        return None
    amp = rg.AreaMassProperties.Compute(brep)
    if amp is None:
        return None
    return amp.Centroid

def min_z_of_brep_vertices(brep):
    if brep is None or brep.Vertices is None or brep.Vertices.Count == 0:
        return None
    min_z = None
    for v in brep.Vertices:
        z = v.Location.Z
        min_z = z if (min_z is None or z < min_z) else min_z
    return min_z

def center_xy_from_centroids(centroids):
    if not centroids:
        return None
    sx = sy = 0.0
    n = 0
    for c in centroids:
        if c is None:
            continue
        sx += c.X
        sy += c.Y
        n += 1
    if n == 0:
        return None
    return rg.Point3d(sx / n, sy / n, 0.0)

def angle_ccw_from_ref_xy_vec(vec, ref_vec):
    if vec is None or ref_vec is None:
        return 0.0

    v = rg.Vector3d(vec.X, vec.Y, 0.0)
    r = rg.Vector3d(ref_vec.X, ref_vec.Y, 0.0)

    if v.IsTiny():
        return 0.0

    v.Unitize()
    if r.IsTiny():
        r = rg.Vector3d(0, -1, 0)
    r.Unitize()

    cross_z = r.X * v.Y - r.Y * v.X
    dot = r.X * v.X + r.Y * v.Y
    ang = math.atan2(cross_z, dot)
    if ang < 0.0:
        ang += 2.0 * math.pi
    return ang

def face_mid_normal(face):
    if face is None:
        return None
    udom = face.Domain(0)
    vdom = face.Domain(1)
    u = 0.5 * (udom.T0 + udom.T1)
    v = 0.5 * (vdom.T0 + vdom.T1)

    n = face.NormalAt(u, v)
    if (not n.IsValid) or n.IsTiny():
        u = udom.T0 + 0.37 * (udom.T1 - udom.T0)
        v = vdom.T0 + 0.61 * (vdom.T1 - vdom.T0)
        n = face.NormalAt(u, v)

    if (not n.IsValid) or n.IsTiny():
        return None
    n.Unitize()
    return n

def sort_roof_floor_by_centroid(face_breps):
    items = []
    for fb in face_breps or []:
        c = centroid_of_brep(fb)
        if c is None:
            continue
        items.append((fb, c))

    items_sorted = sorted(items, key=lambda t: (-t[1].Z, t[1].X, t[1].Y))
    return [t[0] for t in items_sorted]


def sort_walls_from_closed_brep(brep, tol_deg=5.0, ref_vec=None):
    if brep is None:
        return []

    tol = math.sin(math.radians(tol_deg))
    ref = ref_vec if ref_vec is not None else rg.Vector3d(0, -1, 0)
    if ref.IsTiny():
        ref = rg.Vector3d(0, -1, 0)
    ref.Unitize()

    tmp = []
    for f in brep.Faces:
        n = face_mid_normal(f)
        if n is None:
            continue

        if abs(n.Z) > tol:
            continue

        fb = f.DuplicateFace(True)
        if not fb:
            continue

        minZ = min_z_of_brep_vertices(fb)
        if minZ is None:
            continue

        c = centroid_of_brep(fb)
        if c is None:
            continue

        tmp.append((fb, minZ, c))

    center_xy = center_xy_from_centroids([t[2] for t in tmp])
    if center_xy is None:
        return [t[0] for t in tmp]

    walls = []
    for fb, minZ, c in tmp:
        vec = rg.Vector3d(c.X - center_xy.X, c.Y - center_xy.Y, 0.0)
        ang = angle_ccw_from_ref_xy_vec(vec, ref)
        r2 = vec.X * vec.X + vec.Y * vec.Y
        walls.append((fb, minZ, ang, r2))

    items_sorted = sorted(walls, key=lambda t: (-t[1], t[2], t[3]))
    return [t[0] for t in items_sorted]


def sort_walls_from_face_breps(face_breps, tol_deg=5.0, ref_vec=None):
    if not face_breps:
        return []

    ref = ref_vec if ref_vec is not None else rg.Vector3d(0, -1, 0)
    if ref.IsTiny():
        ref = rg.Vector3d(0, -1, 0)
    ref.Unitize()

    tmp = []
    for fb in face_breps:
        if fb is None:
            continue
        minZ = min_z_of_brep_vertices(fb)
        c = centroid_of_brep(fb)
        if minZ is None or c is None:
            continue
        tmp.append((fb, minZ, c))

    center_xy = center_xy_from_centroids([t[2] for t in tmp])
    if center_xy is None:
        return [t[0] for t in tmp]

    walls = []
    for fb, minZ, c in tmp:
        vec = rg.Vector3d(c.X - center_xy.X, c.Y - center_xy.Y, 0.0)
        ang = angle_ccw_from_ref_xy_vec(vec, ref)
        r2 = vec.X * vec.X + vec.Y * vec.Y
        walls.append((fb, minZ, ang, r2))

    items_sorted = sorted(walls, key=lambda t: (-t[1], t[2], t[3]))
    return [t[0] for t in items_sorted]

def round_point3d(point, digits=6):
    X = round(point.X, digits)
    Y = round(point.Y, digits)
    Z = round(point.Z, digits)
    return rg.Point3d(X, Y, Z)

def round_vector3d(vector, digits=6):
    X = round(vector.X, digits)
    Y = round(vector.Y, digits)
    Z = round(vector.Z, digits)
    return rg.Vector3d(X, Y, Z)
