try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import Grasshopper
except ImportError:
    raise ImportError('Grasshopper could not import.')

try:
    from System.Collections import IEnumerable
except ImportError:
    raise ImportError('System.Collections.IEnumerable could not import.')

def _unwrap(x):
    try:
        if x is None:
            return None
        if isinstance(x, Grasshopper.Kernel.Types.GH_ObjectWrapper):
            return x.Value
        if hasattr(x, "Value"):
            return _unwrap(x.Value)

        if isinstance(x, IEnumerable) and not isinstance(x, (str, bytes)):
            return [_unwrap(e) for e in x]
    except:
        pass
    return x

def _as_brep(x):
    x = _unwrap(x)
    if isinstance(x, rg.Brep): return x
    if isinstance(x, rg.Extrusion): return x.ToBrep()
    if isinstance(x, rg.Surface):  return rg.Brep.CreateFromSurface(x)
    return None

def _unwrap_point_list(x):
    _list = []
    for _x in x:
        _list.append((round(_x.X, 3), round(_x.Y, 3), round(_x.Z, 3)))
    return _list
