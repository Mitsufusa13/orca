import copy
import math
import os
import json


def read_epobjects():
    epobjects_path = os.path.join(os.path.dirname(__file__), 'epobjects.json')
    with open(epobjects_path, mode='r', encoding='utf-8') as f:
        epobjects = json.load(f)
    return epobjects


from orca import brepnormalize
from orca import material
from orca.to_idf import write_idf

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

class Model:
    def __init__(self, model_name):
        self.__name = model_name
        self.__multi_object_epclasses = [
            'SCHEDULETYPELIMITS', 'SCHEDULE:DAY:INTERVAL',
            'SCHEDULE:WEEK:DAILY', 'SCHEDULE:YEAR',
            'ZONE', 'BUILDINGSURFACE:DETAILED', 'FENESTRATIONSURFACE:DETAILED',
            'MATERIAL', 'MATERIAL:NOMASS', 'WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM',
            'WINDOWMATERIAL:GLAZING', 'WINDOWMATERIAL:GAS',
            'WINDOWMATERIAL:SHADE', 'WINDOWMATERIAL:BLIND', 'WINDOWMATERIAL:SCREEN',
            'CONSTRUCTION',
            'WINDOWSHADINGCONTROL', 'WINDOWPROPERTY:FRAMEANDDIVIDER',
            'PEOPLE', 'LIGHTS', 'ELECTRICEQUIPMENT',
            'ZONEINFILTRATION:DESIGNFLOWRATE',
            'ZONEHVAC:EQUIPMENTLIST', 'ZONEHVAC:EQUIPMENTCONNECTIONS',
            'ZONEHVAC:IDEALLOADSAIRSYSTEM',
            'ZONECONTROL:HUMIDISTAT', 'ZONECONTROL:THERMOSTAT',
            'THERMOSTATSETPOINT:DUALSETPOINT',
            'OUTPUT:VARIABLE',
        ]
        self.__epobjects_dict = read_epobjects()
        self.__epobjects = {k: None for k in self.epobjects_dict.keys()}
        self.__Zones = {}
        self.__Surfaces = {}
        self.__Windows = {}
        self.__Shadings = {}
        self.__Constructions = {}
        self.__Materials = {}
        self.__WindowShadings = {}
        self.__Frames = {}
        self.__Schedule_Year = {}
        self.__Schedule_Week = {}
        self.__Schedule_Day = {}
        self.__Schedule_TypeLimits = {}
        self.__output_variables = []
        self.__Construction_set = None
        self.__FoundationZoneName = []

        self.__simulation_control_objects = {
            'VERSION': {
                'Version_Identifier': '24.2'
            },
            'SIMULATIONCONTROL': {
                'Do_Zone_Sizing_Calculation': 'No',
                'Do_System_Sizing_Calculation': 'No',
                'Do_Plant_Sizing_Calculation': 'No',
                'Run_Simulation_for_Sizing_Periods': 'No',
                'Run_Simulation_for_Weather_File_Run_Periods': 'Yes',
                'Do_HVAC_Sizing_Simulation_for_Sizing_Periods': 'No',
                'Maximum_Number_of_HVAC_Sizing_Simulation_Passes': '1',
            },
            'BUILDING': {
                'Name': f'{model_name}',
                'North_Axis': '0',
                'Terrain': 'Suburbs',
                'Loads_Convergence_Tolerance_Value': '0.04',
                'Temperature_Convergence_Tolerance_Value': '0.4',
                'Solar_Distribution': 'FullInteriorAndExterior',
                'Maximum_Number_of_Warmup_Days': '25',
                'Minimum_Number_of_Warmup_Days': '1',
            },
            'SHADOWCALCULATION': {
                'Shading_Calculation_Method': 'PolygonClipping',
                'Shading_Calculation_Update_Frequency_Method': 'Periodic',
                'Shading_Calculation_Update_Frequency': '20',
                'Maximum_Figures_in_Shadow_Overlap_Calculations': '15000',
                'Polygon_Clipping_Algorithm': 'SutherlandHodgman',
                'Pixel_Counting_Resolution': '512',
                'Sky_Diffuse_Modeling_Algorithm': 'SimpleSkyDiffuseModeling',
                'Output_External_Shading_Calculation_Results': 'No',
                'Disable_SelfShading_Within_Shading_Zone_Groups': 'No',
                'Disable_SelfShading_From_Shading_Zone_Groups_to_Other_Zones': 'No',
                'Shading_Zone_Group_1_ZoneList_Name': '',
                'Shading_Zone_Group_2_ZoneList_Name': '',
                'Shading_Zone_Group_3_ZoneList_Name': '',
                'Shading_Zone_Group_4_ZoneList_Name': '',
                'Shading_Zone_Group_5_ZoneList_Name': '',
                'Shading_Zone_Group_6_ZoneList_Name': '',
            },
            'SURFACECONVECTIONALGORITHM:INSIDE': {
                'Algorithm': 'TARP',

            },
            'SURFACECONVECTIONALGORITHM:OUTSIDE': {
                'Algorithm': 'DOE-2',
            },
            'HEATBALANCEALGORITHM': {
                'Algorithm': 'ConductionTransferFunction',
                'Surface_Temperature_Upper_Limit': '200',
                'Minimum_Surface_Convection_Heat_Transfer_Coefficient_Value': '0.1',
                'Maximum_Surface_Convection_Heat_Transfer_Coefficient_Value': '1000',
            },
            'HEATBALANCESETTINGS:CONDUCTIONFINITEDIFFERENCE': {
                'Difference_Scheme': 'FullyImplicitFirstOrder',
                'Space_Discretization_Constant': '3',
                'Relaxation_Factor': '1',
                'Inside_Face_Surface_Temperature_Convergence_Criteria': '0.002',

            },
            'ZONEAIRHEATBALANCEALGORITHM': {
                'Algorithm': 'ThirdOrderBackwardDifference',
                'Do_Space_Heat_Balance_for_Sizing': 'No',
                'Do_Space_Heat_Balance_for_Simulation': 'No',

            },
            'ZONEAIRMASSFLOWCONSERVATION': {
                'Adjust_Zone_Mixing_and_Return_For_Air_Mass_Flow_Balance': 'None',
                'Infiltration_Balancing_Method': 'AddInfiltrationFlow',
                'Infiltration_Balancing_Zones': 'MixingSourceZonesOnly',
            },
            'TIMESTEP': {
                'Number_of_Timesteps_per_Hour': '6',
            },
            'RUNPERIOD': {
                'Name':'RunPeriod1',
                'Begin_Month': '1',
                'Begin_Day_of_Month': '1',
                'Begin_Year': '2020',
                'End_Month': '12',
                'End_Day_of_Month': '31',
                'End_Year': '2020',
                'Day_of_Week_for_Start_Day': 'Wednesday',
                'Use_Weather_File_Holidays_and_Special_Days': 'No',
                'Use_Weather_File_Daylight_Saving_Period': 'No',
                'Apply_Weekend_Holiday_Rule': 'No',
                'Use_Weather_File_Rain_Indicators': 'No',
                'Use_Weather_File_Snow_Indicators': 'No',
                'Treat_Weather_as_Actual': 'No',
                'First_Hour_Interpolation_Starting_Values': 'Hour24',
            },
            'GLOBALGEOMETRYRULES': {
                'Starting_Vertex_Position': 'UpperLeftCorner',
                'Vertex_Entry_Direction': 'Counterclockwise',
                'Coordinate_System': 'Relative',
                'Daylighting_Reference_Point_Coordinate_System': 'Relative',
                'Rectangular_Surface_Coordinate_System': 'Relative',
            },
        }
        for k ,v in self.simulation_control_objects.items():
            self.add_epobject(k, v)

        self.__output_objects = {
            'OUTPUT:VARIABLEDICTIONARY': {
                'Key_Field': 'regular',
                'Sort_Option': 'Unsorted',
            },
            'OUTPUTCONTROL:FILES': {
                'Output_CSV': 'No',
                'Output_MTR': 'Yes',
                'Output_ESO': 'Yes',
                'Output_EIO': 'Yes',
                'Output_Tabular': 'Yes',
                'Output_SQLite': 'Yes',
                'Output_JSON': 'Yes',
                'Output_AUDIT': 'Yes',
                'Output_Space_Sizing': 'Yes',
                'Output_Zone_Sizing': 'Yes',
                'Output_System_Sizing': 'Yes',
                'Output_DXF': 'Yes',
                'Output_BND': 'Yes',
                'Output_RDD': 'Yes',
                'Output_MDD': 'Yes',
                'Output_MTD': 'Yes',
                'Output_END': 'Yes',
                'Output_SHD': 'Yes',
                'Output_DFS': 'Yes',
                'Output_GLHE': 'Yes',
                'Output_DelightIn': 'Yes',
                'Output_DelightELdmp': 'Yes',
                'Output_DelightDFdmp': 'Yes',
                'Output_EDD': 'Yes',
                'Output_DBG': 'Yes',
                'Output_PerfLog': 'Yes',
                'Output_SLN': 'Yes',
                'Output_SCI': 'Yes',
                'Output_WRL': 'Yes',
                'Output_Screen': 'Yes',
                'Output_ExtShd': 'Yes',
                'Output_Tarcog': 'Yes',
            },
            'OUTPUT:SQLITE': {
                'Option_Type': 'SimpleAndTabular',
                'Unit_Conversion_for_Tabular_Data': 'None',
            },
        }
        for k ,v in self.output_objects.items():
            self.add_epobject(k, v)
        
        self.__foundation_kiva_objects = {}
        self.__exposed_foundation_perimeters = {}
    
    @property
    def name(self):
        return self.__name
    
    @property
    def foundationzonenames(self):
        return self.__FoundationZoneName
    
    def add_foundationzonenames(self, foundationzonenames):
        for foundationzonename in foundationzonenames:
            if foundationzonename not in self.foundationzonenames:
                self.__FoundationZoneName.append(foundationzonename)

    # property and add property
    @property
    def multi_object_epclasses(self):
        return self.__multi_object_epclasses
    
    @property
    def epobjects_dict(self):
        return self.__epobjects_dict

    @property
    def epobjects(self):
        _epobjects = {}
        for k, v in self.__epobjects.items():
            if v is not None:
                _epobjects[k] = v
        return _epobjects
    
    def add_epobject(self, epclass, value_dict):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])

        for k, v in value_dict.items():
            if k in _dict.keys():
                _dict[k] = v

        self.__epobjects[epclass] = _dict
    
    def edit_epobject(self, epclass, field, value):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])

        if field in _dict.keys():
            self.__epobjects[epclass][field] = value
        else:
            print(f'FieldName "{field}" not in {epclass} fields.')
    
    @property
    def simulation_control_objects(self):
        return self.__simulation_control_objects
    
    def add_simulation_control_object(self, epclass, value_dict):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])
        
        for k, v in value_dict.items():
            if k in _dict.keys():
                _dict[k] = v

        self.__simulation_control_objects[epclass] = _dict
        self.add_epobject(epclass, _dict)
    
    def edit_simulation_control_object(self, epclass, field, value):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])

        if field in _dict.keys():
            self.__simulation_control_objects[epclass][field] = value
            self.edit_epobject(epclass, field, value)
        else:
            print(f'FieldName "{field}" not in {epclass} fields.')
    
    @property
    def output_objects(self):
        return self.__output_objects
    
    def add_output_object(self, epclass, value_dict):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])
        
        for k, v in value_dict.items():
            if k in _dict.keys():
                _dict[k] = v

        self.__output_objects[epclass] = _dict
        self.add_epobject(epclass, _dict)
    
    def edit_output_object(self, epclass, field, value):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])

        if field in _dict.keys():
            self.__output_objects[epclass][field] = value
            self.edit_epobject(epclass, field, value)
        else:
            print(f'FieldName "{field}" not in {epclass} fields.')
    
    @property
    def foundation_kiva_objects(self):
        return self.__foundation_kiva_objects
    
    def add_foundation_kiva_object(self, epclass, value_dict):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])
        
        for k, v in value_dict.items():
            if k in _dict.keys():
                _dict[k] = v

        self.__foundation_kiva_objects[epclass] = _dict
        self.add_epobject(epclass, _dict)
    
    def edit_foundation_kiva_object(self, epclass, field, value):
        epclass = epclass.upper()
        _dict = copy.copy(self.epobjects_dict[epclass])

        if field in _dict.keys():
            self.__foundation_kiva_objects[epclass][field] = value
            self.edit_epobject(epclass, field, value)
        else:
            print(f'FieldName "{field}" not in {epclass} fields.')
    
    @property
    def exposed_foundation_perimeters(self):
        return self.__exposed_foundation_perimeters
    
    def add_exposed_foundation_perimeters(self, surface_name, exposed_foundation_perimeter):
        self.__exposed_foundation_perimeters[surface_name] = exposed_foundation_perimeter
    
    @property
    def zones(self):
        return self.__Zones
    
    def add_zone(self, zone):
        if zone.__class__.__name__ == 'Zone':
            self.__Zones[zone.name()] = zone

            for surfaces_obj in zone.surfaces().values():
                for surface_obj in surfaces_obj:
                    self.add_surface(surface_obj)
            
            for condition_type, internal_gain_obj in zone.conditions().items():
                if internal_gain_obj is not None:
                    if condition_type == 'People':
                        for sch_year_obj in internal_gain_obj.schedules().values():
                            self.add_sch_year(sch_year_obj)
                            for sch_week_obj in sch_year_obj.week_schedules().values():
                                self.add_sch_week(sch_week_obj)
                                for sch_day_obj in sch_week_obj.day_schedules().values():
                                    self.add_sch_day(sch_day_obj)
                                    self.add_sch_typelimits(sch_day_obj.type_limits())
                    else:
                        sch_year_obj = internal_gain_obj.schedule()
                        self.add_sch_year(sch_year_obj)
                        for sch_week_obj in sch_year_obj.week_schedules().values():
                            self.add_sch_week(sch_week_obj)
                            for sch_day_obj in sch_week_obj.day_schedules().values():
                                self.add_sch_day(sch_day_obj)
                                self.add_sch_typelimits(sch_day_obj.type_limits())
                                
            for hvac_type, hvac_obj in zone.hvac().items():
                if hvac_obj is not None:
                    if hvac_type in ['ZoneHVAC', 'ZoneControlHumidistat', 'ZoneControlThermostat', 'ThermostatSetpointDual']:
                        for sch_year_obj in hvac_obj.schedules().values():
                            self.add_sch_year(sch_year_obj)
                            for sch_week_obj in sch_year_obj.week_schedules().values():
                                self.add_sch_week(sch_week_obj)
                                for sch_day_obj in sch_week_obj.day_schedules().values():
                                    self.add_sch_day(sch_day_obj)
                                    self.add_sch_typelimits(sch_day_obj.type_limits())
    
    @property
    def surfaces(self):
        return self.__Surfaces
    
    def add_surface(self, surface):
        if surface.__class__.__name__ == 'Surface':
            self.__Surfaces[surface.name()] = surface
    
    @property
    def windows(self):
        return self.__Windows
    
    def add_window(self, window):
        if window.__class__.__name__ == 'Window':
            self.__Windows[window.name()] = window
    
    @property
    def shadings(self):
        return self.__Shadings
    
    def add_shading(self, shading):
        if shading.__class__.__name__ == 'Shading':
            self.__Shadings[shading.name()] = shading
    
    @property
    def construction_set(self):
        return self.__Construction_set
    
    def add_construction_set(self, construction_set):
        if construction_set.__class__.__name__ == 'Constructions':
            self.__Construction_set = construction_set

            for construction in construction_set.constructions().values():
                if construction is not None:
                    self.add_construction(construction)
                    for material in construction.materials().values():
                        self.add_material(material)
            
            for windowshading in construction_set.windowshadings().values():
                self.add_windowshading(windowshading)

            for frame in construction_set.frame_and_divider().values():
                self.add_frame(frame)

    @property
    def constructions(self):
        return self.__Constructions
    
    def add_construction(self, construction):
        if construction.__class__.__name__ in ['Construction', 'ConstructionWindow']:
            self.__Constructions[construction.name()] = construction

    @property
    def materials(self):
        return self.__Materials
    
    def add_material(self, material):
        if material.__class__.__name__ in ['Material', 'MaterialNomass', 'WindowMaterialSimpleGlazingSystem', 'WindowMaterialGlazing', 'WindowMaterialGas']:
                self.__Materials[material.name()] = material
    
    @property
    def windowshadings(self):
        return self.__WindowShadings
    
    def add_windowshading(self, windowshading):
        if windowshading.__class__.__name__ in ['WindowMaterialShade', 'WindowMaterialBlind', 'WindowMaterialScreen']:
            self.__WindowShadings[windowshading.name()] = windowshading
    
    @property
    def frames(self):
        return self.__Frames
    
    def add_frame(self, frame):
        if frame.__class__.__name__ in ['WindowPropertyFrameAndDivider']:
            self.__Frames[frame.name()] = frame
    
    @property
    def sch_year(self):
        return self.__Schedule_Year
    
    def add_sch_year(self, sch_year):
        if sch_year.__class__.__name__ in ['Year']:
            self.__Schedule_Year[sch_year.name()] = sch_year
    
    @property
    def sch_week(self):
        return self.__Schedule_Week
    
    def add_sch_week(self, sch_week):
        if sch_week.__class__.__name__ in ['Week_Daily']:
            self.__Schedule_Week[sch_week.name()] = sch_week
    
    @property
    def sch_day(self):
        return self.__Schedule_Day
    
    def add_sch_day(self, sch_day):
        if sch_day.__class__.__name__ in ['Day_Interval']:
            self.__Schedule_Day[sch_day.name()] = sch_day
    
    @property
    def sch_typelimits(self):
        return self.__Schedule_TypeLimits
    
    def add_sch_typelimits(self, sch_typelimits):
        if sch_typelimits.__class__.__name__ in ['TypeLimits']:
            self.__Schedule_TypeLimits[sch_typelimits.name()] = sch_typelimits
    
    @property
    def output_variables(self):
        return self.__output_variables
    
    def add_output_variable(self, output_variable):
        if output_variable not in self.__output_variables:
            self.__output_variables.append(output_variable)
    
    # duplicate
    def duplicate(self):
        duplicate_model = Model(self.name)

        for epclass, epobject in self.epobjects.items():
            duplicate_model.add_epobject(epclass, epobject)
        for epclass, epobject in self.simulation_control_objects.items():
            duplicate_model.add_simulation_control_object(epclass, epobject)
        for epclass, epobject in self.output_objects.items():
            duplicate_model.add_output_object(epclass, epobject)
        for epclass, epobject in self.foundation_kiva_objects.items():
            duplicate_model.add_foundation_kiva_object(epclass, epobject)
        
        for _zone in self.zones.values():
            duplicate_model.add_zone(_zone.duplicate())
        zone_breps = {z.name(): z.zonebrep() for z in self.zones.values()}
        
        for _window in self.windows.values():
            duplicate_model.add_window(_window.duplicate(zone_breps[_window.zonename()]))
        
        for _shading in self.shadings.values():
            duplicate_model.add_shading(_shading.duplicate())
        
        if self.construction_set is not None:
            duplicate_model.add_construction_set(self.construction_set.duplicate())
        
        for _construction in self.constructions.values():
            duplicate_model.add_construction(_construction.duplicate())
            
        for _material in self.materials.values():
            duplicate_model.add_material(_material.duplicate())
        
        for surface_name, exposed_foundation_perimeter in self.exposed_foundation_perimeters.items():
            duplicate_model.add_exposed_foundation_perimeters(surface_name, exposed_foundation_perimeter)
        
        for output_variable in self.output_variables:
            duplicate_model.add_output_variable(output_variable)

        duplicate_model.add_foundationzonenames(self.foundationzonenames)

        return duplicate_model
    
    # create idf file
    def to_idfobjects(self, frequency='Hourly'):
        idf_objects = copy.copy(self.epobjects)
        for zone_obj in self.zones.values():
            idf_objects = self.to_idfobjects_dict(zone_obj, idf_objects)
            
            # Internal Gain
            for internal_gain_obj in zone_obj.conditions().values():
                idf_objects = self.to_idfobjects_dict(internal_gain_obj, idf_objects)
            
            # ZoneHVAC
            for hvac_obj in zone_obj.hvac().values():
                idf_objects = self.to_idfobjects_dict(hvac_obj, idf_objects)
        
        for surface_obj in self.surfaces.values():
            idf_objects = self.to_idfobjects_dict(surface_obj, idf_objects)
        
        for window_obj in self.windows.values():
            idf_objects = self.to_idfobjects_dict(window_obj, idf_objects)
            win_shade = window_obj.windowshading()
            if win_shade is not None:
                idf_objects = self.to_idfobjects_dict(win_shade, idf_objects)
        
        for shading_obj in self.shadings.values():
            idf_objects = self.to_idfobjects_dict(shading_obj, idf_objects)
        
        for const_obj in self.constructions.values():
            idf_objects = self.to_idfobjects_dict(const_obj, idf_objects)
        
        for mat_obj in self.materials.values():
            idf_objects = self.to_idfobjects_dict(mat_obj, idf_objects)
        
        for winshad_obj in self.windowshadings.values():
            idf_objects = self.to_idfobjects_dict(winshad_obj, idf_objects)
        
        for frame_obj in self.frames.values():
            idf_objects = self.to_idfobjects_dict(frame_obj, idf_objects)
        
        for sch_year_obj in self.sch_year.values():
            idf_objects = self.to_idfobjects_dict(sch_year_obj, idf_objects)
        
        for sch_week_obj in self.sch_week.values():
            idf_objects = self.to_idfobjects_dict(sch_week_obj, idf_objects)
        
        for sch_day_obj in self.sch_day.values():
            idf_objects = self.to_idfobjects_dict(sch_day_obj, idf_objects)
        
        for sch_typelimits_obj in self.sch_typelimits.values():
            idf_objects = self.to_idfobjects_dict(sch_typelimits_obj, idf_objects)
        
        for epclass, value_dict in self.foundation_kiva_objects.items():
            idf_objects[epclass] = value_dict
        
        for value_dict in self.exposed_foundation_perimeters.values():
            epclass = 'SURFACEPROPERTY:EXPOSEDFOUNDATIONPERIMETER'
            idf_objects[epclass] = value_dict
        
        for epclass, value_dict in self.simulation_control_objects.items():
            idf_objects[epclass] = value_dict
        
        for epclass, value_dict in self.output_objects.items():
            idf_objects[epclass] = value_dict
        
        epclass = 'OUTPUT:VARIABLE'
        idf_objects[epclass] = []
        for output_variable in self.output_variables:
            value_dict = {
                'Key_Value': '*',
                'Variable_Name': f'{output_variable}',
                'Reporting_Frequency': f'{frequency}',
                'Schedule_Name': None,}
            idf_objects[epclass].append(value_dict)
        
        _idf_objects = self.sort_idfobjects(idf_objects)
        _idf_objects = self.idfobjects_to_list(_idf_objects)

        return _idf_objects
    
    def to_idfobjects_dict(self, _object, idf_objects_dict):
        if _object is not None:
            idf_object = _object.to_idfobject()
            _class = idf_object['class']
            _values = idf_object['fields']
            if _class not in idf_objects_dict.keys():
                idf_objects_dict[_class] = []
            idf_objects_dict[_class].append(_values)
        
        return idf_objects_dict
    
    def sort_idfobjects(self, idf_objects):
        _idf_objects = {}
        for k in self.epobjects_dict.keys():
            if k in idf_objects.keys():
                _idf_objects[k] = idf_objects[k]
                
        return _idf_objects
    
    def idfobjects_to_list(self, idf_objects):
        _idf_objects = {}
        for epclass, value in idf_objects.items():
            if type(value) == list:
                _idf_objects[epclass] = value
            else:
                _idf_objects[epclass] = [value]
        
        return _idf_objects

    def write_idf_file(self, path):
        _idf_objects = self.to_idfobjects()
        write_idf(_idf_objects, path)

        return _idf_objects

    # To set construction building surfaces
    def set_surface_constructions(self, foundationzonenames=[], atticzonenames=[]):
        foundation_surface_names = []
        attic_surface_names = []
        for zone in self.zones.values():
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
                    _prop = {'Construction_Name': self.construction_set.properties()[key]}
                    surface.update_properties(_prop)
                    self.add_surface(surface)
        
        for zone in self.zones.values():
            surface_type = 'Floor'
            for surface in zone.surfaces()[surface_type]:
                zone_name = surface.properties()['Zone_Name']
                pair_surface_name = surface.properties()['Outside_Boundary_Condition_Object']
                if pair_surface_name in foundation_surface_names:
                    key = 'FoundationRoof'
                    _prop = {'Construction_Name': self.construction_set.properties()[key]}
                    surface.update_properties(_prop)
                    self.add_surface(surface)
    
    def set_foundation(self):
        self.set_foundation_perimeter()

        if len(self.exposed_foundation_perimeters) > 0:
            if len(self.__foundation_kiva_objects) == 0:
                self.set_foundation_settings()

    def set_foundation_settings(self):
        self.__foundation_kiva_objects = {
            'FOUNDATION:KIVA': {
                'Name': 'FoundationKiva1',
                'Initial_Indoor_Air_Temperature': None,
                'Interior_Horizontal_Insulation_Material_Name': 'FoundationInsulation',
                'Interior_Horizontal_Insulation_Depth': 0.000,
                'Interior_Horizontal_Insulation_Width': 0.010,
                'Interior_Vertical_Insulation_Material_Name': 'FoundationInsulation',
                'Interior_Vertical_Insulation_Depth': 0.010,
                'Exterior_Horizontal_Insulation_Material_Name': 'FoundationInsulation',
                'Exterior_Horizontal_Insulation_Depth': 0.000,
                'Exterior_Horizontal_Insulation_Width': 0.000,
                'Exterior_Vertical_Insulation_Material_Name': 'FoundationInsulation',
                'Exterior_Vertical_Insulation_Depth': 0.010,
                'Wall_Height_Above_Grade': 0.2,
                'Wall_Depth_Below_Slab': 0.000,
                'Footing_Wall_Construction_Name': None,
                'Footing_Material_Name': 'Footing_Concrete',
                'Footing_Depth': 0.3,
            },
            'FOUNDATION:KIVA:SETTINGS': {
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
            },
        }
        for k ,v in self.foundation_kiva_objects.items():
            self.add_epobject(k, v)
        
        _footing_concrete_material = material.Material()
        _footing_concrete_material.set_name('Footing_Concrete')
        _footing_concrete_material.update_properties({
            'Name': 'Footing_Concrete',
            'Roughness': 'MediumRough',
            'Thickness': '0.100',
            'Conductivity': '1.6',
            'Density': '2300',
            'Specific_Heat': '880',
            'Thermal_Absorptance': '0.9',
            'Solar_Absorptance': '0.7',
            'Visible_Absorptance': '0.7',
        })
        self.add_material(_footing_concrete_material)
        _foundation_insulation_material = material.Material()
        _foundation_insulation_material.set_name('FoundationInsulation')
        _foundation_insulation_material.update_properties({
            'Name': 'FoundationInsulation',
            'Roughness': 'MediumRough',
            'Thickness': '0.030',
            'Conductivity': '0.022',
            'Density': '45',
            'Specific_Heat': '1700',
            'Thermal_Absorptance': '0.9',
            'Solar_Absorptance': '0.7',
            'Visible_Absorptance': '0.7',
        })
        self.add_material(_foundation_insulation_material)
    
    def set_foundation_perimeter(self):
        for zone_obj in self.zones.values():
            foundations = []
            walls = []
            for surface in zone_obj.surfaces()['Floor']+zone_obj.surfaces()['Wall']:
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
                    vertices_wall.append(vertices[0])
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
                    self.add_exposed_foundation_perimeters(foundation.name(), _properties)
    
    def search_surface(self, guid_brep):
        target_surface = []

        for surface in self.surfaces.values():
            if is_point_on_brep_plane(guid_brep, surface.geometry_properties()['Centroid']):
                target_surface.append(surface)
        
        return target_surface

    def update_surface_properties(self, surface_object, properties_dict):
        surface_object.update_properties(properties_dict)
    
    def update_surfaces_properties(self, guid_brep, properties_dict):
        target_surfaces = self.search_surface(guid_brep)
        for target_surface in target_surfaces:
            self.update_surface_properties(target_surface, properties_dict)


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
    'OUTER': {
        'WALL': sd.Color.FromArgb(0, 252, 218, 106),
        'ROOF': sd.Color.FromArgb(0, 168,   0,   0),
        'FLOOR': sd.Color.FromArgb(0, 168,   0,   0),
    },
    'INNER': {
        'WALL': sd.Color.FromArgb(0, 245, 144,  12),
        'CEILING': sd.Color.FromArgb(0, 230, 230, 255),
        'FLOOR': sd.Color.FromArgb(0, 230, 230, 255),
    },
    'FOUNDATION': {
        'WALL': sd.Color.FromArgb(0, 191, 191, 191),
        'CEILING': sd.Color.FromArgb(0, 230, 230, 255),
        'FLOOR': sd.Color.FromArgb(0, 90, 90, 90),
    },
    'OTHERS':{
        'AIRWALL': sd.Color.FromArgb(0, 0, 0, 0),
        'ADIABATIC': sd.Color.FromArgb(0, 100, 100, 100),
        'WINDOW': sd.Color.FromArgb(255,  12, 245, 245),
        'DOOR': sd.Color.FromArgb(255, 160,  82,  45),
        'SHADING': sd.Color.FromArgb(0, 129,  12, 245),
    },
}

def check_zones(Model):
    FoundationNames = Model.foundationzonenames
    mp = rg.MeshingParameters()
    mp.SimplePlanes = True
    mp.RefineGrid = False
    mp.MaximumEdgeLength = 0
    Mesh = []
    text_loc = []
    text = []
    buildingsurface_have_fenestrationsurface_dict = {}
    for zone in Model.zones.values():
        for surface in zone.surfaces()['Wall']+zone.surfaces()['Roof']+zone.surfaces()['Floor']:
            buildingsurface_have_fenestrationsurface_dict[surface.name()] = {'bs_object': surface, 'fs_objects': [], 'color': None}
            key = ''
            if surface.properties()['Zone_Name'] in FoundationNames:
                key1 = 'FOUNDATION'
            elif surface.properties()['Outside_Boundary_Condition'] == 'Outdoors':
                key1 = 'OUTER'
            elif surface.properties()['Outside_Boundary_Condition'] == 'Adiabatic':
                key1 = 'OTHERS'
                key2 = 'ADIABATIC'
            else:
                key1 = 'INNER'
            if key1 in ['FOUNDATION', 'OUTER', 'INNER']:
                key2 = surface.properties()['Surface_Type'].upper()
            else:
                pass
            color = part_color_dict[key1][key2]
            buildingsurface_have_fenestrationsurface_dict[surface.name()]['color'] = color
    
    for window in Model.windows.values():
        buildingsurface_have_fenestrationsurface_dict[window.properties()['Building_Surface_Name']]['fs_objects'].append(window)

        key1 = 'OTHERS'
        key2 = window.properties()['Surface_Type'].upper()
        color = part_color_dict[key1][key2]

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

    
    for shading in Model.shadings.values():
        key1 = 'OTHERS'
        key2 = 'SHADING'
        color = part_color_dict[key1][key2]

        Mesh.append(create_mesh_from_brep(shading.surfacebrep(), color))
        text_loc.append(plane_right_from_normal(shading.geometry_properties()['Centroid'], shading.geometry_properties()['Normal']))
        text.append(shading.name())
    
    return Mesh, text_loc, text
