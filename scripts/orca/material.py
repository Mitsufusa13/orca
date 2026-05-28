class Material:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Roughness': 'MediumRough',
            'Thickness': None,
            'Conductivity': None,
            'Density': None,
            'Specific_Heat': None,
            'Thermal_Absorptance': 0.9,
            'Solar_Absorptance': 0.7,
            'Visible_Absorptance': 0.7,
        }
        self.__resistance = None
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        if key == 'Roughness':
            roughnesses = ['VeryRough', 'Rough', 'MediumRough', 'MediumSmooth', 'Smooth', 'VerySmooth']
            if value not in roughnesses:
                raise ValueError(f'roughness must be one of the following in {roughnesses}.')
        elif key == 'Thickness':
            if value <= 0:
                raise ValueError(f'thickness must be greater than 0.')
        elif key == 'Conductivity':
            if value <= 0:
                raise ValueError(f'conductivity must be greater than 0.')
        elif key == 'Density':
            if value <= 0:
                raise ValueError(f'density must be greater than 0.')
        elif key == 'Specific_Heat':
            if value < 100:
                raise ValueError(f'specific_heat must be greater than or equal to 100.')
        elif key == 'Thermal_Absorptance':
            if value <= 0 or 0.99999 < value:
                raise ValueError(f'thermal_absorptance must be greater than 0 and less than or equal to 0.99999.')
        elif key == 'Solar_Absorptance':
            if value < 0 or  1 < value:
                raise ValueError(f'solar_absorptance must be greater than or equal to 0 and less than or equal to 1.')
        elif key == 'Visible_Absorptance':
            if value < 0 or  1 < value:
                raise ValueError(f'visible_absorptance must be greater than or equal to 0 and less than or equal to 1.')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name

    def resistance(self):
        return self.__resistance
    
    def calculate_resistance(self):
        _thickness = self.properties()['Thickness']
        _lambda = self.properties()['Conductivity']
        if _thickness is None:
            raise ValueError('Thickness has not yet been set.')
        if _lambda is None:
            raise ValueError('Conductivity has not yet been set.')
        R = _thickness / _lambda
        self.__resistance = R
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'MATERIAL',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = Material()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

class MaterialNomass:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Roughness': 'MediumRough',
            'ThermalResistance': None,
            'Thermal_Absorptance': 0.9,
            'Solar_Absorptance': 0.7,
            'Visible_Absorptance': 0.7,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        if key == 'Roughness':
            roughnesses = ['VeryRough', 'Rough', 'MediumRough', 'MediumSmooth', 'Smooth', 'VerySmooth']
            if value not in roughnesses:
                raise ValueError(f'roughness must be one of the following in {roughnesses}.')
        elif key == 'ThermalResistance':
            if value <= 0:
                raise ValueError(f'thermal_resistance must be greater than 0.')
        elif key == 'Thermal_Absorptance':
            if value <= 0 or 0.99999 < value:
                raise ValueError(f'thermal_absorptance must be greater than 0 and less than or equal to 0.99999.')
        elif key == 'Solar_Absorptance':
            if value < 0 or  1 < value:
                raise ValueError(f'solar_absorptance must be greater than or equal to 0 and less than or equal to 1.')
        elif key == 'Visible_Absorptance':
            if value < 0 or  1 < value:
                raise ValueError(f'visible_absorptance must be greater than or equal to 0 and less than or equal to 1.')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def resistance(self):
        return self.properties()['ThermalResistance']
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'MATERIAL:NOMASS',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = MaterialNomass()
        duplicate_material.update_properties(self.properties())
        return duplicate_material
    

class WindowMaterialSimpleGlazingSystem:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'UFactor': None,
            'Solar_Heat_Gain_Coefficient': None,
            'Visible_Transmittance': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        if key == 'UFactor':
            if value <= 0:
                raise ValueError(f'u_factor must be greater than 0.')
        elif key == 'Solar_Heat_Gain_Coefficient':
            if value <= 0 or 1.0 <= value:
                raise ValueError(f'shgc must be greater than 0 and less than 1. value: {value}')
        elif key == 'Visible_Transmittance':
            if value <= 0 or 1.0 <= value:
                raise ValueError(f'vt must be greater than 0 and less than 1.')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def resistance(self):
        R = 1 / self.properties()['UFactor'] - (0.11 + 0.04)
        return R
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = WindowMaterialSimpleGlazingSystem()
        duplicate_material.update_properties(self.properties())
        return duplicate_material
    
class WindowMaterialGlazing:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Optical_Data_Type': 'SpectralAverage',
            'Window_Glass_Spectral_Data_Set_Name': None,
            'Thickness': None,
            'Solar_Transmittance_at_Normal_Incidence': None,
            'Front_Side_Solar_Reflectance_at_Normal_Incidence': None,
            'Back_Side_Solar_Reflectance_at_Normal_Incidence': None,
            'Visible_Transmittance_at_Normal_Incidence': None,
            'Front_Side_Visible_Reflectance_at_Normal_Incidence': None,
            'Back_Side_Visible_Reflectance_at_Normal_Incidence': None,
            'Infrared_Transmittance_at_Normal_Incidence': None,
            'Front_Side_Infrared_Hemispherical_Emissivity': 0.84,
            'Back_Side_Infrared_Hemispherical_Emissivity': 0.84,
            'Conductivity': 0.9,
            'Dirt_Correction_Factor_for_Solar_and_Visible_Transmittance': 1,
            'Solar_Diffusing': 'No',
            'Youngs_modulus': 72000000000,
            'Poissons_ratio': 0.22,
            'Window_Glass_Spectral_and_Incident_Angle_Transmittance_Data_Set_Table_Name': None,
            'Window_Glass_Spectral_and_Incident_Angle_Front_Reflectance_Data_Set_Table_Name': None,
            'Window_Glass_Spectral_and_Incident_Angle_Back_Reflectance_Data_Set_Table_Name': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWMATERIAL:GLAZING',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = WindowMaterialGlazing()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

class WindowMaterialGas:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Gas_Type': None,
            'Thickness': None,
            'Conductivity_Coefficient_A': None,
            'Conductivity_Coefficient_B': None,
            'Conductivity_Coefficient_C': None,
            'Viscosity_Coefficient_A': None,
            'Viscosity_Coefficient_B': None,
            'Viscosity_Coefficient_C': None,
            'Specific_Heat_Coefficient_A': None,
            'Specific_Heat_Coefficient_B': None,
            'Specific_Heat_Coefficient_C': None,
            'Molecular_Weight': None,
            'Specific_Heat_Ratio': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWMATERIAL:GAS',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = WindowMaterialGas()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

class WindowMaterialShade:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Solar_Transmittance': None,
            'Solar_Reflectance': None,
            'Visible_Transmittance': None,
            'Visible_Reflectance': None,
            'Infrared_Hemispherical_Emissivity': None,
            'Infrared_Transmittance': None,
            'Thickness': None,
            'Conductivity': None,
            'Shade_to_Glass_Distance': 0.05,
            'Top_Opening_Multiplier': 0.5,
            'Bottom_Opening_Multiplier': 0.5,
            'LeftSide_Opening_Multiplier': 0.5,
            'RightSide_Opening_Multiplier': 0.5,
            'Airflow_Permeability': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWMATERIAL:SHADE',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = WindowMaterialShade()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

class WindowMaterialBlind:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Slat_Orientation': None,
            'Slat_Width': None,
            'Slat_Separation': None,
            'Slat_Thickness': None,
            'Slat_Angle': None,
            'Slat_Conductivity': None,
            'Slat_Beam_Solar_Transmittance': None,
            'Front_Side_Slat_Beam_Solar_Reflectance': None,
            'Back_Side_Slat_Beam_Solar_Reflectance': None,
            'Slat_Diffuse_Solar_Transmittance': None,
            'Front_Side_Slat_Diffuse_Solar_Reflectance': None,
            'Back_Side_Slat_Diffuse_Solar_Reflectance': None,
            'Slat_Beam_Visible_Transmittance': None,
            'Front_Side_Slat_Beam_Visible_Reflectance': None,
            'Back_Side_Slat_Beam_Visible_Reflectance': None,
            'Slat_Diffuse_Visible_Transmittance': None,
            'Front_Side_Slat_Diffuse_Visible_Reflectance': None,
            'Back_Side_Slat_Diffuse_Visible_Reflectance': None,
            'Slat_Infrared_Hemispherical_Transmittance': None,
            'Front_Side_Slat_Infrared_Hemispherical_Emissivity': None,
            'Back_Side_Slat_Infrared_Hemispherical_Emissivity': None,
            'Blind_to_Glass_Distance': None,
            'Blind_Top_Opening_Multiplier': None,
            'Blind_Bottom_Opening_Multiplier': None,
            'Blind_Left_Side_Opening_Multiplier': None,
            'Blind_Right_Side_Opening_Multiplier': None,
            'Minimum_Slat_Angle': None,
            'Maximum_Slat_Angle': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWMATERIAL:BLIND',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = WindowMaterialBlind()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

class WindowMaterialScreen:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Reflected_Beam_Transmittance_Accounting_Method': None,
            'Diffuse_Solar_Reflectance': None,
            'Diffuse_Visible_Reflectance': None,
            'Thermal_Hemispherical_Emissivity': None,
            'Conductivity': None,
            'Screen_Material_Spacing': None,
            'Screen_Material_Diameter': None,
            'Screen_to_Glass_Distance': None,
            'Top_Opening_Multiplier': None,
            'Bottom_Opening_Multiplier': None,
            'Left_Side_Opening_Multiplier': None,
            'Right_Side_Opening_Multiplier': None,
            'Angle_of_Resolution_for_Screen_Transmittance_Output_Map': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWMATERIAL:SCREEN',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_material = WindowMaterialScreen()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

class WindowPropertyFrameAndDivider:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Frame_Width': None,
            'Frame_Outside_Projection': None,
            'Frame_Inside_Projection': None,
            'Frame_Conductance': None,
            'Ratio_of_FrameEdge_Glass_Conductance_to_CenterOfGlass_Conductance': None,
            'Frame_Solar_Absorptance': None,
            'Frame_Visible_Absorptance': None,
            'Frame_Thermal_Hemispherical_Emissivity': None,
            'Divider_Type': None,
            'Divider_Width': None,
            'Number_of_Horizontal_Dividers': None,
            'Number_of_Vertical_Dividers': None,
            'Divider_Outside_Projection': None,
            'Divider_Inside_Projection': None,
            'Divider_Conductance': None,
            'Ratio_of_DividerEdge_Glass_Conductance_to_CenterOfGlass_Conductance': None,
            'Divider_Solar_Absorptance': None,
            'Divider_Visible_Absorptance': None,
            'Divider_Thermal_Hemispherical_Emissivity': None,
            'Outside_Reveal_Solar_Absorptance': None,
            'Inside_Sill_Depth': None,
            'Inside_Sill_Solar_Absorptance': None,
            'Inside_Reveal_Depth': None,
            'Inside_Reveal_Solar_Absorptance': None,
            'NFRC_Product_Type_for_Assembly_Calculations': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'WINDOWPROPERTY:FRAMEANDDIVIDER',
            'fields': self.properties(),
        }
        return idfobject

    def duplicate(self):
        duplicate_material = WindowPropertyFrameAndDivider()
        duplicate_material.update_properties(self.properties())
        return duplicate_material

