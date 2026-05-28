
class People:
    def __init__(self, name, zone_or_zonelist_or_space_or_spacelist_name, people_number_schedule, activity_level_schedule):
        self.__properties = {
            'Name': name,
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone_or_zonelist_or_space_or_spacelist_name,
            'Number_of_People_Schedule_Name': people_number_schedule.name(),
            'Number_of_People_Calculation_Method': 'People',
            'Number_of_People': None,
            'People_per_Floor_Area': None,
            'Floor_Area_per_Person': None,
            'Fraction_Radiant': '0.3',
            'Sensible_Heat_Fraction': 'autocalculate',
            'Activity_Level_Schedule_Name': activity_level_schedule.name(),
            'Carbon_Dioxide_Generation_Rate': '3.82e-08',
            'Enable_ASHRAE_55_Comfort_Warnings': 'No',
            'Mean_Radiant_Temperature_Calculation_Type': 'EnclosureAveraged',
            'Surface_NameAngle_Factor_List_Name': None,
            'Work_Efficiency_Schedule_Name': None,
            'Clothing_Insulation_Calculation_Method': 'ClothingInsulationSchedule',
            'Clothing_Insulation_Calculation_Method_Schedule_Name': None,
            'Clothing_Insulation_Schedule_Name': None,
            'Air_Velocity_Schedule_Name': None,
            'Thermal_Comfort_Model_1_Type': None,
            'Thermal_Comfort_Model_2_Type': None,
            'Thermal_Comfort_Model_3_Type': None,
            'Thermal_Comfort_Model_4_Type': None,
            'Thermal_Comfort_Model_5_Type': None,
            'Thermal_Comfort_Model_6_Type': None,
            'Thermal_Comfort_Model_7_Type': None,
            'Ankle_Level_Air_Velocity_Schedule_Name': None,
            'Cold_Stress_Temperature_Threshold': '15.56',
            'Heat_Stress_Temperature_Threshold': '30.0',
        }
        self.__schedules = {
            'Number_of_People_Schedule': people_number_schedule,
            'Activity_Level_Schedule': activity_level_schedule,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Number_of_People_Calculation_Method':
            methods = ['People', 'People/Area', 'Area/Person']
            if value not in methods:
                raise ValueError(f'Design_Level_Calculation_Method must be one of the following in {methods}.')
        
        if key == 'Number_of_People_Schedule_Name' or key == 'Activity_Level_Schedule_Name':
            self.set_schedule(key, value)
        else:
            self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedules(self):
        return self.__schedules
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_value(self, method, value):
        methods = ['People', 'People/Area', 'Area/Person']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Number_of_People_Calculation_Method'] = method

        if method == 'People':
            self.__properties['Number_of_People'] = value
        elif method == 'People/Area':
            self.__properties['People_per_Floor_Area'] = value
        elif method == 'Area/Person':
            self.__properties['Floor_Area_per_Person'] = value
    
    def set_schedule(self, key, schedule):
        self.__properties[key] = schedule.name()
        if key == 'Number_of_People_Schedule_Name':
            self.__schedules['Number_of_People_Schedule'] = schedule
        elif key == 'Activity_Level_Schedule_Name':
            self.__schedules['Activity_Level_Schedule'] = schedule
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'PEOPLE',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_people = People(self.name(), self.properties()['Zone_or_ZoneList_or_Space_or_SpaceList_Name'],
                                  self.schedules()['Number_of_People_Schedule'], self.schedules()['Activity_Level_Schedule'])
        duplicate_people.update_properties(self.properties())
        return duplicate_people

class Lights:
    def __init__(self, name, zone_or_zonelist_or_space_or_spacelist_name, schedule):
        self.__properties = {
            'Name': name,
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone_or_zonelist_or_space_or_spacelist_name,
            'Schedule_Name': schedule.name(),
            'Design_Level_Calculation_Method': 'LightingLevel',
            'Lighting_Level': None,
            'Watts_per_Floor_Area': None,
            'Watts_per_Person': None,
            'Return_Air_Fraction': '0.0',
            'Fraction_Radiant': '0.0',
            'Fraction_Visible': '0.0',
            'Fraction_Replaceable': '1.0',
            'EndUse_Subcategory': 'General',
            'Return_Air_Fraction_Calculated_from_Plenum_Temperature': 'No',
            'Return_Air_Fraction_Function_of_Plenum_Temperature_Coefficient_1': '0.0',
            'Return_Air_Fraction_Function_of_Plenum_Temperature_Coefficient_2': '0.0',
            'Return_Air_Heat_Gain_Node_Name': None,
            'Exhaust_Air_Heat_Gain_Node_Name': None,
        }
        self.__schedule = schedule
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Design_Level_Calculation_Method':
            methods = ['LightingLevel', 'Watts/Area', 'Watts/Person']
            if value not in methods:
                raise ValueError(f'Design_Level_Calculation_Method must be one of the following in {methods}.')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedule(self):
        return self.__schedule
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_value(self, method, value):
        methods = ['LightingLevel', 'Watts/Area', 'Watts/Person']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Design_Level_Calculation_Method'] = method

        if method == 'LightingLevel':
            self.__properties['Lighting_Level'] = value
        elif method == 'Watts/Area':
            self.__properties['Watts_per_Floor_Area'] = value
        elif method == 'Watts/Person':
            self.__properties['Watts_per_Person'] = value
    
    def set_schedule(self, schedule):
        self.__properties['Schedule_Name'] = schedule
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'LIGHTS',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_lights = Lights(self.name(), self.properties()['Zone_or_ZoneList_or_Space_or_SpaceList_Name'], self.schedule())
        duplicate_lights.update_properties(self.properties())
        return duplicate_lights

class ElectricEquipment:
    def __init__(self, name, zone_or_zonelist_or_space_or_spacelist_name, schedule):
        self.__properties = {
            'Name': name,
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone_or_zonelist_or_space_or_spacelist_name,
            'Schedule_Name': schedule.name(),
            'Design_Level_Calculation_Method': 'EquipmentLevel',
            'Design_Level': None,
            'Watts_per_Floor_Area': None,
            'Watts_per_Person': None,
            'Fraction_Latent': '0.0',
            'Fraction_Radiant': '0.0',
            'Fraction_Lost': '0.0',
            'EndUse_Subcategory': 'General',
        }
        self.__schedule = schedule
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Design_Level_Calculation_Method':
            methods = ['EquipmentLevel', 'Watts/Area', 'Watts/Person']
            if value not in methods:
                raise ValueError(f'Design_Level_Calculation_Method must be one of the following in {methods}.')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedule(self):
        return self.__schedule
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_value(self, method, value):
        methods = ['EquipmentLevel', 'Watts/Area', 'Watts/Person']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Design_Level_Calculation_Method'] = method

        if method == 'EquipmentLevel':
            self.__properties['Design_Level'] = value
        elif method == 'Watts/Area':
            self.__properties['Watts_per_Floor_Area'] = value
        elif method == 'Watts/Person':
            self.__properties['Watts_per_Person'] = value
    
    def set_schedule(self, schedule):
        self.__properties['Schedule_Name'] = schedule
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ELECTRICEQUIPMENT',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_ee = ElectricEquipment(self.name(), self.properties()['Zone_or_ZoneList_or_Space_or_SpaceList_Name'], self.schedule())
        duplicate_ee.update_properties(self.properties())
        return duplicate_ee

# if __name__ == '__main__':
#     import os
#     import json
#     epobjects_path = os.path.join(os.path.dirname(__file__), 'epobjects.json')
#     with open(epobjects_path, mode='r', encoding='utf-8') as f:
#         epobjects = json.load(f)
#     for k, v in epobjects['ELECTRICEQUIPMENT'].items():
#         print(f"            '{k}': '{v}',")
