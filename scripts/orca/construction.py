import math

class Construction:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Outside_Layer': None,
        }
        self.__materials = {}
        self.__layer_n = 0
        self.__resistance = None
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        layer_names = [k for k in self.__properties.keys()]+[f'Layer_{i}' for i in range(2, 11)]
        if key not in layer_names:
            raise KeyError(f'key must be in [{layer_names}]')
        
        available_classes = ['Material', 'MaterialNomass', 'WindowMaterialSimpleGlazingSystem']
        if value.__class__.__name__ not in available_classes:
            raise ValueError(f'Layer must be these class: [{available_classes}]')
        
        if value.__class__.__name__ in available_classes:
            self.__properties[key] = value.name()
            self.__materials[key] = value
            self.__layer_n += 1
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def materials(self):
        return self.__materials
    
    def layers_number(self):
        return self.__layer_n
    
    def set_outside_layer(self, material):
        self.set_properties('Outside_Layer', material)
    
    def add_inner_layer(self, material):
        self.set_properties(f'Layer_{self.layers_number()+1}', material)
    
    def add_outer_layer(self, material):
        _properties = {}
        for i in range(1, self.layers_number()+1):
            if i == 1:
                _properties[f'Layer_{i+1}'] = self.properties()['Outside_Layer']
            else:
                _properties[f'Layer_{i+1}'] = self.properties()[f'Layer_{i}']

        self.update_properties(_properties)
        self.set_outside_layer(material)

    def resistance(self):
        return self.__resistance

    def calculate_resistance(self, r_i, r_o, coef):
        R = r_i + r_o
        for k in self.properties().keys():
            if 'Layer' in k:
                R += self.materials()[k].resistance()
        R /= coef
        R = math.floor(R*1000) / 1000
        self.__resistance = R
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'CONSTRUCTION',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_construction = Construction()
        duplicate_construction.update_properties(self.properties())
        return duplicate_construction

class ConstructionWindow:
    def __init__(self):
        self.__properties = {
            'Name': None,
            'Outside_Layer': None,
        }
        self.__materials = {}
        self.__layer_n = 0
        self.__resistance = None
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        layer_names = [k for k in self.__properties.keys()]+[f'Layer_{i}' for i in range(2, 11)]
        if key not in layer_names:
            raise KeyError(f'key must be in [{layer_names}]')
        
        available_classes = ['WindowMaterialGlazing', 'WindowMaterialGas', 'WindowMaterialShade', 'WindowMaterialBlind', 'WindowMaterialScreen']
        if value.__class__.__name__ not in available_classes:
            raise ValueError(f'Layer must be these class: [{available_classes}]')
        
        if value.__class__.__name__ in available_classes:
            self.__properties[key] = value.name()
            self.__materials[key] = value
            self.__layer_n += 1
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def materials(self):
        return self.__materials
    
    def layers_number(self):
        return self.__layer_n
    
    def set_outside_layer(self, material):
        self.set_properties('Outside_Layer', material)
    
    def add_inner_layer(self, material):
        self.set_properties(f'Layer_{self.layers_number()+1}', material)
    
    def add_outer_layer(self, material):
        _properties = {}
        for i in range(1, self.layers_number()+1):
            if i == 1:
                _properties[f'Layer_{i+1}'] = self.properties()['Outside_Layer']
            else:
                _properties[f'Layer_{i+1}'] = self.properties()[f'Layer_{i}']

        self.update_properties(_properties)
        self.set_outside_layer(material)

    def resistance(self):
        return self.__resistance

    def calculate_resistance(self, U, coef):
        R = 1 / U
        R /= coef
        R = math.floor(R*1000) / 1000
        self.__resistance = R

    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}

    def to_idfobject(self):
        idfobject = {
            'class': 'CONSTRUCTION',
            'fields': self.properties(),
        }
        return idfobject

    def duplicate(self):
        duplicate_construction = ConstructionWindow()
        duplicate_construction.update_properties(self.properties())
        return duplicate_construction
