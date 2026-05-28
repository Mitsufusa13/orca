class ZoneInfiltrationDesignFlowRate:
    def __init__(self, name, zone_or_zonelist_or_space_or_spacelist_name, schedule):
        self.__properties = {
            'Name': name,
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone_or_zonelist_or_space_or_spacelist_name,
            'Schedule_Name': schedule.name(),
            'Design_Flow_Rate_Calculation_Method': 'Flow/Zone',
            'Design_Flow_Rate': '',
            'Flow_Rate_per_Floor_Area': '',
            'Flow_Rate_per_Exterior_Surface_Area': '',
            'Air_Changes_per_Hour': '',
            'Constant_Term_Coefficient': '1.0',
            'Temperature_Term_Coefficient': '0.0',
            'Velocity_Term_Coefficient': '0.0',
            'Velocity_Squared_Term_Coefficient': '0.0',
        }
        self.__schedule = schedule
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Design_Flow_Rate_Calculation_Method':
            methods = ['Flow/Zone', 'Flow/Area', 'Flow/ExteriorArea', 'Flow/ExteriorWallArea', 'AirChanges/Hour']
            if value not in methods:
                raise ValueError(f'Design_Flow_Rate_Calculation_Method must be one of the following in {methods}.')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedule(self):
        return self.__schedule
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_value(self, method, value):
        methods = ['Flow/Zone', 'Flow/Area', 'Flow/ExteriorArea', 'Flow/ExteriorWallArea', 'AirChanges/Hour']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Design_Flow_Rate_Calculation_Method'] = method

        if method == 'Flow/Zone':
            self.__properties['Design_Flow_Rate'] = value
        elif method == 'Flow/Area':
            self.__properties['Flow_Rate_per_Floor_Area'] = value
        elif method == 'Flow/ExteriorArea':
            self.__properties['Flow_Rate_per_Exterior_Surface_Area'] = value
        elif method == 'Flow/ExteriorWallArea':
            self.__properties['Flow_Rate_per_Exterior_Surface_Area'] = value
        elif method == 'AirChanges/Hour':
            self.__properties['Air_Changes_per_Hour'] = value
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONEINFILTRATION:DESIGNFLOWRATE',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = ZoneInfiltrationDesignFlowRate(self.name(), self.properties()['Zone_or_ZoneList_or_Space_or_SpaceList_Name'], self.schedule())
        duplicate_class.update_properties(self.properties())
        return duplicate_class


class EquipmentList:
    def __init__(self, list_name):
        self.__properties = {
            'Name': list_name,
            'Load_Distribution_Scheme': 'SequentialLoad',
        }

        self.__equipment_object = {}
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Load_Distribution_Scheme':
            self.set_load_distribution_scheme(value)
        elif 'Zone_Equipment' in key:
            self.add_zone_equipment()

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_load_distribution_scheme(self, scheme):
        schemes = ['SequentialLoad', 'UniformLoad', 'UniformPLR', 'SequentialUniformPLR']
        if scheme not in schemes:
            raise ValueError(f'scheme must be one of the following in {schemes}.')

        self.__properties['Load_Distribution_Scheme'] = scheme
    
    def add_zone_equipment(self, equipment_object):
        equipment_object_type = equipment_object.epclass()
        equipment_name = equipment_object.name()
        n = (len(self.properties()) - 2) // 6 + 1
        equipment_object_types = [
            'ZONEHVAC:TERMINALUNIT:VARIABLEREFRIGERANTFLOW',
            'ZONEHVAC:AIRDISTRIBUTIONUNIT',
            'ZONEHVAC:ENERGYRECOVERYVENTILATOR',
            'ZONEHVAC:EVAPORATIVECOOLERUNIT',
            'ZONEHVAC:HYBRIDUNITARYHVAC',
            'ZONEHVAC:FORCEDAIR:USERDEFINED',
            'ZONEHVAC:FOURPIPEFANCOIL',
            'ZONEHVAC:OUTDOORAIRUNIT',
            'ZONEHVAC:PACKAGEDTERMINALAIRCONDITIONER',
            'ZONEHVAC:PACKAGEDTERMINALHEATPUMP',
            'ZONEHVAC:UNITHEATER',
            'ZONEHVAC:UNITVENTILATOR',
            'ZONEHVAC:VENTILATEDSLAB',
            'ZONEHVAC:WATERTOAIRHEATPUMP',
            'ZONEHVAC:WINDOWAIRCONDITIONER',
            'ZONEHVAC:BASEBOARD:RADIANTCONVECTIVE:ELECTRIC',
            'ZONEHVAC:BASEBOARD:RADIANTCONVECTIVE:WATER',
            'ZONEHVAC:BASEBOARD:RADIANTCONVECTIVE:STEAM',
            'ZONEHVAC:COOLINGPANEL:RADIANTCONVECTIVE:WATER',
            'ZONEHVAC:BASEBOARD:CONVECTIVE:ELECTRIC',
            'ZONEHVAC:BASEBOARD:CONVECTIVE:WATER',
            'ZONEHVAC:HIGHTEMPERATURERADIANT',
            'ZONEHVAC:LOWTEMPERATURERADIANT:VARIABLEFLOW',
            'ZONEHVAC:LOWTEMPERATURERADIANT:CONSTANTFLOW',
            'ZONEHVAC:LOWTEMPERATURERADIANT:ELECTRIC',
            'ZONEHVAC:DEHUMIDIFIER:DX',
            'ZONEHVAC:IDEALLOADSAIRSYSTEM',
            'ZONEHVAC:REFRIGERATIONCHILLERSET',
            'FAN:ZONEEXHAUST',
            'WATERHEATER:HEATPUMP:PUMPEDCONDENSER',
            'WATERHEATER:HEATPUMP:WRAPPEDCONDENSER',
            'HEATEXCHANGER:AIRTOAIR:FLATPLATE',
            'AIRLOOPHVAC:UNITARYSYSTEM',
        ]
        if equipment_object_type not in equipment_object_types:
            raise ValueError(f'{equipment_object_type}:equipment_object_type must be one of the following in {equipment_object_types}.')
        
        self.__equipment_object[f'Zone_Equipment_{n}_Object'] = equipment_object
        self.__properties[f'Zone_Equipment_{n}_Object_Type'] = equipment_object_type
        self.__properties[f'Zone_Equipment_{n}_Name'] = equipment_name
        self.__properties[f'Zone_Equipment_{n}_Cooling_Sequence'] = n
        self.__properties[f'Zone_Equipment_{n}_Heating_or_NoLoad_Sequence'] = n
        self.__properties[f'Zone_Equipment_{n}_Sequential_Cooling_Fraction_Schedule_Name'] = None
        self.__properties[f'Zone_Equipment_{n}_Sequential_Heating_Fraction_Schedule_Name'] = None
        
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONEHVAC:EQUIPMENTLIST',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = EquipmentList(self.name())
        duplicate_class.update_properties(self.properties())
        return duplicate_class


class EquipmentConnections:
    def __init__(self, name, equipment_list_name, exhaust=False):
        self.__properties = {
            'Zone_Name': f'{name}',
            'Zone_Conditioning_Equipment_List_Name': equipment_list_name,
            'Zone_Air_Inlet_Node_or_NodeList_Name': f'{name}_Inlet_Node',
            'Zone_Air_Exhaust_Node_or_NodeList_Name': f'{name}_Exhaust_Node' if exhaust else None,
            'Zone_Air_Node_Name': f'{name}_Air_Node',
            'Zone_Return_Air_Node_or_NodeList_Name': f'{name}_Return_Node',
            'Zone_Return_Air_Node_1_Flow_Rate_Fraction_Schedule_Name': None,
            'Zone_Return_Air_Node_1_Flow_Rate_Basis_Node_or_NodeList_Name': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Zone_Name']
    
    def set_name(self, name):
        self.__properties['Zone_Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONEHVAC:EQUIPMENTCONNECTIONS',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = EquipmentConnections(self.name(), self.properties()['Zone_Conditioning_Equipment_List_Name'])
        duplicate_class.update_properties(self.properties())
        return duplicate_class


class IdealLoadsAirSystem:
    def __init__(self, name, availability_schedule,
                 zone_supply_air_node_name, zone_exhaust_air_node_name=None,
                 heating_availability_schedule=None, cooling_availability_schedule=None):
        self.__properties = {
            'Name': name,
            'Availability_Schedule_Name': availability_schedule.name() if availability_schedule is not None else None,
            'Zone_Supply_Air_Node_Name': zone_supply_air_node_name,
            'Zone_Exhaust_Air_Node_Name': zone_exhaust_air_node_name,
            'System_Inlet_Air_Node_Name': None,
            'Maximum_Heating_Supply_Air_Temperature': '50.0',
            'Minimum_Cooling_Supply_Air_Temperature': '13.0',
            'Maximum_Heating_Supply_Air_Humidity_Ratio': '0.0156',
            'Minimum_Cooling_Supply_Air_Humidity_Ratio': '0.0077',
            'Heating_Limit': 'NoLimit',
            'Maximum_Heating_Air_Flow_Rate': None,
            'Maximum_Sensible_Heating_Capacity': None,
            'Cooling_Limit': 'NoLimit',
            'Maximum_Cooling_Air_Flow_Rate': None,
            'Maximum_Total_Cooling_Capacity': None,
            'Heating_Availability_Schedule_Name': heating_availability_schedule.name() if heating_availability_schedule is not None else None,
            'Cooling_Availability_Schedule_Name': cooling_availability_schedule.name() if cooling_availability_schedule is not None else None,
            'Dehumidification_Control_Type': 'ConstantSensibleHeatRatio',
            'Cooling_Sensible_Heat_Ratio': '0.7',
            'Humidification_Control_Type': 'None',
            'Design_Specification_Outdoor_Air_Object_Name': None,
            'Outdoor_Air_Inlet_Node_Name': None,
            'Demand_Controlled_Ventilation_Type': 'None',
            'Outdoor_Air_Economizer_Type': 'NoEconomizer',
            'Heat_Recovery_Type': 'None',
            'Sensible_Heat_Recovery_Effectiveness': '0.7',
            'Latent_Heat_Recovery_Effectiveness': '0.65',
            'Design_Specification_ZoneHVAC_Sizing_Object_Name': None,
        }
        self.__schedules = {
            'Availability_Schedule': availability_schedule,
            'Heating_Availability_Schedule': heating_availability_schedule,
            'Cooling_Availability_Schedule': cooling_availability_schedule,
        }
        self.__epclass = 'ZONEHVAC:IDEALLOADSAIRSYSTEM'
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedules(self):
        return self.__schedules
    
    def epclass(self):
        return self.__epclass
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_schedule(self, key, schedule):
        self.__schedules[key] = schedule
        self.set_properties(f'{key}_Name', schedule.name())
    
    def set_heating_limit(self, method, air_flow_rate=None, capacity=None):
        methods = ['NoLimit', 'LimitFlowRate', 'LimitCapacity', 'LimitFlowRateAndCapacity']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Heating_Limit'] = method

        if method == 'NoLimit':
            pass
        elif method == 'LimitFlowRate':
            if air_flow_rate is None:
                raise ValueError(f'If method is {method}, please provide the value of air_flow_rate.')
            self.__properties['Maximum_Heating_Air_Flow_Rate'] = air_flow_rate
        elif method == 'LimitCapacity':
            if capacity is None:
                raise ValueError(f'If method is {method}, please provide the value of capacity.')
            self.__properties['Maximum_Sensible_Heating_Capacity'] = capacity
        elif method == 'LimitFlowRateAndCapacity':
            if air_flow_rate is None or capacity is None:
                raise ValueError(f'If method is {method}, please provide the values of air_flow_rate and capacity.')
            self.__properties['Maximum_Heating_Air_Flow_Rate'] = air_flow_rate
            self.__properties['Maximum_Sensible_Heating_Capacity'] = capacity
    
    def set_cooling_limit(self, method, air_flow_rate=None, capacity=None):
        methods = ['NoLimit', 'LimitFlowRate', 'LimitCapacity', 'LimitFlowRateAndCapacity']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Cooling_Limit'] = method

        if method == 'NoLimit':
            pass
        elif method == 'LimitFlowRate':
            if air_flow_rate is None:
                raise ValueError(f'If method is {method}, please provide the value of air_flow_rate.')
            self.__properties['Maximum_Cooling_Air_Flow_Rate'] = air_flow_rate
        elif method == 'LimitCapacity':
            if capacity is None:
                raise ValueError(f'If method is {method}, please provide the value of capacity.')
            self.__properties['Maximum_Total_Cooling_Capacity'] = capacity
        elif method == 'LimitFlowRateAndCapacity':
            if air_flow_rate is None or capacity is None:
                raise ValueError(f'If method is {method}, please provide the values of air_flow_rate and capacity.')
            self.__properties['Maximum_Cooling_Air_Flow_Rate'] = air_flow_rate
            self.__properties['Maximum_Total_Cooling_Capacity'] = capacity
    
    def set_dehumidification_control_type(self, method, SHR=None):
        methods = ['Humidistat', 'None', 'ConstantSupplyHumidityRatio']
        if method not in methods:
            raise ValueError(f'method must be one of the following in {methods}.')
        self.__properties['Dehumidification_Control_Type'] = method

        if method == 'ConstantSupplyHumidityRatio':
            if SHR is None:
                raise ValueError(f'If method is {method}, please provide the value of SHR.')
            self.__properties['Cooling_Sensible_Heat_Ratio'] = SHR
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONEHVAC:IDEALLOADSAIRSYSTEM',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = IdealLoadsAirSystem(self.name(), self.schedules()['Availability_Schedule'], None)
        duplicate_class.update_properties(self.properties())
        for k, v in self.schedules().items():
            if v is not None:
                duplicate_class.set_schedule(k, v.duplicate())
        return duplicate_class


class ZoneControlHumidistat:
    def __init__(self, name, zone_name, humidifying_schedule=None, dehumidifying_schedule=None):
        self.__properties = {
            'Name': name,
            'Zone_Name': zone_name,
            'Humidifying_Relative_Humidity_Setpoint_Schedule_Name': humidifying_schedule.name() if humidifying_schedule is not None else None,
            'Dehumidifying_Relative_Humidity_Setpoint_Schedule_Name': dehumidifying_schedule.name() if dehumidifying_schedule is not None else None,
        }

        self.__schedules = {
            'Humidifying_Relative_Humidity_Setpoint_Schedule': humidifying_schedule if humidifying_schedule is not None else None,
            'Dehumidifying_Relative_Humidity_Setpoint_Schedule': dehumidifying_schedule if dehumidifying_schedule is not None else None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedules(self):
        return self.__schedules
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_schedule(self, key, schedule):
        self.__schedules[key] = schedule
        self.set_properties(f'{key}_Name', schedule.name())
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONECONTROL:HUMIDISTAT',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = ZoneControlHumidistat(self.name(), self.properties()['Zone_Name'])
        duplicate_class.update_properties(self.properties())
        for k, v in self.schedules().items():
            if v is not None:
                duplicate_class.set_schedule(k, v.duplicate())
        return duplicate_class


class ZoneControlThermostat:
    def __init__(self, name, zone_name, control_type_schedule):
        self.__properties = {
            'Name': name,
            'Zone_or_ZoneList_Name': zone_name,
            'Control_Type_Schedule_Name': control_type_schedule.name() if control_type_schedule is not None else None,
            'Control_1_Object_Type': None,
            'Control_1_Name': None,
            'Control_2_Object_Type': None,
            'Control_2_Name': None,
            'Control_3_Object_Type': None,
            'Control_3_Name': None,
            'Control_4_Object_Type': None,
            'Control_4_Name': None,
            'Temperature_Difference_Between_Cutout_And_Setpoint': '0.0',
        }

        self.__schedules = {
            'Control_Type_Schedule': control_type_schedule,
        }

        self.__thermostats = {
            'Control_1_Object': None,
            'Control_2_Object': None,
            'Control_3_Object': None,
            'Control_4_Object': None,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedules(self):
        return self.__schedules
    
    def thermostats(self):
        return self.__thermostats
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_schedule(self, key, schedule):
        self.__schedules[key] = schedule
        self.set_properties(f'{key}_Name', schedule.name())
    
    def set_control(self, thermostat, n):
        self.__thermostats[f'Control_{n}_Object'] = thermostat
        self.__properties[f'Control_{n}_Object_Type'] = thermostat.epclass()
        self.__properties[f'Control_{n}_Name'] = thermostat.name()
        
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'ZONECONTROL:THERMOSTAT',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = ZoneControlThermostat(self.name(), self.properties()['Zone_or_ZoneList_Name'], None)
        duplicate_class.update_properties(self.properties())
        for k, v in self.schedules().items():
            if v is not None:
                duplicate_class.set_schedule(k, v.duplicate())
        for i, (k, v) in enumerate(self.thermostats().items()):
            if v is not None:
                duplicate_class.set_control(v.duplicate(), i+1)
        return duplicate_class


class ThermostatSetpointDual:
    def __init__(self, name, heating_setpoint_temperature_schedule, cooling_setpoint_temperature_schedule):
        self.__properties = {
            'Name': name,
            'Heating_Setpoint_Temperature_Schedule_Name': heating_setpoint_temperature_schedule.name() if heating_setpoint_temperature_schedule is not None else None,
            'Cooling_Setpoint_Temperature_Schedule_Name': cooling_setpoint_temperature_schedule.name() if cooling_setpoint_temperature_schedule is not None else None,
        }

        self.__schedules = {
            'Heating_Setpoint_Temperature_Schedule': heating_setpoint_temperature_schedule,
            'Cooling_Setpoint_Temperature_Schedule': cooling_setpoint_temperature_schedule,
        }

        self.__epclass = 'THERMOSTATSETPOINT:DUALSETPOINT'
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}]')

        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def schedules(self):
        return self.__schedules
    
    def epclass(self):
        return self.__epclass
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_schedule(self, key, schedule):
        self.__schedules[key] = schedule
        self.set_properties(f'{key}_Name', schedule.name())
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'THERMOSTATSETPOINT:DUALSETPOINT',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = ThermostatSetpointDual(self.name(), None, None)
        duplicate_class.update_properties(self.properties())
        for k, v in self.schedules().items():
            if v is not None:
                duplicate_class.set_schedule(k, v.duplicate())
        return duplicate_class


#####################
class VariableRefrigerantFlow:
    def __init__(self):
        self.__properties = {
            'Heat_Pump_Name': None,
            'Availability_Schedule_Name': None,
            'Gross_Rated_Total_Cooling_Capacity': None,
            'Gross_Rated_Cooling_COP': '3.3',
            'Minimum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode': '-6.0',
            'Maximum_Condenser_Inlet_Node_Temperature_in_Cooling_Mode': '43.0',
            'Cooling_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name': None,
            'Cooling_Capacity_Ratio_Boundary_Curve_Name': None,
            'Cooling_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name': None,
            'Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name': None,
            'Cooling_Energy_Input_Ratio_Boundary_Curve_Name': None,
            'Cooling_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name': None,
            'Cooling_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name': None,
            'Cooling_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name': None,
            'Cooling_Combination_Ratio_Correction_Factor_Curve_Name': None,
            'Cooling_PartLoad_Fraction_Correlation_Curve_Name': None,
            'Gross_Rated_Heating_Capacity': None,
            'Rated_Heating_Capacity_Sizing_Ratio': '1.0',
            'Gross_Rated_Heating_COP': '3.4',
            'Minimum_Condenser_Inlet_Node_Temperature_in_Heating_Mode': '-20.0',
            'Maximum_Condenser_Inlet_Node_Temperature_in_Heating_Mode': '16.0',
            'Heating_Capacity_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name': None,
            'Heating_Capacity_Ratio_Boundary_Curve_Name': None,
            'Heating_Capacity_Ratio_Modifier_Function_of_High_Temperature_Curve_Name': None,
            'Heating_Energy_Input_Ratio_Modifier_Function_of_Low_Temperature_Curve_Name': None,
            'Heating_Energy_Input_Ratio_Boundary_Curve_Name': None,
            'Heating_Energy_Input_Ratio_Modifier_Function_of_High_Temperature_Curve_Name': None,
            'Heating_Performance_Curve_Outdoor_Temperature_Type': 'WetBulbTemperature',
            'Heating_Energy_Input_Ratio_Modifier_Function_of_Low_PartLoad_Ratio_Curve_Name': None,
            'Heating_Energy_Input_Ratio_Modifier_Function_of_High_PartLoad_Ratio_Curve_Name': None,
            'Heating_Combination_Ratio_Correction_Factor_Curve_Name': None,
            'Heating_PartLoad_Fraction_Correlation_Curve_Name': None,
            'Minimum_Heat_Pump_PartLoad_Ratio': '0.15',
            'Zone_Name_for_Master_Thermostat_Location': None,
            'Master_Thermostat_Priority_Control_Type': 'MasterThermostatPriority',
            'Thermostat_Priority_Schedule_Name': None,
            'Zone_Terminal_Unit_List_Name': None,
            'Heat_Pump_Waste_Heat_Recovery': 'No',
            'Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Cooling_Mode': None,
            'Vertical_Height_used_for_Piping_Correction_Factor': None,
            'Piping_Correction_Factor_for_Length_in_Cooling_Mode_Curve_Name': None,
            'Piping_Correction_Factor_for_Height_in_Cooling_Mode_Coefficient': '0.0',
            'Equivalent_Piping_Length_used_for_Piping_Correction_Factor_in_Heating_Mode': None,
            'Piping_Correction_Factor_for_Length_in_Heating_Mode_Curve_Name': None,
            'Piping_Correction_Factor_for_Height_in_Heating_Mode_Coefficient': '0.0',
            'Crankcase_Heater_Power_per_Compressor': '33.0',
            'Number_of_Compressors': '2',
            'Ratio_of_Compressor_Size_to_Total_Compressor_Capacity': '0.5',
            'Maximum_Outdoor_DryBulb_Temperature_for_Crankcase_Heater': '5.0',
            'Defrost_Strategy': 'Resistive',
            'Defrost_Control': 'Timed',
            'Defrost_Energy_Input_Ratio_Modifier_Function_of_Temperature_Curve_Name': None,
            'Defrost_Time_Period_Fraction': '0.058333',
            'Resistive_Defrost_Heater_Capacity': '0.0',
            'Maximum_Outdoor_Drybulb_Temperature_for_Defrost_Operation': '5.0',
            'Condenser_Type': 'AirCooled',
            'Condenser_Inlet_Node_Name': None,
            'Condenser_Outlet_Node_Name': None,
            'Water_Condenser_Volume_Flow_Rate': None,
            'Evaporative_Condenser_Effectiveness': '0.9',
            'Evaporative_Condenser_Air_Flow_Rate': None,
            'Evaporative_Condenser_Pump_Rated_Power_Consumption': '0.0',
            'Supply_Water_Storage_Tank_Name': None,
            'Basin_Heater_Capacity': '0.0',
            'Basin_Heater_Setpoint_Temperature': '2.0',
            'Basin_Heater_Operating_Schedule_Name': None,
            'Fuel_Type': 'Electricity',
            'Minimum_Condenser_Inlet_Node_Temperature_in_Heat_Recovery_Mode': None,
            'Maximum_Condenser_Inlet_Node_Temperature_in_Heat_Recovery_Mode': None,
            'Heat_Recovery_Cooling_Capacity_Modifier_Curve_Name': None,
            'Initial_Heat_Recovery_Cooling_Capacity_Fraction': '0.5',
            'Heat_Recovery_Cooling_Capacity_Time_Constant': '0.15',
            'Heat_Recovery_Cooling_Energy_Modifier_Curve_Name': None,
            'Initial_Heat_Recovery_Cooling_Energy_Fraction': '1.0',
            'Heat_Recovery_Cooling_Energy_Time_Constant': '0.0',
            'Heat_Recovery_Heating_Capacity_Modifier_Curve_Name': None,
            'Initial_Heat_Recovery_Heating_Capacity_Fraction': '1.0',
            'Heat_Recovery_Heating_Capacity_Time_Constant': '0.15',
            'Heat_Recovery_Heating_Energy_Modifier_Curve_Name': None,
            'Initial_Heat_Recovery_Heating_Energy_Fraction': '1.0',
            'Heat_Recovery_Heating_Energy_Time_Constant': '0.0',
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
            'class': 'AIRCONDITIONER:VARIABLEREFRIGERANTFLOW',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = VariableRefrigerantFlow()
        duplicate_class.update_properties(self.properties())
        return duplicate_class


#####################
class Fan:
    def __init__(self):
        self.__properties = {
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
            'class': '',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = Fan()
        duplicate_class.update_properties(self.properties())
        return duplicate_class


#####################
class Coil:
    def __init__(self):
        self.__properties = {
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
            'class': '',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_class = Coil()
        duplicate_class.update_properties(self.properties())
        return duplicate_class

if __name__ == '__main__':
    import os
    import json
    epclass_name = 'ZONEINFILTRATION:DESIGNFLOWRATE'
    epobjects_path = os.path.join(os.path.dirname(__file__), 'epobjects.json')
    with open(epobjects_path, mode='r', encoding='utf-8') as f:
        epobjects = json.load(f)
    for k, v in epobjects[epclass_name].items():
        if v == '':
            v = None
            print(f"            '{k}': {v},")
        else:
            print(f"            '{k}': '{v}',")
