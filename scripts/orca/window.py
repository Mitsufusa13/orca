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

Tol = sc.doc.ModelAbsoluteTolerance

class Window:
    def __init__(self, zonename):
        self.__properties = {
            'Name': None,
            'Surface_Type': None,
            'Construction_Name': None,
            'Building_Surface_Name': None,
            'Outside_Boundary_Condition_Object': None,
            'View_Factor_to_Ground': 'autocalculate',
            'Frame_and_Divider_Name': None,
            'Multiplier': '1',
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

        self.__zonename = zonename

        self.__windowshading = None
    
    def zonename(self):
        return self.__zonename
    
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
    
    def windowshading(self):
        return self.__windowshading
    
    def set_name(self, name):
        self.__properties['Name'] = str(name)
    
    def set_type(self, surface_type):
        self.__properties['Surface_Type'] = surface_type
    
    def set_construction(self, construction):
        self.__properties['Construction_Name'] = str(construction)
    
    def set_buildingsurface(self, buildingsurface_name, outside_boundary_condition_object=None):
        self.__properties['Building_Surface_Name'] = str(buildingsurface_name)
        if outside_boundary_condition_object is not None:
            self.__properties['Outside_Boundary_Condition_Object'] = str(outside_boundary_condition_object)
    
    def set_windowshading(self, windowshading):
        self.__windowshading = windowshading

    def set_frame_and_divider(self, frame_and_divider):
        self.__properties['Frame_and_Divider_Name'] = str(frame_and_divider)
    
    def set_surfacebrep(self, surfacebrep, zonebrep):
        if type(surfacebrep) != rg.Brep:
            raise TypeError('Unexpected Brep exists.')
        else:
            self.__geometry['Surface'] = surfacebrep

        self.__geometry_properties['Area'] = round(rg.AreaMassProperties.Compute(surfacebrep).Area, 6)
        self.__geometry_properties['Centroid'] = round_point3d(rg.AreaMassProperties.Compute(surfacebrep).Centroid)
        self.__geometry_properties['Normal'] = self.set_normal(zonebrep)

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
        if solid.IsPointInside(_p1, 10e-4, True):
            p0 = p1
        elif solid.IsPointInside(_p2, 10e-4, True):
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
    
    def to_idfobject(self):
        idfobject = {
            'class': 'FENESTRATIONSURFACE:DETAILED',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self, zonebrep):
        duplicate_window = Window(self.zonename())
        duplicate_window.update_surfacebrep(self.surfacebrep(), zonebrep)
        duplicate_window.update_properties(self.properties())
        if self.windowshading() is not None:
            duplicate_window.set_windowshading(self.windowshading().duplicate())
        return duplicate_window

class ShadingControl:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Zone_Name': None,
            'Shading_Control_Sequence_Number': 1,
            'Shading_Type': None,
            'Construction_with_Shading_Name': None,
            'Shading_Control_Type': None,
            'Schedule_Name': None,
            'Setpoint': None,
            'Shading_Control_Is_Scheduled': 'No',
            'Glare_Control_Is_Active': 'No',
            'Shading_Device_Material_Name': None,
            'Type_of_Slat_Angle_Control_for_Blinds': 'FixedSlatAngle',
            'Slat_Angle_Schedule_Name': None,
            'Setpoint_2': None,
            'Daylighting_Control_Object_Name': None,
            'Multiple_Surface_Control_Type': 'Sequential',
            'Fenestration_Surface_1_Name': None,
            'Fenestration_Surface_2_Name': None,
            'Fenestration_Surface_3_Name': None,
            'Fenestration_Surface_4_Name': None,
            'Fenestration_Surface_5_Name': None,
            'Fenestration_Surface_6_Name': None,
            'Fenestration_Surface_7_Name': None,
            'Fenestration_Surface_8_Name': None,
            'Fenestration_Surface_9_Name': None,
            'Fenestration_Surface_10_Name': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        if key == 'Shading_Type':
            shading_types = ['InteriorShade', 'ExteriorShade', 'ExteriorScreen', 'InteriorBlind', 'ExteriorBlind', 'BetweenGlassShade', 'BetweenGlassBlind', 'SwitchableGlazing']
            if value not in shading_types:
                raise ValueError(f'Shading_Type must be these types: [{shading_types}]')
        elif key == 'Shading_Control_Type':
            control_types = [
                'AlwaysOn', 'AlwaysOff', 'OnIfScheduleAllows',
                'OnIfHighSolarOnWindow', 'OnIfHighHorizontalSolar', 'OnIfHighOutdoorAirTemperature', 'OnIfHighZoneAirTemperature',
                'OnIfHighZoneCooling', 'OnIfHighGlare', 'MeetDaylightIlluminanceSetpoint', 'OnNightIfLowOutdoorTempAndOffDay',
                'OnNightIfLowInsideTempAndOffDay', 'OnNightIfHeatingAndOffDay', 'OnNightIfLowOutdoorTempAndOnDayIfCooling',
                'OnNightIfHeatingAndOnDayIfCooling', 'OffNightAndOnDayIfCoolingAndHighSolarOnWindow', 'OnNightAndOnDayIfCoolingAndHighSolarOnWindow',
                'OnIfHighOutdoorAirTempAndHighSolarOnWindow', 'OnIfHighOutdoorAirTempAndHighHorizontalSolar',
                'OnIfHighZoneAirTempAndHighSolarOnWindow', 'OnIfHighZoneAirTempAndHighHorizontalSolar',
                'OnIfHighSolarOrHighLuminanceTillMidnight', 'OnIfHighSolarOrHighLuminanceTillSunset', 'OnIfHighSolarOrHighLuminanceTillNextMorning',
            ]
            if value not in control_types:
                raise ValueError(f'Shading_Control_Type must be these types: [{control_types}]')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        _properties = {}
        for k, v in self.properties().items():
            if 'Fenestration_Surface' in k:
                if v is not None:
                    _properties[k] = v
            else:
                _properties[k] = v
        
        idfobject = {
            'class': 'WINDOWSHADINGCONTROL',
            'fields': _properties,
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = ShadingControl()
        duplicate_class.update_properties(self.properties())
        return duplicate_class

