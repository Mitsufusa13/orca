import math
from orca import brepnormalize
from orca.brepnormalize import round_point3d, round_vector3d

try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import scriptcontext as sc
except ImportError:
    raise ImportError('scriptcontext could not import.')

Tol = sc.doc.ModelAbsoluteTolerance

def create_zone_brep(reference_point, width, depth, height):
    p0 = reference_point
    p1 = p0 + rg.Point3d(width, 0, 0)
    p2 = p0 + rg.Point3d(width, depth, 0)
    p3 = p0 + rg.Point3d(0, depth, 0)
    Bottom = rg.NurbsSurface.CreateFromCorners(p0, p1, p2, p3)
    brep_tmp = Bottom.ToBrep()
    edge_crvs = list(brep_tmp.DuplicateEdgeCurves(True))
    profile_joined = rg.Curve.JoinCurves(edge_crvs, 1e-6)
    profile = profile_joined[0]
    Extr = rg.Extrusion.Create(profile, height, True)
    zone_brep = Extr.ToBrep()
    return zone_brep, [p0, p1, p2, p3]

def create_attic_zone_brep(zone_breps, roof_brep, AngTol=10e-6):
    if len(zone_breps) > 1:
        zone_brep = rg.Brep.CreateBooleanUnion(zone_breps, Tol)[0]
    else:
        zone_brep = zone_breps[0]
    maximum_height = 0
    for i in range(zone_brep.Faces.Count):
        face = zone_brep.Faces[i].DuplicateFace(True)
        centroid = rg.AreaMassProperties.Compute(face).Centroid.Z
        maximum_height = max(maximum_height, centroid)
    extrude_breps = []
    for i in range(zone_brep.Faces.Count):
        face = zone_brep.Faces[i].DuplicateFace(True)
        normal = brepnormalize.face_normal_outward(face, zone_brep)
        if normal.Z >= (1-AngTol):
            if rg.AreaMassProperties.Compute(face).Centroid.Z >= maximum_height:
                extrude_breps.append(face)
    extruded_breps = []
    for extrude_brep in extrude_breps:
        edge_crvs = list(extrude_brep.DuplicateEdgeCurves(True))
        profile_joined = rg.Curve.JoinCurves(edge_crvs, 1e-6)
        profile = profile_joined[0]
        Extr = rg.Extrusion.Create(profile, 10, True).ToBrep()
        extruded_breps.append(Extr)
    if len(extruded_breps) == 0:
        pass
    splited_breps = []
    for extrude_brep in extruded_breps:
        splited_brep = brepnormalize.split_brep(extrude_brep, [roof_brep])
        try:
            if splited_brep[0].CapPlanarHoles(Tol) is None:
                splited_brep1 = rg.Brep.CreateBooleanIntersection(splited_brep[0], roof_brep, Tol)[0]
            else:    
                splited_brep1 = splited_brep[0].CapPlanarHoles(Tol)
        except Exception:
            splited_brep1 = splited_brep[0]
        try:
            if splited_brep[1].CapPlanarHoles(Tol) is None:
                splited_brep2 = rg.Brep.CreateBooleanIntersection(splited_brep[1], roof_brep, Tol)[0]
            else:    
                splited_brep2 = splited_brep[1].CapPlanarHoles(Tol)
        except Exception:
            splited_brep2 = splited_brep[1]
        if rg.AreaMassProperties.Compute(splited_brep1).Centroid.Z > rg.AreaMassProperties.Compute(splited_brep2).Centroid.Z:
            splited_breps.append(splited_brep2)
        else:
            splited_breps.append(splited_brep1)
    if len(extruded_breps) == 0:
        pass
    attic_brep = splited_breps[0]
    breps = [zone_brep] + splited_breps
    joined_brep = rg.Brep.CreateBooleanUnion(breps, Tol)[0]
    return zone_brep , attic_brep, joined_brep

def create_window(wall, anchor, width, height, windowreference, offsetX, offsetY, margin):
    wall_brep_face = wall
    plane = face_plane(wall_brep_face)

    crv3d = face_outerloop_curve(wall_brep_face)
    xmin, xmax, ymin, ymax = curve_bbox_in_plane(crv3d, plane)
    xmin_safe, xmax_safe, ymin_safe, ymax_safe, used_margin = apply_margins_with_auto_clamp(
        xmin, xmax, ymin, ymax, margin
    )

    vtag, htag = [s.strip() for s in anchor.split(',')]
    xw = pick_from3('h', htag, xmin_safe, xmax_safe)
    yw = pick_from3('v', vtag, ymin_safe, ymax_safe)

    Px = xw + offsetX
    Py = yw + offsetY

    vref, href = [s.strip() for s in windowreference.split(',')]
    x0, x1, y0, y1 = rect_from_anchor(Px, Py, width, height, href, vref)

    x0, x1, y0, y1, scale_used = clamp_rect_with_autoshrink(x0, x1, y0, y1, xmin_safe, xmax_safe, ymin_safe, ymax_safe)

    if scale_used < 1.0:
        print("⚠️ Window auto-shrunk to {:.1f}% of original size to fit wall.".format(scale_used * 100))

    window_brep = plane_rect_surface(plane, x0, x1, y0, y1)

    face = wall_brep_face.Faces[0]
    uu = 0.5*(x0+x1); vv = 0.5*(y0+y1)
    p3d = plane.PointAt(uu, vv)

    ok, fu, fv = face.ClosestPoint(p3d)
    if not ok:
        fu = face.Domain(0).Mid
        fv = face.Domain(1).Mid

    n_wall = face.NormalAt(fu, fv); n_wall.Unitize()

    srf = window_brep.Faces[0]
    mu = srf.Domain(0).Mid; mv = srf.Domain(1).Mid
    n_win = srf.NormalAt(mu, mv); n_win.Unitize()
    if n_wall * n_win < 0:
        srf = srf.DuplicateFace(False)
        srf.Flip()
        window_brep = srf.ToBrep()

    return window_brep, wall_brep_face

def create_window_wwr(wall, anchor, wwr, windowreference, offsetX, offsetY, margin):
    wall_brep_face = wall
    plane = face_plane(wall_brep_face)

    crv3d = face_outerloop_curve(wall_brep_face)
    xmin, xmax, ymin, ymax = curve_bbox_in_plane(crv3d, plane)
    xmin_safe, xmax_safe, ymin_safe, ymax_safe, used_margin = apply_margins_with_auto_clamp(
        xmin, xmax, ymin, ymax, margin
    )

    wall_width, wall_height = xmax - xmin, ymax - ymin
    _wwr = math.sqrt(wwr)
    width, height = _wwr * wall_width, _wwr * wall_height

    vtag, htag = [s.strip() for s in anchor.split(',')]
    xw = pick_from3('h', htag, xmin_safe, xmax_safe)
    yw = pick_from3('v', vtag, ymin_safe, ymax_safe)

    Px = xw + offsetX
    Py = yw + offsetY

    vref, href = [s.strip() for s in windowreference.split(',')]
    x0, x1, y0, y1 = rect_from_anchor(Px, Py, width, height, href, vref)

    x0, x1, y0, y1, scale_used = clamp_rect_with_autoshrink(x0, x1, y0, y1, xmin_safe, xmax_safe, ymin_safe, ymax_safe)

    if scale_used < 1.0:
        print("⚠️ Window auto-shrunk to {:.1f}% of original size to fit wall.".format(scale_used * 100))

    window_brep = plane_rect_surface(plane, x0, x1, y0, y1)

    face = wall_brep_face.Faces[0]
    uu = 0.5*(x0+x1); vv = 0.5*(y0+y1)
    p3d = plane.PointAt(uu, vv)

    ok, fu, fv = face.ClosestPoint(p3d)
    if not ok:
        fu = face.Domain(0).Mid
        fv = face.Domain(1).Mid

    n_wall = face.NormalAt(fu, fv); n_wall.Unitize()

    srf = window_brep.Faces[0]
    mu = srf.Domain(0).Mid; mv = srf.Domain(1).Mid
    n_win = srf.NormalAt(mu, mv); n_win.Unitize()
    if n_wall * n_win < 0:
        srf = srf.DuplicateFace(False)
        srf.Flip()
        window_brep = srf.ToBrep()

    return window_brep, wall_brep_face

def anchor_check(anchor):
    _anchor = anchor.replace(' ', '').split(',')
    vertical = ['top', 'center', 'bottom']
    horizontal = ['left', 'center', 'right']
    if _anchor[0] not in vertical:
        raise ValueError(f'Vertical reference must be one of the following in {vertical}.')
    if _anchor[1] not in horizontal:
        raise ValueError(f'Horizontal reference must be one of the following in {horizontal}.')
    return anchor

def face_plane(face_brep):
    face = face_brep.Faces[0] if isinstance(face_brep, rg.Brep) else face_brep
    ok, pl = face.TryGetPlane()
    if not ok:
        raise ValueError("Wall face is not planar.")
    return pl

def brep_vertices_2d(face_brep, plane):
    if not isinstance(face_brep, rg.Brep):
        face_brep = face_brep.ToBrep()
    pts2 = []
    for v in face_brep.Vertices:
        u,vv,_ = plane.ClosestParameter(v.Location)
        pts2.append(rg.Point2d(u, vv))
    return pts2

def face_outerloop_curve(face_brep):
    face = face_brep.Faces[0] if isinstance(face_brep, rg.Brep) else face_brep
    loop = face.OuterLoop
    crv3d = loop.To3dCurve()
    return crv3d

def curve_bbox_in_plane(curve3d, plane, tol=1e-3, angle_tol=math.radians(2.0)):
    plc = curve3d.ToPolyline(tol, angle_tol, 0, 0)
    if plc is not None:
        ok, poly = plc.TryGetPolyline()
        if ok and poly is not None and poly.Count >= 2:
            pts = [poly[i] for i in range(poly.Count)]
        else:
            pts = [plc.Point(i) for i in range(plc.PointCount)]
    else:
        t0, t1 = curve3d.Domain.T0, curve3d.Domain.T1
        ts = [t0 + (t1 - t0) * i / 100.0 for i in range(101)]
        pts = [curve3d.PointAt(t) for t in ts]

    us, vs = [], []
    for pt in pts:
        ok, uu, vv = plane.ClosestParameter(pt)
        if ok:
            us.append(uu)
            vs.append(vv)

    if not us or not vs:
        raise ValueError("Failed to compute plane-local bbox for wall face.")

    return min(us), max(us), min(vs), max(vs)

def apply_margins_with_auto_clamp(xmin, xmax, ymin, ymax, margin):
    w = xmax - xmin
    h = ymax - ymin
    if w <= 0 or h <= 0:
        raise ValueError("Wall face 2D bounding box has zero or negative size.")

    max_margin = max(0.0, min(margin, w * 0.5 - 1e-9, h * 0.5 - 1e-9))

    used = max(0.0, max_margin)
    xmin_s = xmin + used
    xmax_s = xmax - used
    ymin_s = ymin + used
    ymax_s = ymax - used

    if xmin_s >= xmax_s or ymin_s >= ymax_s:
        eps = 1e-9
        cx = 0.5 * (xmin + xmax)
        cy = 0.5 * (ymin + ymax)
        xmin_s, xmax_s = cx - eps, cx + eps
        ymin_s, ymax_s = cy - eps, cy + eps

    return xmin_s, xmax_s, ymin_s, ymax_s, used

def bbox2d(pts2):
    xs = [p.X for p in pts2]
    ys = [p.Y for p in pts2]
    return min(xs), max(xs), min(ys), max(ys)

def pick_from3(axis, where, mn, mx):
    if where == 'left' or where == 'bottom':
        return mn
    if where == 'center':
        return 0.5*(mn+mx)
    if where == 'right' or where == 'top':
        return mx
    raise ValueError("anchor keyword error")

def rect_from_anchor(Px, Py, W, H, href, vref):
    if href == 'left':
        x0, x1 = Px, Px + W
    elif href == 'center':
        x0, x1 = Px - W*0.5, Px + W*0.5
    elif href == 'right':
        x0, x1 = Px - W, Px
    else:
        raise ValueError("win horizontal ref")
    if vref == 'bottom':
        y0, y1 = Py, Py + H
    elif vref == 'center':
        y0, y1 = Py - H*0.5, Py + H*0.5
    elif vref == 'top':
        y0, y1 = Py - H, Py
    else:
        raise ValueError("win vertical ref")
    return x0, x1, y0, y1

def clamp_rect_with_autoshrink(x0, x1, y0, y1, xmin, xmax, ymin, ymax):
    w = x1 - x0
    h = y1 - y0
    safe_w = xmax - xmin
    safe_h = ymax - ymin

    if safe_w <= 0 or safe_h <= 0:
        raise ValueError("Safe area is invalid (too small or negative).")

    scale = min(1.0, safe_w / w, safe_h / h)
    if scale < 1.0:
        cx = (x0 + x1) * 0.5
        cy = (y0 + y1) * 0.5
        w *= scale
        h *= scale
        x0 = cx - w * 0.5
        x1 = cx + w * 0.5
        y0 = cy - h * 0.5
        y1 = cy + h * 0.5

    if x0 < xmin:
        d = xmin - x0; x0 += d; x1 += d
    if x1 > xmax:
        d = xmax - x1; x0 += d; x1 += d
    if y0 < ymin:
        d = ymin - y0; y0 += d; y1 += d
    if y1 > ymax:
        d = ymax - y1; y0 += d; y1 += d

    return x0, x1, y0, y1, scale

def plane_rect_surface(plane, x0, x1, y0, y1):
    dom_u = rg.Interval(x0, x1)
    dom_v = rg.Interval(y0, y1)
    srf = rg.PlaneSurface(plane, dom_u, dom_v)
    return srf.ToBrep()

def read_anchor_point(face_brep, anchor, centroid, normal):
    anchor = anchor.replace(' ', '').split(',')
    if not isinstance(face_brep, rg.Brep):
        face_brep = face_brep.ToBrep()
    _vertices = [v.Location for v in face_brep.Vertices]

    def make_local_axes(n):
        world_z = rg.Vector3d(0, 0, 1)
        if abs(n * world_z) > 0.9:
            world_z = rg.Vector3d(0, 1, 0)
        u = rg.Vector3d.CrossProduct(world_z, n); u.Unitize()
        v = rg.Vector3d.CrossProduct(n, u); v.Unitize()
        return u, v, n

    def project_to_local(vtx, origin, u, v):
        rel = rg.Vector3d(vtx - origin)
        return rel * u, rel * v

    u, v, _ = make_local_axes(normal)

    def key_top_left(pt):      uu,vv = project_to_local(pt, centroid, u, v); return (-vv,  uu)
    def key_top_right(pt):     uu,vv = project_to_local(pt, centroid, u, v); return (-vv, -uu)
    def key_bottom_left(pt):   uu,vv = project_to_local(pt, centroid, u, v); return ( vv,  uu)
    def key_bottom_right(pt):  uu,vv = project_to_local(pt, centroid, u, v); return ( vv, -uu)

    top_left     = sorted(_vertices, key=key_top_left)[0]
    top_right    = sorted(_vertices, key=key_top_right)[0]
    bottom_left  = sorted(_vertices, key=key_bottom_left)[0]
    bottom_right = sorted(_vertices, key=key_bottom_right)[0]

    center_left   = (top_left+bottom_left) / 2
    center_right  = (top_right+bottom_right) / 2
    top_center    = (top_left+top_right) / 2
    bottom_center = (bottom_left+bottom_right) / 2

    h_vector = bottom_right - bottom_left; face_width = round(h_vector.Length, 3); h_vector.Unitize()
    v_vector = top_left - bottom_left;     face_height= round(v_vector.Length, 3); v_vector.Unitize()

    anchor_dict = {
        'top':{
            'right':  top_right,
            'center': top_center,
            'left':   top_left,
        },
        'center':{
            'right':  center_right,
            'center': centroid,
            'left':   center_left,
        },
        'bottom':{
            'right':  bottom_right,
            'center': bottom_center,
            'left':   bottom_left,
        }
    }
    anchor_point = anchor_dict[anchor[0]][anchor[1]]
    return anchor_point, h_vector, v_vector, face_width, face_height

def create_roof(reference_point, width, depth, rad, eave_length_px=0, eave_length_mx=0, eave_length_py=0, eave_length_my=0):
    _depth = round(depth/2, 3)
    _deg = math.atan(rad)
    _grad_vector1 = round_vector3d(rg.Vector3d(0, 1, _deg))
    _grad_vector2 = round_vector3d(rg.Vector3d(0, 1, -1*_deg))
    _hori_vector1 =  round_vector3d(rg.Vector3d(1, 0, 0))
    _hori_vector2 =  round_vector3d(rg.Vector3d(-1, 0, 0))

    # under minus x
    p0 = round_point3d(reference_point)
    p1 = round_point3d(p0 + rg.Point3d(width, 0, 0))

    # top
    p2 = round_point3d(p1 + _grad_vector1 * _depth)
    p3 = round_point3d(p0 + _grad_vector1 * _depth)

    # under plus x
    p4 = round_point3d(p2 + _grad_vector2 * (depth-_depth))
    p5 = round_point3d(p3 + _grad_vector2 * (depth-_depth))

    s1 = rg.NurbsSurface.CreateFromCorners(p0, p1, p2, p3).ToBrep()
    s2 = rg.NurbsSurface.CreateFromCorners(p3, p2, p4, p5).ToBrep()
    roof_brep = rg.Brep.JoinBreps([s1, s2], Tol)[0]
    center_point = (p0 + p1 + p4 + p5) / 4

    eave_breps = []
    p0s = [
        round_point3d(p0+_grad_vector1*eave_length_my*(-1)),
        round_point3d(p0+_grad_vector1*eave_length_my*(-1)+_hori_vector2*eave_length_mx),
        round_point3d(p1+_grad_vector1*eave_length_my*(-1)),
        p5,
        round_point3d(p3+_hori_vector2*eave_length_mx),
        p2,
    ]
    p1s = [
        round_point3d(p1+_grad_vector1*eave_length_my*(-1)),
        round_point3d(p0+_grad_vector1*eave_length_my*(-1)),
        round_point3d(p1+_grad_vector1*eave_length_my*(-1)+_hori_vector1*eave_length_px),
        p4,
        p3,
        round_point3d(p2+_hori_vector1*eave_length_px),
    ]
    p2s = [
        p1,
        p3,
        round_point3d(p2+_hori_vector1*eave_length_px),
        round_point3d(p4+_grad_vector2*eave_length_py),
        round_point3d(p5+_grad_vector2*eave_length_py),
        round_point3d(p4+_grad_vector2*eave_length_py+_hori_vector1*eave_length_px),
    ]
    p3s = [
        p0,
        round_point3d(p3+_hori_vector2*eave_length_mx),
        p2,
        round_point3d(p5+_grad_vector2*eave_length_py),
        round_point3d(p5+_grad_vector2*eave_length_py+_hori_vector2*eave_length_mx),
        round_point3d(p4+_grad_vector2*eave_length_py),
    ]
    for _p0, _p1, _p2, _p3 in zip(p0s, p1s, p2s, p3s):
        try:
            EaveBrep = rg.NurbsSurface.CreateFromCorners(_p0, _p1, _p2, _p3).ToBrep()
            eave_breps.append(EaveBrep)
        except Exception:
            pass
    all_breps = [roof_brep]
    for eave_brep in eave_breps:
        all_breps.append(eave_brep)
    joined = rg.Brep.JoinBreps(all_breps, Tol)
    return roof_brep, eave_breps, joined, center_point

def search_wall_brep(self, zonebrep):
    return 
