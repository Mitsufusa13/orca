import copy
from orca.brepnormalize import round_point3d, round_vector3d

try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import scriptcontext as sc
except ImportError:
    raise ImportError('scriptcontext could not import.')

Tol = 1e-6

class Shading:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Transmittance_Schedule_Name': None,
            'Number_of_Vertices': None,
        }

        self.__geometry = {
            'Surface': None,
        }

        self.__geometry_properties = {
            'Area': None,
            'Centroid': None,
            'Normal': None,
        }

        self.__vertices = None
    
    def properties(self):
        return self.__properties
    
    def geometry(self):
        return self.__geometry
    
    def geometry_properties(self):
        return self.__geometry_properties
    
    def name(self):
        return self.__properties['Name']
    
    def surfacebrep(self):
        return self.__geometry['Surface']
    
    def vertices(self):
        return self.__vertices
    
    def set_name(self, name):
        self.__properties['Name'] = str(name)
    
    def set_surfacebrep(self, surfacebrep):
        if type(surfacebrep) != rg.Brep:
            raise TypeError('Unexpected Brep exists.')
        else:
            self.__geometry['Surface'] = surfacebrep

        self.__geometry_properties['Area'] = round(rg.AreaMassProperties.Compute(surfacebrep).Area, 6)
        self.__geometry_properties['Centroid'] = round_point3d(rg.AreaMassProperties.Compute(surfacebrep).Centroid)
        self.__geometry_properties['Normal'] = self.set_normal()

        self.set_vertices()
    
    def set_vertices(self):
        _vertices = []
        face = self.surfacebrep().Faces[0]
        n = self.geometry_properties()['Normal']
        c = self.geometry_properties()['Centroid']
        vertices = set()
        trims = face.OuterLoop.Trims
        for i,t in enumerate(trims):
            vertices.add(round_point3d(t.Edge.StartVertex.Location))
            vertices.add(round_point3d(t.Edge.EndVertex.Location))
        def make_local_axes(n):
            world_z = rg.Vector3d(0, 0, 1)
            if abs(n * world_z) > 0.9:
                world_z = rg.Vector3d(0, 1, 0)
            u = rg.Vector3d.CrossProduct(world_z, n)
            u.Unitize()
            v = rg.Vector3d.CrossProduct(n, u)
            v.Unitize()
            return u, v, n
        def project_to_local(vtx, origin, u, v):
            rel = rg.Vector3d(vtx - origin)
            return rel * u, rel * v
        def key(vtx, origin, u, v):
            ucoord, vcoord = project_to_local(vtx, origin, u, v)
            return (-vcoord, ucoord)
        u, v, _ = make_local_axes(n)
        vertices = sorted(list(vertices), key=lambda vv: key(vv, c, u, v))
        p0 = vertices[0]
        vertices.remove(p0)
        _vertices.append(p0)

        neighbor_vertices = []
        for t in trims:
            if round_point3d(t.Edge.StartVertex.Location) == p0:
                neighbor_vertices.append(round_point3d(t.Edge.EndVertex.Location))
            elif round_point3d(t.Edge.EndVertex.Location) == p0:
                neighbor_vertices.append(round_point3d(t.Edge.StartVertex.Location))
            else:
                pass
        p1 = neighbor_vertices[0] if len(neighbor_vertices) > 0 else None
        p2 = neighbor_vertices[1] if len(neighbor_vertices) > 1 else None
        vA = round_vector3d(rg.Vector3d(p1-p0))
        vA.Unitize()
        _vA = rg.Vector3d.CrossProduct(n, vA)
        _vA.Unitize()
        _p1 = p0 + (vA + _vA + (-1*n)) * 0.001
        vB = round_vector3d(rg.Vector3d(p2-p0))
        vB.Unitize()
        _vB = rg.Vector3d.CrossProduct(n, vB)
        _vB.Unitize()
        _p2 = p0 + (vB + _vB + (-1*n)) * 0.001
        solid = rg.Brep.CreateFromOffsetFace(face, -1, Tol, False, True)
        if solid.SolidOrientation == rg.BrepSolidOrientation.Inward:
            solid.Flip()
        self.solid = solid
        if solid.IsPointInside(_p1, 1e-6, True):
            p0 = p1
        elif solid.IsPointInside(_p2, 1e-6, True):
            p0 = p2
        else:
            raise ValueError('')
        try:
            vertices.remove(p0)
            _vertices.append(p0)
        except:
            pass
        ITER_MAX = 50
        n = 0
        while len(vertices) != 0 and n <= ITER_MAX:
            for t in trims:
                n += 1
                s = round_point3d(t.Edge.StartVertex.Location)
                e = round_point3d(t.Edge.EndVertex.Location)
                if s == p0 and e in vertices:
                    p0 = e
                    vertices.remove(p0)
                    _vertices.append(p0)   
                elif e == p0 and s in vertices:
                    p0 = s
                    vertices.remove(p0)
                    _vertices.append(p0)
                elif n == ITER_MAX:
                    _vertices_ = copy.copy(vertices)
                    for v in _vertices_:
                        vertices.remove(v)
                        _vertices.append(v)
                else:
                    continue
        new_vertices = []
        new_vertices.append(_vertices[0])
        _vertices.append(_vertices[0])
        for i in range(len(_vertices[:len(_vertices)-2])):
            _p0 = _vertices[i]
            _p1 = _vertices[i+1]
            _p2 = _vertices[i+2]
            _v1 = _p1 - _p0
            _v1.Unitize()
            _v2 = _p2 - _p1
            _v2.Unitize()
            dot = _v1 * _v2
            if dot <= 1 - Tol:
                new_vertices.append(_p1)
        _vertices = new_vertices

        _vertices = [v.Location if isinstance(v,rg.BrepVertex) else v for v in _vertices]
        self.__vertices = [round_point3d(v) for v in _vertices]

        self.properties()['Number_of_Vertices'] = len(self.vertices())

        for i, vertex in enumerate(self.vertices()):
            self.properties()[f'Vertex_{i+1}_X-coordinate'] = vertex.X
            self.properties()[f'Vertex_{i+1}_Y-coordinate'] = vertex.Y
            self.properties()[f'Vertex_{i+1}_Z-coordinate'] = vertex.Z
    
    def set_normal(self):
        face = self.surfacebrep().Faces[0]
        u = face.Domain(0).Mid
        v = face.Domain(1).Mid
        n = face.NormalAt(u, v)
        return round_vector3d(n)
    
    def set_transmittance(self, transmittance):
        self.__properties['Transmittance_Schedule_Name'] = transmittance
    
    def update_surfacebrep(self, surfacebrep):
        if type(surfacebrep) != rg.Brep:
            raise TypeError('Unexpected Brep exists.')
        else:
            self.__geometry['Surface'] = surfacebrep

        self.__geometry_properties['Area'] = round(rg.AreaMassProperties.Compute(surfacebrep).Area, 6)
        self.__geometry_properties['Centroid'] = round_point3d(rg.AreaMassProperties.Compute(surfacebrep).Centroid)
        self.__geometry_properties['Normal'] = self.set_normal()

        self.set_vertices()

    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'SHADING:BUILDING:DETAILED',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_shading = Shading()
        duplicate_shading.update_surfacebrep(self.surfacebrep())
        duplicate_shading.update_properties(self.properties())
        return duplicate_shading
