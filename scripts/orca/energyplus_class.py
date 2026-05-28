import os
import json


def read_epobjects():
    epobjects_path = os.path.join(os.path.dirname(__file__), 'epobjects.json')
    with open(epobjects_path, mode='r', encoding='utf-8') as f:
        epobjects = json.load(f)
    return epobjects

class EnergyPlusClass:
    def __init__(self):
        self.__properties = {
        }
        self.__epclass = None
    
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
    
    def epclass(self):
        return self.__epclass
    
    def set_epclass(self, epclass):
        epclass = epclass.upper()
        if epclass not in [k.upper() for k in read_epobjects().keys()]:
            raise ValueError(f'energyPlus class has not {epclass}.')
        
        self.__epclass = epclass
        self.__properties = read_epobjects()[epclass]
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def property_fields(self):
        fields = []
        for k in self.properties().keys():
            fields.append(k)
        return fields
    
    def property_values(self):
        values = []
        for v in self.properties().values():
            values.append(v)
        return values
    
    def to_idfobject(self):
        idfobject = {
            'class': self.epclass(),
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = EnergyPlusClass()
        duplicate_class.set_epclass(self.epclass())
        duplicate_class.update_properties(self.properties())
        return duplicate_class

