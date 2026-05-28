import math

class Constructions:
    def __init__(self):
        self.__properties = {
            'OuterWall': None,
            'OuterRoof': None,
            'OuterFloor': None,
            'InnerWall': None,
            'InnerRoof': None,
            'InnerFloor': None,
            'FoundationWall': None,
            'FoundationRoof': None,
            'FoundationFloor': None,
        }
        self.__constructions = {}
        self.__windowshadings = {}
        self.__frame_and_divider = {}
        self.materials = {}
        self.__U_dict = {}
    
    def properties(self):
        return self.__properties
    
    def windowshadings(self):
        return self.__windowshadings
    
    def frame_and_divider(self):
        return self.__frame_and_divider
    
    def set_properties(self, key, value):
        if key not in self.properties().keys():
            raise KeyError(f'{key} is not in properties keys.')
        if value.__class__.__name__ not in ['Construction', 'ConstructionWindow']:
            raise ValueError(f'value must be Construction class.')
        
        self.__properties[key] = value.name()
        self.__constructions[value.name()] = value
        self.set_U_dict(value)
        for name, material in value.materials().items():
            self.materials[name] = material
    
    def U_dict(self):
        return self.__U_dict
    
    def set_U_dict(self, Construction):
        R = Construction.resistance()
        self.__U_dict[Construction.name()] = math.ceil(1/R*1000) / 1000
    
    def add_window_construction(self, key, value):
        if value.__class__.__name__ not in ['Construction', 'ConstructionWindow']:
            raise ValueError(f'value must be Construction class.')
        
        self.__properties[key] = value.name()
        self.__constructions[value.name()] = value
        for name, material in value.materials().items():
            self.materials[name] = material
    
    def add_windowshading(self, windowshading):
        if windowshading.__class__.__name__ not in ['WindowMaterialShade', 'WindowMaterialBlind', 'WindowMaterialScreen']:
            raise ValueError(f'frame_and_divider must be WindowPropertyFrameAndDivider class.')
        
        self.__windowshadings[windowshading.name()] = windowshading
    
    def add_frame_and_divider(self, frame_and_divider):
        if frame_and_divider.__class__.__name__ not in ['WindowPropertyFrameAndDivider']:
            raise ValueError(f'frame_and_divider must be WindowPropertyFrameAndDivider class.')
        
        self.__frame_and_divider[frame_and_divider.name()] = frame_and_divider
    
    def constructions(self):
        return self.__constructions
    
    def add_construction(self, construction):
        self.__constructions[construction.name()] = construction
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def duplicate(self):
        duplicate_constructions = Constructions()
        duplicate_constructions.update_properties(self.properties())
        for k, v in self.properties().items():
            if v is not None:
                duplicate_constructions.set_properties(k, self.constructions()[v])
        for k, v in self.windowshadings().items():
            duplicate_constructions.add_windowshading(v)
        for k, v in self.frame_and_divider().items():
            duplicate_constructions.add_frame_and_divider(v)
        for _construction in self.constructions().values():
            duplicate_constructions.set_U_dict(_construction)
        return duplicate_constructions
