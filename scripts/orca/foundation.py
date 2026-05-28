import math

class Foundation:
    def __init__(self, WallConstruction, BottomConstruction, InsulationMaterialInner=None, InsulationMaterialOuter=None):
        self.__properties = {
            'Name': None,
            'Outside_Layer': None,
        }
        self.__materials = {}
        self.__layer_n = 1
        self.__InsulationMaterialInner = None
        self.__InsulationMaterialOuter = None
        self.__FootingMaterial = None

        self.set_wallconstruction(WallConstruction)
        self.set_bottomconstruction(BottomConstruction)
        if InsulationMaterialInner is not None:
            self.set_insulationmaterial_inner(InsulationMaterialInner)
        if InsulationMaterialOuter is not None:
            self.set_insulationmaterial_outer(InsulationMaterialOuter)

        self._Foundationkiva = self.default_foundationkiva()
        self._Foundationkiva_settings = self.default_settings()
        self.__FoundationPerimeter = []

    def properties(self):
        return self.__properties

    def set_properties(self, key, value):
        if key not in list(self.__properties.keys()) + [f'Layer_{i}' for i in range(2, 11)]:
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        available_classes = ['Material', 'MaterialNomass', 'WindowMaterialSimpleGlazingSystem', 'WindowMaterialGlazing', 'WindowMaterialGas', 'WindowMaterialShade', 'WindowMaterialBlind', 'WindowMaterialScreen']
        if value.__class__.__name__ not in available_classes:
            raise ValueError(f'Layer must be these class: [{available_classes}]')
        
        if value.__class__.__name__ in available_classes:
            self.__properties[key] = value.name()
            self.__materials[value.name()] = value
        else:
            self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def materials(self):
        return self.__materials

    def wallconstruction(self):
        return self.__WallConstruction
    
    def bottomconstruction(self):
        return self.__BottomConstruction
    
    def insulationmaterial_inner(self):
        return self.__InsulationMaterialInner
    
    def insulationmaterial_outer(self):
        return self.__InsulationMaterialOuter
    
    def footingmaterial(self):
        return self.__FootingMaterial
    
    def foundationkiva(self):
        return self._Foundationkiva
    
    def foundationkiva_settings(self):
        return self._Foundationkiva_settings
    
    def foundation_perimeter(self):
        return self.__FoundationPerimeter
    
    def set_wallconstruction(self, construction):
        if construction.__class__.__name__ == 'Construction':
            self.__WallConstruction = construction
        else:
            raise TypeError('construction must be Construction class.')
    
    def set_bottomconstruction(self, construction):
        if construction.__class__.__name__ == 'Construction':
            self.__BottomConstruction = construction
        else:
            raise TypeError('construction must be Construction class.')
    
    def set_insulationmaterial_inner(self, material):
        if material.__class__.__name__ == 'Material':
            self.foundationkiva()['Interior_Horizontal_Insulation_Material_Name'] = material.name()
            self.foundationkiva()['Interior_Vertical_Insulation_Material_Name'] = material.name()
            self.__InsulationMaterialInner = material
        else:
            raise TypeError('material must be Material class.')
    
    def set_insulationmaterial_outer(self, material):
        if material.__class__.__name__ == 'Material':
            self.foundationkiva()['Exterior_Horizontal_Insulation_Material_Name'] = material.name()
            self.foundationkiva()['Exterior_Vertical_Insulation_Material_Name'] = material.name()
            self.__InsulationMaterialOuter = material
        else:
            raise TypeError('material must be Material class.')
    
    def set_footing_material(self, material):
        if material.__class__.__name__ == 'Material':
            self.foundationkiva()['Footing_Material_Name'] = material.name()
            self.__FootingMaterial = material
        else:
            raise TypeError('material must be Material class.')
    
    def add_perimeter(self, zone):
        surfaces = zone.surfaces()
        perimeter = 0
        foundation_surface_name = ''
        for surface in surfaces:
            if surface.outsideboundarycondition() == 'Foundation':
                foundation_surface_name = surface.name()
            if surface.facetype() =='Wall' and surface.outsideboundarycondition() == 'Outdoors':
                xs = [v.X for v in surface.vertices()]
                ys = [v.Y for v in surface.vertices()]
                _length = round(math.sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2), 3)
                perimeter += _length
        _dict = {
            'Surface_Name': foundation_surface_name,
            'Exposed_Perimeter_Calculation_Method': 'TotalExposedPerimeter',
            'Total_Exposed_Perimeter': round(perimeter, 3),
        }
        if foundation_surface_name not in [v['Surface_Name'] for v in self.foundation_perimeter()]:
            self.foundation_perimeter().append(_dict)
    
    def default_foundationkiva(self):
        _default_foundationkiva = {
            'Name': 'FoundationKiva',
            'Initial_Indoor_Air_Temperature': '',
            'Interior_Horizontal_Insulation_Material_Name': '',
            'Interior_Horizontal_Insulation_Depth': '',
            'Interior_Horizontal_Insulation_Width': '',
            'Interior_Vertical_Insulation_Material_Name': '',
            'Interior_Vertical_Insulation_Depth': '',
            'Exterior_Horizontal_Insulation_Material_Name': '',
            'Exterior_Horizontal_Insulation_Depth': '',
            'Exterior_Horizontal_Insulation_Width': '',
            'Exterior_Vertical_Insulation_Material_Name': '',
            'Exterior_Vertical_Insulation_Depth': '',
            'Wall_Height_Above_Grade': 0.2,
            'Wall_Depth_Below_Slab': 0,
            'Footing_Wall_Construction_Name': self.bottomconstruction().constructionname(),
            'Footing_Material_Name': '',
            'Footing_Depth': 0.00001,
        }
        return _default_foundationkiva
    
    def default_settings(self):
        _default_settings = {
            'Soil Conductivity': 1.0,
            'Soil Density': 1800,
            'Soil Specific Heat': 1350,
            'Ground Solar Absorptance': 0.9,
            'Ground Thermal Absorptance': 0.9,
            'Ground Surface Roughness': 0.005,
            'Far-Field Width': 40,
            'Deep-Ground Boundary Condition': 'ZeroFlux',
            'Deep-Ground Depth': 10,
            'Minimum Cell Dimension': 0.02,
            'Maximum Cell Growth Coefficient': 1.5,
            'Simulation Timesteps': 'Timestep',
        }
        return _default_settings
    
    def update_foundationkiva(self, update_dict):
        for k in update_dict.keys():
            self.foundationkiva()[k] = update_dict[k]
    
    def update_settings(self, update_dict):
        for k in update_dict.keys():
            self.foundationkiva_settings()[k] = update_dict[k]
