import copy
import math
from orca import brepnormalize
from orca.brepnormalize import round_point3d, round_vector3d
from orca import zonehvac_ideal_loads_air_system as hvac

try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import scriptcontext as sc
except ImportError:
    raise ImportError('scriptcontext could not import.')

Tol = 1e-6

class Zone:
    def __init__(self, zone_name):
        self.__properties = {
            'Name': zone_name,
            'Direction_of_Relative_North': '0',
            'X_Origin': '0',
            'Y_Origin': '0',
            'Z_Origin': '0',
            'Type': '1',
            'Multiplier': '1',
            'Ceiling_Height': None,
            'Volume': None,
            'Floor_Area': None,
            'Zone_Inside_Convection_Algorithm': None,
            'Zone_Outside_Convection_Algorithm': None,
            'Part_of_Total_Floor_Area': 'Yes',
        }

        self.__geometries = {
            'Zone': None,
            'Surfaces': {
                'Wall': [],
                'Roof': [],
                'Floor': [],
            },
        }

        self.__tol = 1e-9
        self.__z_up_threshold = 0.70710678

        self.__conditions = {
            'People': None,
            'Lights': None,
            'ElectricEquipment': None,
            'Infiltration': None,
        }

        self.__hvac = {
            'EquipmentList': None,
            'EquipmentConnections': None,
            'ZoneHVAC': None,
            'ZoneControlHumidistat': None,
            'ZoneControlThermostat': None,
            'ThermostatSetpointDual': None,
        }
        
    def properties(self):
        return self.__properties
    
    def geometries(self):
        return self.__geometries
    
    def name(self):
        return self.__properties['Name']
    
    def zonebrep(self):
        return self.__geometries['Zone']
    
    def surfaces(self):
        return self.__geometries['Surfaces']
    
    def set_zonebrep(self, zonebrep):
        if type(zonebrep) == rg.Brep and zonebrep.IsSolid:
            self.__geometries['Zone'] = zonebrep
        else:
            raise TypeError(f'ZoneBrep type must be ClosedBrep. Type:{type(zonebrep)} IsSolid:{zonebrep.IsSolid}')
    
    def set_zonesurfaces(self):
        brep = self.zonebrep()

        if brep is None:
            raise ValueError('ZoneBrep is not set.')
        
        geometries = {
            'Roof': [],
            'Floor': [],
            'Wall': [],
        }
        
        self.__geometries['Surfaces']['Wall'] = []
        self.__geometries['Surfaces']['Roof'] = []
        self.__geometries['Surfaces']['Floor'] = []

        b = brep.DuplicateBrep()

        key_num = {
            'Roof': 1,
            'Floor': 1,
            'Wall': 1,
        }

        for fi in range(b.Faces.Count):
            face = b.Faces[fi]

            udom = face.Domain(0)
            vdom = face.Domain(1)
            u = 0.5 * (udom.T0 + udom.T1)
            v = 0.5 * (vdom.T0 + vdom.T1)

            n = face.NormalAt(u, v)
            if not n.IsValid or n.IsZero:
                u = udom.T0 + 0.37 * (udom.T1 - udom.T0)
                v = vdom.T0 + 0.61 * (vdom.T1 - vdom.T0)
                n = face.NormalAt(u, v)

            if not n.IsValid or n.IsZero:
                continue

            n.Unitize()
            z = n.Z

            if z >= self.__z_up_threshold:
                key = 'Roof'
            elif z <= -self.__z_up_threshold:
                key = 'Floor'
            else:
                key = 'Wall'

            face_brep = face.DuplicateFace(True)
            geometries[key].append(face_brep)
            
        geometries['Wall']  = brepnormalize.sort_walls_from_face_breps(geometries['Wall'], tol_deg=5.0)
        geometries['Roof']  = brepnormalize.sort_roof_floor_by_centroid(geometries['Roof'])
        geometries['Floor'] = brepnormalize.sort_roof_floor_by_centroid(geometries['Floor'])

        for key in geometries:
            face_breps = geometries[key]
            for face_brep in face_breps:
                _surface = Surface(self.name())
                _surface.set_name(f'{self.name()}_{key}_{key_num[key]}')
                _surface.set_surfacebrep(face_brep, self.zonebrep())
                self.__geometries['Surfaces'][key].append(_surface)
                key_num[key] += 1
    
    def update_zonebrep(self, zonebrep):
        if type(zonebrep) == rg.Brep and zonebrep.IsSolid:
            self.__geometries['Zone'] = zonebrep
        else:
            raise TypeError('ZoneBrep type must be ClosedBrep.')
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def calculate_properties(self):
        self.__properties['Ceiling_Height'] = self.calculate_ceiling_height()
        self.__properties['Volume'] = self.calculate_volume()
        self.__properties['Floor_Area'] = self.calculate_floor_area()
    
    def calculate_ceiling_height(self):
        vertices_zs = []
        for face in self.surfaces()['Roof']+self.surfaces()['Floor']:
            for vertex in face.vertices():
                vertices_zs.append(vertex.Z) 
        _min = min(vertices_zs)
        _max = max(vertices_zs)
        height = _max - _min
        return round(height, 3)
    
    def calculate_volume(self):
        volume = round(rg.VolumeMassProperties.Compute(self.zonebrep()).Volume, 9)
        return volume
    
    def calculate_floor_area(self):
        floors = [face.geometry_properties()['Area'] for face in self.surfaces()['Floor']]
        floor_area = sum(floors)
        return round(floor_area, 6)
    
    def conditions(self):
        return self.__conditions
    
    def set_conditions(self, args):
        for k, v in args.items():
            if k in self.__conditions.keys():
                self.__conditions[k] = v
    
    def people(self):
        return self.__conditions['People']

    def set_people(self, people):
        self.__conditions['People'] = people
    
    def lights(self):
        return self.__conditions['Lights']

    def set_lights(self, lights):
        self.__conditions['Lights'] = lights
    
    def electric_equipment(self):
        return self.__conditions['ElectricEquipment']

    def set_electric_equipment(self, electric_equipment):
        self.__conditions['ElectricEquipment'] = electric_equipment
    
    def infiltration(self):
        return self.__conditions['Infiltration']

    def set_infiltration(self, infiltration):
        self.__conditions['Infiltration'] = infiltration
    
    def hvac(self):
        return self.__hvac
    
    def set_hvac(self, args):
        for k, v in args.items():
            if k in self.__hvac.keys():
                self.__hvac[k] = v
    
    def set_zonehvac_base(self):
        self.__hvac['EquipmentList'] = hvac.EquipmentList(f'{self.name()}_EquipmentList')
        self.__hvac['EquipmentConnections'] = hvac.EquipmentConnections(self.name(), f'{self.name()}_EquipmentList')
    
    def add_zonehvac(self, equipment_object):
        self.__hvac['EquipmentList'].add_zone_equipment(equipment_object)
    
    def set_hvac_object(self, key, hvac_object):
        self.__hvac[key] = hvac_object
        
        if key == 'ZoneControlThermostat':
            self.__hvac['ThermostatSetpointDual'] = hvac_object.thermostats()['Control_1_Object']

    def set_hvac_properties(self, epclass, key, value):
        self.__hvac[epclass].set_properties(key, value)
   
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONE',
            'fields': self.properties(),
        }
        return idfobject
    
    def to_idfobject_conditions(self):
        idfobjects = []
        for _obj in self.conditions().values():
            idfobj = _obj.to_idfobject()
            idfobjects.append(idfobj)
        return idfobjects
    
    def to_idfobject_hvac(self):
        idfobjects = []
        for _obj in self.hvac().values():
            idfobj = _obj.to_idfobject()
            idfobjects.append(idfobj)
        return idfobjects

    def duplicate(self, surface_reset=False):
        duplicate_zone = Zone(self.name())
        zb = self.zonebrep()
        duplicate_zone.update_zonebrep(zb.DuplicateBrep() if zb else None)
        duplicate_zone.update_properties(self.properties())
        
        if surface_reset:
            duplicate_zone.set_zonesurfaces()
        else:
            for surface in self.surfaces()['Wall']:
                duplicate_zone.append_surface('Wall', surface.surfacebrep(), surface.properties())
            for surface in self.surfaces()['Roof']:
                duplicate_zone.append_surface('Roof', surface.surfacebrep(), surface.properties())
            for surface in self.surfaces()['Floor']:
                duplicate_zone.append_surface('Floor', surface.surfacebrep(), surface.properties())
        
        for k, v in self.conditions().items():
            if v is not None:
                duplicate_zone.set_conditions({k:v.duplicate()})
        
        for k, v in self.hvac().items():
            if v is not None:
                duplicate_zone.set_hvac({k:v.duplicate()})
        
        return duplicate_zone
    
    def append_surface(self, surface_type, surface_brep, surface_properties):
        _surface = Surface(self.name())
        _surface.update_surfacebrep(surface_brep, self.zonebrep())
        _surface.update_properties(surface_properties)
        self.surfaces()[surface_type].append(_surface)


class Surface:
    def __init__(self, zonename):
        self.__properties = {
            'Name': None,
            'Surface_Type': None,
            'Construction_Name': None,
            'Zone_Name': zonename,
            'Space_Name': None,
            'Outside_Boundary_Condition': 'Outdoors',
            'Outside_Boundary_Condition_Object': None,
            'Sun_Exposure': 'SunExposed',
            'Wind_Exposure': 'WindExposed',
            'View_Factor_to_Ground': 'autocalculate',
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
    
    def set_surfacebrep(self, surfacebrep, zonebrep):
        if type(surfacebrep) != rg.Brep:
            raise TypeError('Unexpected Brep exists.')
        else:
            self.__geometry['Surface'] = surfacebrep

        self.__geometry_properties['Area'] = round(rg.AreaMassProperties.Compute(surfacebrep).Area, 6)
        self.__geometry_properties['Centroid'] = round_point3d(rg.AreaMassProperties.Compute(surfacebrep).Centroid)
        self.__geometry_properties['Normal'] = self.set_normal(zonebrep)

        self.set_vertices()
        self.set_type()

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
        except ValueError:
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
    
    def set_normal(self, zonebrep):
        face = self.surfacebrep().Faces[0]
        u = face.Domain(0).Mid
        v = face.Domain(1).Mid
        p = self.geometry_properties()['Centroid']
        n = face.NormalAt(u, v)
        test_p = p + n * 0.01
        if zonebrep.IsPointInside(test_p, Tol, True):
            n.Reverse()
        return round_vector3d(n)
    
    def set_type(self, AngTol=10.0):
        _normal = self.geometry_properties()['Normal']
        _hoizontal_venctor = rg.Vector3d(_normal.X, _normal.Y, 0)
        _hoizontal_venctor.Unitize()
        theta = math.degrees(math.acos(abs(_normal * _hoizontal_venctor)))
        if -AngTol <= theta <= AngTol:
            self.__properties['Surface_Type'] = 'Wall'
        else:
            if _normal.Z > 0:
                self.__properties['Surface_Type'] = 'Roof'
            else:
                self.__properties['Surface_Type'] = 'Floor'
    
    def update_surfacebrep(self, surfacebrep, zonebrep):
        if type(surfacebrep) != rg.Brep:
            raise TypeError('Unexpected Brep exists.')
        else:
            self.__geometry['Surface'] = surfacebrep
        
        self.__geometry_properties['Area'] = round(rg.AreaMassProperties.Compute(surfacebrep).Area, 6)
        self.__geometry_properties['Centroid'] = round_point3d(rg.AreaMassProperties.Compute(surfacebrep).Centroid)
        self.__geometry_properties['Normal'] = self.set_normal(zonebrep)

        self.set_vertices()


    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def update_vertices(self, vertices):
        self.__vertices = vertices
    
    def to_idfobject(self):
        idfobject = {
            'class': 'BUILDINGSURFACE:DETAILED',
            'fields': self.properties(),
        }
        return idfobject
