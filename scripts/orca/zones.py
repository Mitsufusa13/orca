import math
from orca import brepnormalize

try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import scriptcontext as sc
except ImportError:
    raise ImportError('scriptcontext could not import.')

try:
    import System.Drawing as sd
except ImportError:
    raise ImportError('System.Drawing could not import.')

Tol = 1e-6

class Zones:
    def __init__(self):
        self.__Zones = []
        self.__Windows = []
        self.__Shadings = []
        self.__Constructions = None
        self.__Materials = []
        self.__WindowShadings = []
        self.__Frames = []

        self.__foundation_kiva_properties = None
        self.__foundation_kiva_settings_properties = None
        self.__exposed_foundation_perimeters = []
    
    def zones(self):
        return self.__Zones
    
    def windows(self):
        return self.__Windows
    
    def shadings(self):
        return self.__Shadings
    
    def constructions(self):
        return self.__Constructions
    
    def materials(self):
        return self.__Materials
    
    def windowshadings(self):
        return self.__WindowShadings
    
    def frames(self):
        return self.__Frames
    
    def add_zone(self, zone):
        if zone.__class__.__name__ == 'Zone':
            self.__Zones.append(zone)
    
    def add_window(self, window):
        if window.__class__.__name__ == 'Window':
            self.__Windows.append(window)
    
    def add_shading(self, shading):
        if shading.__class__.__name__ == 'Shading':
            self.__Shadings.append(shading)
    
    def add_constructions(self, constructions):
        if constructions.__class__.__name__ == 'Constructions':
            self.__Constructions = constructions

            for construction in constructions.constructions().values():
                for material in construction.materials().values():
                    self.add_material(material)
            
            for windowshading in constructions.windowshadings().values():
                self.add_windowshading(windowshading)

            for frame in constructions.frame_and_divider().values():
                self.add_frame(frame)

    def add_material(self, material):
        if material.__class__.__name__ in ['Material', 'MaterialNomass', 'WindowMaterialSimpleGlazingSystem', 'WindowMaterialGlazing', 'WindowMaterialGas']:
            material_names = [_material.name() for _material in self.materials()]
            if material.name() not in material_names:
                self.__Materials.append(material)
    
    def add_windowshading(self, windowshading):
        if windowshading.__class__.__name__ in ['WindowMaterialShade', 'WindowMaterialBlind', 'WindowMaterialScreen']:
            self.__WindowShadings.append(windowshading)
    
    def add_frame(self, frame):
        if frame.__class__.__name__ in ['WindowPropertyFrameAndDivider']:
            self.__Frames.append(frame)
    
    def set_surface_constructions(self, foundationzonenames=[], atticzonenames=[]):
        foundation_surface_names = []
        attic_surface_names = []
        for zone in self.zones():
            for surface_type, surfaces in zone.surfaces().items():
                for surface in surfaces:
                    surface_name = surface.name()
                    zone_name = surface.properties()['Zone_Name']
                    if zone_name in atticzonenames:
                        attic_surface_names.append(surface_name)
                    if zone_name in foundationzonenames:
                        foundation_surface_names.append(surface_name)
                        key = 'Foundation'
                    else:
                        if surface.properties()['Outside_Boundary_Condition'] == 'Outdoors':
                            key = 'Outer'
                        else:
                            key = 'Inner'
                    key += surface_type
                    _prop = {'Construction_Name': self.constructions().properties()[key]}
                    surface.update_properties(_prop)
        
        for zone in self.zones():
            surface_type = 'Floor'
            for surface in zone.surfaces()[surface_type]:
                zone_name = surface.properties()['Zone_Name']
                pair_surface_name = surface.properties()['Outside_Boundary_Condition_Object']
                if pair_surface_name in foundation_surface_names:
                    key = 'FoundationRoof'
                    _prop = {'Construction_Name': self.constructions().properties()[key]}
                    surface.update_properties(_prop)
    
    def foundation_kiva_properties(self):
        return self.__foundation_kiva_properties
    
    def foundation_kiva_settings_properties(self):
        return self.__foundation_kiva_settings_properties
    
    def foundation_kiva_exposed_foundation_perimeters_properties(self):
        return self.__exposed_foundation_perimeters

    def set_foundation(self):
        self.__foundation_kiva_properties = {
            'Name': 'FK1',
            'Initial_Indoor_Air_Temperature': None,
            'Interior_Horizontal_Insulation_Material_Name': 'FoundationInsulation1',
            'Interior_Horizontal_Insulation_Depth': 0.000,
            'Interior_Horizontal_Insulation_Width': 0.010,
            'Interior_Vertical_Insulation_Material_Name': 'FoundationInsulation1',
            'Interior_Vertical_Insulation_Depth': 0.010,
            'Exterior_Horizontal_Insulation_Material_Name': 'FoundationInsulation1',
            'Exterior_Horizontal_Insulation_Depth': 0.000,
            'Exterior_Horizontal_Insulation_Width': 0.000,
            'Exterior_Vertical_Insulation_Material_Name': 'FoundationInsulation1',
            'Exterior_Vertical_Insulation_Depth': 0.010,
            'Wall_Height_Above_Grade': 0.2,
            'Wall_Depth_Below_Slab': 0.000,
            'Footing_Wall_Construction_Name': None,
            'Footing_Material_Name': 'Concrete_150',
            'Footing_Depth': 0.3,
        }

        self.__foundation_kiva_settings_properties = {
            'Soil_Conductivity': 1.73,
            'Soil_Density': 1842,
            'Soil_Specific_Heat': 419,
            'Ground_Solar_Absorptivity': 0.9,
            'Ground_Thermal_Absorptivity': 0.9,
            'Ground_Surface_Roughness': 0.03,
            'FarField_Width': 40,
            'DeepGround_Boundary_Condition': 'Autoselect',
            'DeepGround_Depth': 'autocalculate',
            'Minimum_Cell_Dimension': 0.02,
            'Maximum_Cell_Growth_Coefficient': 1.5,
            'Simulation_Timestep': 'Hourly',
        }
        for zone in self.zones():
            foundations = []
            walls = []
            for surface in zone.surfaces()['Floor']+zone.surfaces()['Wall']:
                if surface.properties()['Outside_Boundary_Condition'] == 'Foundation':
                    foundations.append(surface)
                elif surface.properties()['Surface_Type'] == 'Wall' and surface.properties()['Outside_Boundary_Condition'] == 'Outdoors':
                    walls.append(surface)
            for foundation in foundations:
                perimetr_length = 0
                edges = []
                vertices = list(foundation.vertices())
                vertices.append(vertices[0])
                for i in range(len(vertices[:-1])):
                    v1 = vertices[i]
                    v2 = vertices[i+1]
                    edges.append(((v1.X, v1.Y, v1.Z), (v2.X, v2.Y, v2.Z)))
                for wall in walls:
                    vertices_wall = list(wall.vertices())
                    vertices_wall.append(vertices_wall[0])
                    for i in range(len(vertices_wall[:-1])):
                        v1 = vertices_wall[i]
                        v2 = vertices_wall[i+1]
                        edge = ((v1.X, v1.Y, v1.Z), (v2.X, v2.Y, v2.Z))
                        for _edge in edges:
                            if _edge[0] == edge[0] and _edge[1] == edge[1]:
                                edge_length = math.sqrt((v2.X-v1.X)**2+(v2.Y-v1.Y)**2+(v2.Z-v1.Z)**2)
                                perimetr_length += edge_length
                            elif _edge[0] == edge[1] and _edge[1] == edge[0]:
                                edge_length = math.sqrt((v2.X-v1.X)**2+(v2.Y-v1.Y)**2+(v2.Z-v1.Z)**2)
                                perimetr_length += edge_length
                if perimetr_length > 0:
                    _properties = {
                        'Surface_Name': foundation.name(),
                        'Exposed_Perimeter_Calculation_Method': 'TotalExposedPerimeter',
                        'Total_Exposed_Perimeter': perimetr_length,
                    }
                    self.__exposed_foundation_perimeters.append(_properties)
    
    def duplicate(self):
        duplicate_zones = Zones()
        for _zone in self.zones():
            duplicate_zones.add_zone(_zone.duplicate())
        breps = {zone.name():zone.zonebrep() for zone in duplicate_zones.zones()}
        for _window in self.windows():
            duplicate_zones.add_window(_window.duplicate(breps[_window.zonename()]))
        for _shading in self.shadings():
            duplicate_zones.add_shading(_shading.duplicate())
        if self.constructions() is not None:
            duplicate_zones.add_constructions(self.constructions().duplicate())
        return duplicate_zones
    
    def to_idfobjects_dict(self):
        idf_objects = {}
        schedule_names = {
            'Year': [],
            'Week': [],
            'Day': [],
            'Typelimits': [],
        }
        internal_gain_names = {
            'People': [],
            'Lights': [],
            'ElectricEquipment': [],
            'Infiltration': [],
        }
        hvac_names = {
            'EquipmentList': [],
            'EquipmentConnections': [],
            'ZoneHVAC': [],
            'ZoneControlHumidistat': [],
            'ZoneControlThermostat': [],
            'ThermostatSetpointDual': [],
        }
        for obj_zone in self.zones():
            idf_object = obj_zone.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)
            for _, obj_surfaces in obj_zone.surfaces().items():
                for obj_surface in obj_surfaces:
                    idf_object = obj_surface.to_idfobject()
                    _class = idf_object['class']
                    _values = idf_object['fields']
                    if _class not in idf_objects.keys():
                        idf_objects[_class] = []
                    idf_objects[_class].append(_values)
            
            for k, obj_internal_gain in obj_zone.conditions().items():
                if obj_internal_gain is not None:
                    idf_object = obj_internal_gain.to_idfobject()
                    _class = idf_object['class']
                    _values = idf_object['fields']
                    if _class not in idf_objects.keys():
                        idf_objects[_class] = []
                    if _values['Name'] not in internal_gain_names[k]:
                        idf_objects[_class].append(_values)
                        internal_gain_names[k].append(_values['Name'])

                        if k == 'People':
                            for _, obj_sch_year in obj_internal_gain.schedules().items():
                                if obj_sch_year is not None:
                                    idf_object = obj_sch_year.to_idfobject()
                                    _class = idf_object['class']
                                    _values = idf_object['fields']
                                    if _class not in idf_objects.keys():
                                        idf_objects[_class] = []
                                    if _values['Name'] not in schedule_names['Year']:
                                        idf_objects[_class].append(_values)
                                        schedule_names['Year'].append(_values['Name'])
                                    for _, obj_sch_week in obj_sch_year.week_schedules().items():
                                        if obj_sch_week is not None:
                                            idf_object = obj_sch_week.to_idfobject()
                                            _class = idf_object['class']
                                            _values = idf_object['fields']
                                            if _class not in idf_objects.keys():
                                                idf_objects[_class] = []
                                            if _values['Name'] not in schedule_names['Week']:
                                                idf_objects[_class].append(_values)
                                                schedule_names['Week'].append(_values['Name'])
                                            for _, obj_sch_day in obj_sch_week.day_schedules().items():
                                                if obj_sch_day is not None:
                                                    idf_object = obj_sch_day.to_idfobject()
                                                    _class = idf_object['class']
                                                    _values = idf_object['fields']
                                                    if _class not in idf_objects.keys():
                                                        idf_objects[_class] = []
                                                    if _values['Name'] not in schedule_names['Day']:
                                                        idf_objects[_class].append(_values)
                                                        schedule_names['Day'].append(_values['Name'])

                                                    idf_object = obj_sch_day.type_limits().to_idfobject()
                                                    _class = idf_object['class']
                                                    _values = idf_object['fields']
                                                    if _class not in idf_objects.keys():
                                                        idf_objects[_class] = []
                                                    if _values['Name'] not in schedule_names['Typelimits']:
                                                        idf_objects[_class].append(_values)
                                                        schedule_names['Typelimits'].append(_values['Name'])
                        else:
                            obj_sch_year = obj_internal_gain.schedule()
                            idf_object = obj_sch_year.to_idfobject()
                            _class = idf_object['class']
                            _values = idf_object['fields']
                            if _class not in idf_objects.keys():
                                idf_objects[_class] = []
                            if _values['Name'] not in schedule_names['Year']:
                                idf_objects[_class].append(_values)
                                schedule_names['Year'].append(_values['Name'])
                            for _, obj_sch_week in obj_sch_year.week_schedules().items():
                                if obj_sch_week is not None:
                                    idf_object = obj_sch_week.to_idfobject()
                                    _class = idf_object['class']
                                    _values = idf_object['fields']
                                    if _class not in idf_objects.keys():
                                        idf_objects[_class] = []
                                    if _values['Name'] not in schedule_names['Week']:
                                        idf_objects[_class].append(_values)
                                        schedule_names['Week'].append(_values['Name'])
                                    for _, obj_sch_day in obj_sch_week.day_schedules().items():
                                        if obj_sch_day is not None:
                                            idf_object = obj_sch_day.to_idfobject()
                                            _class = idf_object['class']
                                            _values = idf_object['fields']
                                            if _class not in idf_objects.keys():
                                                idf_objects[_class] = []
                                            if _values['Name'] not in schedule_names['Day']:
                                                idf_objects[_class].append(_values)
                                                schedule_names['Day'].append(_values['Name'])

                                            idf_object = obj_sch_day.type_limits().to_idfobject()
                                            _class = idf_object['class']
                                            _values = idf_object['fields']
                                            if _class not in idf_objects.keys():
                                                idf_objects[_class] = []
                                            if _values['Name'] not in schedule_names['Typelimits']:
                                                idf_objects[_class].append(_values)
                                                schedule_names['Typelimits'].append(_values['Name'])

            for k, obj_hvac in obj_zone.hvac().items():
                if obj_hvac is not None:
                    idf_object = obj_hvac.to_idfobject()
                    _class = idf_object['class']
                    _values = idf_object['fields']
                    if _class not in idf_objects.keys():
                        idf_objects[_class] = []
                    if k != 'EquipmentConnections':
                        if _values['Name'] not in hvac_names[k]:
                            idf_objects[_class].append(_values)
                            hvac_names[k].append(_values['Name'])

                            if k in ['ZoneHVAC', 'ZoneControlHumidistat', 'ZoneControlThermostat', 'ThermostatSetpointDual']:
                                for _, obj_sch_year in obj_hvac.schedules().items():
                                    if obj_sch_year is not None:
                                        idf_object = obj_sch_year.to_idfobject()
                                        _class = idf_object['class']
                                        _values = idf_object['fields']
                                        if _class not in idf_objects.keys():
                                            idf_objects[_class] = []
                                        if _values['Name'] not in schedule_names['Year']:
                                            idf_objects[_class].append(_values)
                                            schedule_names['Year'].append(_values['Name'])
                                        for _, obj_sch_week in obj_sch_year.week_schedules().items():
                                            if obj_sch_week is not None:
                                                idf_object = obj_sch_week.to_idfobject()
                                                _class = idf_object['class']
                                                _values = idf_object['fields']
                                                if _class not in idf_objects.keys():
                                                    idf_objects[_class] = []
                                                if _values['Name'] not in schedule_names['Week']:
                                                    idf_objects[_class].append(_values)
                                                    schedule_names['Week'].append(_values['Name'])
                                                for _, obj_sch_day in obj_sch_week.day_schedules().items():
                                                    if obj_sch_day is not None:
                                                        idf_object = obj_sch_day.to_idfobject()
                                                        _class = idf_object['class']
                                                        _values = idf_object['fields']
                                                        if _class not in idf_objects.keys():
                                                            idf_objects[_class] = []
                                                        if _values['Name'] not in schedule_names['Day']:
                                                            idf_objects[_class].append(_values)
                                                            schedule_names['Day'].append(_values['Name'])

                                                        idf_object = obj_sch_day.type_limits().to_idfobject()
                                                        _class = idf_object['class']
                                                        _values = idf_object['fields']
                                                        if _class not in idf_objects.keys():
                                                            idf_objects[_class] = []
                                                        if _values['Name'] not in schedule_names['Typelimits']:
                                                            idf_objects[_class].append(_values)
                                                            schedule_names['Typelimits'].append(_values['Name'])
                            else:
                                pass
                    else:
                        if _values['Zone_Name'] not in hvac_names[k]:
                            idf_objects[_class].append(_values)
                            hvac_names[k].append(_values['Zone_Name'])

        for obj in self.windows():
            idf_object = obj.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)

            if obj.windowshading() is not None:
                idf_object = obj.windowshading().to_idfobject()
                _class = idf_object['class']
                _values = idf_object['fields']
                if _class not in idf_objects.keys():
                    idf_objects[_class] = []
                idf_objects[_class].append(_values)

        for obj in self.shadings():
            idf_object = obj.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)
        
        for obj in self.materials():
            idf_object = obj.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)
        
        for obj in [v for v in self.constructions().constructions().values()]:
            idf_object = obj.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)
        
        for obj in self.windowshadings():
            idf_object = obj.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)
        
        for obj in self.frames():
            idf_object = obj.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)
        
        if len(self.foundation_kiva_exposed_foundation_perimeters_properties()) > 0:
            idf_object = {
                'class': 'FOUNDATION:KIVA',
                'fields': self.foundation_kiva_properties(),
            }
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)

            idf_object = {
                'class': 'FOUNDATION:KIVA:SETTINGS',
                'fields': self.foundation_kiva_settings_properties(),
            }
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects.keys():
                idf_objects[_class] = []
            idf_objects[_class].append(_values)

            for _prop in self.foundation_kiva_exposed_foundation_perimeters_properties():
                idf_object = {
                    'class': 'SURFACEPROPERTY:EXPOSEDFOUNDATIONPERIMETER',
                    'fields': _prop,
                }
                _class = idf_object['class']
                _values = idf_object['fields']
                if _class not in idf_objects.keys():
                    idf_objects[_class] = []
                idf_objects[_class].append(_values)
        
        return idf_objects

def extract_zonesurfaces(zones):
    _surfaces = []
    for zone in zones:
        surface_dict = zone.surfaces()
        for surfaces in surface_dict.values():
            for surface in surfaces:
                _surfaces.append(surface)
    return _surfaces, [s.surfacebrep() for s in _surfaces]

def split_surfaces(Zones):
    for i, z1 in enumerate(Zones):
        split_zones = []
        for j, z2 in enumerate(Zones):
            if i == j:
                pass
            else:
                split_zones.append(z2)
        for split_zone in split_zones:
            splited_surfaces = brepnormalize.split_brep(z1.zonebrep(), [split_zone.zonebrep()], Tol)
            if len(splited_surfaces) <= 1:
                pass
            else:
                new_zonebrep = brepnormalize.join_breps(splited_surfaces, Tol, False, False, False)[0]
                new_zonebrep.CapPlanarHoles(Tol)
                if new_zonebrep.IsSolid:
                    z1.update_zonebrep(new_zonebrep)
                    z1.set_zonesurfaces()
                else:
                    pass

def judgement_floor_ground(zones, ground_brep, ground_object):
    for zone in zones:
        for surface in zone.surfaces()['Floor']:
            centroid = surface.geometry_properties()['Centroid']
            if is_point_on_brep_plane(ground_brep, centroid):
                _prop = {
                        'Outside_Boundary_Condition': ground_object,
                        'Sun_Exposure': 'NoSun',
                        'Wind_Exposure': 'NoWind',
                    }
                surface.update_properties(_prop)
            else:
                pass
    return zones

def is_point_on_brep_plane(brep, point, tol=1e-6):
    if brep is None or point is None:
        return False

    for face in brep.Faces:
        rc, plane = face.TryGetPlane()
        if not rc:
            continue

        dist = abs(plane.DistanceTo(point))

        if dist <= tol:
            return True

    return False

def _pt_equal(a, b, tol=Tol, scale=5.0):
    tol = sc.doc.ModelAbsoluteTolerance if tol is None else float(tol)
    return a.DistanceTo(b) <= tol*scale

def matching_surfaces(zones):
    for target_zone in zones:
        evaluate_surfaces = []
        for evaluate_zone in zones:
            if target_zone.name() != evaluate_zone.name():
                surfaces = evaluate_zone.surfaces()['Wall']+evaluate_zone.surfaces()['Roof']+evaluate_zone.surfaces()['Floor']
                for surface in surfaces:
                    evaluate_surfaces.append(surface)

        surfaces = target_zone.surfaces()['Wall']+target_zone.surfaces()['Roof']+target_zone.surfaces()['Floor']
        for target_surface in surfaces:
            target_centroid = target_surface.geometry_properties()['Centroid']
            for evaluate_surface in evaluate_surfaces:
                evaluate_centroid = evaluate_surface.geometry_properties()['Centroid']
                if _pt_equal(target_centroid, evaluate_centroid):
                    _prop = {
                        'Outside_Boundary_Condition': 'Surface',
                        'Outside_Boundary_Condition_Object': evaluate_surface.name(),
                        'Sun_Exposure': 'NoSun',
                        'Wind_Exposure': 'NoWind',
                    }
                    if target_surface.properties()['Surface_Type'] == 'Roof':
                        _prop['Surface_Type'] = 'Ceiling'
                    target_surface.update_properties(_prop)
    return zones

def search_window_host_wall(window, walls):
    window_nomal = window.geometry_properties()['Normal']
    walls_same_normal = []
    for _wall in walls:
        if _wall.geometry_properties()['Normal'] == window_nomal:
            walls_same_normal.append(_wall)

    window_centroid = window.geometry_properties()['Centroid']
    walls_on_centroid = []
    for _wall in walls_same_normal:
        _wall_face = _wall.surfacebrep().Faces[0]
        ok, u, v = _wall_face.ClosestPoint(window_centroid)
        if ok:
            pt_on = _wall_face.PointAt(u, v)
            dist = window_centroid.DistanceTo(pt_on)
            inside = _wall_face.IsPointOnFace(u, v) == rg.PointFaceRelation.Interior and dist < Tol
            if inside:
                walls_on_centroid.append(_wall)

    if len(walls_on_centroid) == 1:
        return walls_on_centroid[0]

def plane_right_from_normal(origin: rg.Point3d,
                            normal: rg.Vector3d,
                            world_up: rg.Vector3d = rg.Vector3d.ZAxis) -> rg.Plane:
    n = rg.Vector3d(normal)
    if n.IsTiny():
        n = rg.Vector3d.ZAxis
    n.Unitize()

    up_ref = rg.Vector3d(world_up)
    up_ref.Unitize()
    if abs(rg.Vector3d.Multiply(up_ref, n)) > 0.999:
        up_ref = rg.Vector3d.YAxis
        if abs(rg.Vector3d.Multiply(up_ref, n)) > 0.999:
            up_ref = rg.Vector3d.XAxis

    up = up_ref - rg.Vector3d.Multiply(rg.Vector3d.Multiply(up_ref, n), n)
    if up.IsTiny():
        up = rg.Vector3d.YAxis
    up.Unitize()

    right = rg.Vector3d.CrossProduct(up, n)
    if right.IsTiny():
        right = rg.Vector3d.XAxis
    right.Unitize()

    y = rg.Vector3d.CrossProduct(n, right)
    y.Unitize()

    return rg.Plane(origin, right, y)

def create_mesh_from_brep(surface_brep, color, mp=None):
    if surface_brep is None:
        return None
    
    if mp is None:
        mp = rg.MeshingParameters()
        mp.SimplePlanes = True
        mp.RefineGrid = False
        mp.MaximumEdgeLength = 0
    
    meshes = rg.Mesh.CreateFromBrep(surface_brep, mp)
    if not meshes:
        return None
    
    if len(meshes) == 1:
        mesh = meshes[0]
    else:
        mesh = rg.Mesh()
        for m in meshes:
            mesh.Append(m)
    
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    mesh.VertexColors.CreateMonotoneMesh(color)
    return mesh

def create_mesh_from_brep_with_cut_openings(surface, opening_surfaces, color, tol=None):
    if tol is None:
        tol = Tol

    bool_tol = tol * 0.1

    surface_brep = surface.surfacebrep()

    face = surface_brep.Faces[0]
    outer_loop = face.OuterLoop.To3dCurve()

    inner_loops = []
    for wb in opening_surfaces:
        f = wb.surfacebrep().Faces[0]
        inner_loops.append(f.OuterLoop.To3dCurve())

    diff_curves = rg.Curve.CreateBooleanDifference(outer_loop, inner_loops, bool_tol)
    if not diff_curves:
        print('BooleanDifference failed:', surface.name())
        return None

    breps = rg.Brep.CreatePlanarBreps(diff_curves, bool_tol)
    if not breps:
        print('CreatePlanarBreps failed:', surface.name())
        return None

    surface_mesh = create_mesh_from_brep(breps[0], color)
    return surface_mesh



part_color_dict = {
    'OUTERWALL':   sd.Color.FromArgb(0, 252, 218, 106),
    'INNERWALL':   sd.Color.FromArgb(0, 245, 144,  12),
    'FOUNDATIONWALL':   sd.Color.FromArgb(0, 191, 191, 191),
    'OUTERROOF':   sd.Color.FromArgb(0, 168,   0,   0),
    'INNERCEILING':sd.Color.FromArgb(0, 230, 230, 255),
    'FOUNDATIONROOF':sd.Color.FromArgb(0, 230, 230, 255),
    'FOUNDATIONCEILING':sd.Color.FromArgb(0, 230, 230, 255),
    'OUTERFLOOR':  sd.Color.FromArgb(0, 168,   0,   0),
    'INNERFLOOR':  sd.Color.FromArgb(0, 230, 230, 255),
    'FOUNDATIONFLOOR':  sd.Color.FromArgb(0, 90, 90, 90),
    'AIRWALL':sd.Color.FromArgb(0.99, 0, 0, 0),
    'WINDOW': sd.Color.FromArgb(255,  12, 245, 245),
    'DOOR':   sd.Color.FromArgb(255, 160,  82,  45),
    'SHADING':sd.Color.FromArgb(0, 129,  12, 245),
}

def check_zones(Zones, FoundationNames):
    mp = rg.MeshingParameters()
    mp.SimplePlanes = True
    mp.RefineGrid = False
    mp.MaximumEdgeLength = 0
    Mesh = []
    text_loc = []
    text = []
    buildingsurface_have_fenestrationsurface_dict = {}
    for zone in Zones.zones():
        for surface in zone.surfaces()['Wall']+zone.surfaces()['Roof']+zone.surfaces()['Floor']:
            buildingsurface_have_fenestrationsurface_dict[surface.name()] = {'bs_object': surface, 'fs_objects': [], 'color': None}
            key = ''
            if surface.properties()['Zone_Name'] in FoundationNames:
                key += 'FOUNDATION'
            elif surface.properties()['Outside_Boundary_Condition'] == 'Outdoors':
                key += 'OUTER'
            else:
                key += 'INNER'
            key += surface.properties()['Surface_Type'].upper()
            color = part_color_dict[key]
            buildingsurface_have_fenestrationsurface_dict[surface.name()]['color'] = color
    
    for window in Zones.windows():
        buildingsurface_have_fenestrationsurface_dict[window.properties()['Building_Surface_Name']]['fs_objects'].append(window)

        key = ''
        key += window.properties()['Surface_Type'].upper()
        color = part_color_dict[key]

        Mesh.append(create_mesh_from_brep(window.surfacebrep(), color))
        text_loc.append(plane_right_from_normal(window.geometry_properties()['Centroid'], window.geometry_properties()['Normal']))
        text.append(window.name())
    
    for k in buildingsurface_have_fenestrationsurface_dict.keys():
        color = buildingsurface_have_fenestrationsurface_dict[k]['color']
        bs_object = buildingsurface_have_fenestrationsurface_dict[k]['bs_object']
        fs_objects = buildingsurface_have_fenestrationsurface_dict[k]['fs_objects']
        
        if len(fs_objects) > 0:
            print(bs_object.name())
            mesh = create_mesh_from_brep_with_cut_openings(bs_object, fs_objects, color)
        else:
            mesh = create_mesh_from_brep(bs_object.surfacebrep(), color)
        
        Mesh.append(mesh)
        text_loc.append(plane_right_from_normal(bs_object.geometry_properties()['Centroid'], bs_object.geometry_properties()['Normal']))
        text.append(bs_object.name())

    
    for shading in Zones.shadings():
        key = 'SHADING'
        color = part_color_dict[key]

        Mesh.append(create_mesh_from_brep(shading.surfacebrep(), color))
        text_loc.append(plane_right_from_normal(shading.geometry_properties()['Centroid'], shading.geometry_properties()['Normal']))
        text.append(shading.name())
    
    return Mesh, text_loc, text