import datetime

class TypeLimits:
    def __init__(self, name):
        self.__properties = {
            'Name': name,
            'Lower_Limit_Value': None,
            'Upper_Limit_Value': None,
            'Numeric_Type': None,
            'Unit_Type': 'Dimensionless'
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Lower_Limit_Value':
            if type(value) not in [int, float]:
                raise TypeError(f'Lower_Limit_Value type must be numeric.({type(value)})')
        elif key == 'Upper_Limit_Value':
            if type(value) not in [int, float]:
                raise TypeError(f'Upper_Limit_Value type must be numeric.({type(value)})')
        elif key == 'Numeric_Type':
            numeric_type = ['Continuous', 'Discrete']
            if value not in numeric_type:
                raise ValueError(f'Numeric_Type must be one of the following in {numeric_type}.')
        elif key == 'Unit_Type':
            unit_type = [
                'Dimensionless', 'Temperature', 'DeltaTemperature',
                'PrecipitationRate', 'Angle', 'ConvectionCoefficient',
                'ActivityLevel', 'Velocity', 'Capacity',
                'Power', 'Availability', 'Percent',
                'Control', 'Mode',
            ]
            if value not in unit_type:
                raise ValueError(f'Unit_Type must be one of the following in {unit_type}.')
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'SCHEDULETYPELIMITS',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_schedule = TypeLimits(self.name())
        duplicate_schedule.update_properties(self.properties())
        return duplicate_schedule

class Day_Interval:
    def __init__(self, name, type_limits):
        self.__properties = {
            'Name': name,
            'Schedule_Type_Limits_Name': type_limits.name(),
            'Interpolate_to_Timestep': 'No',
        }
        self.__type_limits = type_limits
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        
        if key == 'Schedule_Type_Limits_Name':
            if type(value) not in [str]:
                raise TypeError(f'Schedule_Type_Limits_Name type must be string.')
        elif key == 'Interpolate_to_Timestep':
            interpolate_to_timestep = ['No', 'Average', 'Linear']
            if value not in interpolate_to_timestep:
                raise ValueError(f'Interpolate_to_Timestep must be one of the following in {interpolate_to_timestep}.')
        
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def type_limits(self):
        return self.__type_limits
    
    def set_schedules(self, minutes_time_delta, Value_Until_Time_list):
        if minutes_time_delta < 10:
            raise ValueError(f'minutes_time_delta({minutes_time_delta}) must be greater than 10.')
        Time_list = []
        _datetime = datetime.datetime.combine(datetime.datetime.today(), datetime.time(0, 0, 0))
        while True:
            _datetime += datetime.timedelta(minutes=minutes_time_delta)
            val = f'{str(_datetime.hour)}:{str(_datetime.minute).zfill(2)}'
            if val == '0:00':
                val = '24:00'
                Time_list.append(val)
                break
            Time_list.append(val)
        
        if len(Time_list) != len(Value_Until_Time_list):
            raise ValueError(f'Time_list({len(Time_list)}) and Value_Until_Time_list({len(Value_Until_Time_list)}) must be same length.')
        
        for i, (t, v) in enumerate(zip(Time_list, Value_Until_Time_list)):
            self.__properties[f'Time_{i+1}'] = t
            self.__properties[f'Value_Until_Time_{i+1}'] = v
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'SCHEDULE:DAY:INTERVAL',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_schedule = Day_Interval(self.name(), self.type_limits())
        duplicate_schedule.update_properties(self.properties())
        return duplicate_schedule

class Week_Daily:
    def __init__(self, name, weekday_day_schedule, weekend_day_schedule):
        self.__day_schedules = []
        weekday_day_schedule_name = weekday_day_schedule.name()
        self.__day_schedules.append(weekday_day_schedule)
        weekend_day_schedule_name = weekend_day_schedule.name()
        self.__day_schedules.append(weekend_day_schedule)
         
        self.__properties = {
            'Name': name,
            'Sunday_ScheduleDay_Name': weekend_day_schedule_name,
            'Monday_ScheduleDay_Name': weekday_day_schedule_name,
            'Tuesday_ScheduleDay_Name': weekday_day_schedule_name,
            'Wednesday_ScheduleDay_Name': weekday_day_schedule_name,
            'Thursday_ScheduleDay_Name': weekday_day_schedule_name,
            'Friday_ScheduleDay_Name': weekday_day_schedule_name,
            'Saturday_ScheduleDay_Name': weekend_day_schedule_name,
            'Holiday_ScheduleDay_Name': weekend_day_schedule_name,
            'SummerDesignDay_ScheduleDay_Name': weekend_day_schedule_name,
            'WinterDesignDay_ScheduleDay_Name': weekend_day_schedule_name,
            'CustomDay1_ScheduleDay_Name': weekend_day_schedule_name,
            'CustomDay2_ScheduleDay_Name': weekday_day_schedule_name,
        }
        self.__day_schedules = {
            'Sunday_ScheduleDay': weekend_day_schedule,
            'Monday_ScheduleDay': weekday_day_schedule,
            'Tuesday_ScheduleDay': weekday_day_schedule,
            'Wednesday_ScheduleDay': weekday_day_schedule,
            'Thursday_ScheduleDay': weekday_day_schedule,
            'Friday_ScheduleDay': weekday_day_schedule,
            'Saturday_ScheduleDay': weekend_day_schedule,
            'Holiday_ScheduleDay': weekend_day_schedule,
            'SummerDesignDay_ScheduleDay': weekend_day_schedule,
            'WinterDesignDay_ScheduleDay': weekend_day_schedule,
            'CustomDay1_ScheduleDay': weekend_day_schedule,
            'CustomDay2_ScheduleDay': weekday_day_schedule,
        }
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        self.__properties[key] = value
    
    def set_day_schedule(self, key, value):
        if key not in self.__day_schedules.keys():
            raise KeyError(f'key must be in [{self.__day_schedules.keys()}].')
        self.__day_schedules[key] = value
        self.set_properties(f'{key}_Name', value.name())
    
    def name(self):
        return self.__properties['Name']
    
    def day_schedules(self):
        return self.__day_schedules
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_weekdays(self, day_schedule):
        for k in ['Monday_ScheduleDay', 'Tuesday_ScheduleDay', 'Wednesday_ScheduleDay', 'Thursday_ScheduleDay', 'Friday_ScheduleDay']:
            self.set_day_schedule(k, day_schedule)
    
    def set_weekends(self, day_schedule):
        for k in ['Sunday_ScheduleDay', 'Saturday_ScheduleDay']:
            self.set_day_schedule(k, day_schedule)
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def update_day_schedules(self, day_schedules):
        self.__day_schedules = {**self.day_schedules(), **day_schedules}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'SCHEDULE:WEEK:DAILY',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_schedule = Week_Daily(self.name(),
                                        self.day_schedules()['Monday_ScheduleDay'],
                                        self.day_schedules()['Sunday_ScheduleDay'])
        duplicate_schedule.update_properties(self.properties())
        duplicate_schedule.update_day_schedules(self.day_schedules())
        return duplicate_schedule

class Year:
    def __init__(self, name, type_limits_name):
        self.__properties = {
            'Name': name,
            'Schedule_Type_Limits_Name': type_limits_name,
        }
        self.__week_schedules = {}
    
    def properties(self):
        return self.__properties
    
    def set_properties(self, key, value):
        if key not in self.__properties.keys():
            raise KeyError(f'key must be in [{self.__properties.keys()}].')
        self.__properties[key] = value
    
    def name(self):
        return self.__properties['Name']
    
    def week_schedules(self):
        return self.__week_schedules
    
    def set_name(self, name):
        self.__properties['Name'] = name
    
    def set_one_period_schedule(self, week_schedule, start_month, start_day, end_month, end_day):
        n = (len(self.properties()) - 2) // 5 + 1
        self.__week_schedules[f'ScheduleWeek_{n}'] = week_schedule
        self.__properties[f'ScheduleWeek_Name_{n}'] = week_schedule.name()
        self.__properties[f'Start_Month_{n}'] = start_month
        self.__properties[f'Start_Day_{n}'] = start_day
        self.__properties[f'End_Month_{n}'] = end_month
        self.__properties[f'End_Day_{n}'] = end_day
    
    def set_periods_schedule(self, week_schedule_names, start_months, start_days, end_months, end_days):
        for wsn, sm, sd, em, ed in zip(week_schedule_names, start_months, start_days, end_months, end_days):
            self.set_one_period_schedule(wsn, sm, sd, em, ed)
    
    def set_week_schedule(self, key, value):
        self.__week_schedules[key] = value
    
    def update_properties(self, properties):
        self.__properties = {**self.properties(), **properties}
    
    def to_idfobject(self):
        idfobject = {
            'class': 'SCHEDULE:YEAR',
            'fields': self.properties(),
        }
        return idfobject
    
    def duplicate(self):
        duplicate_schedule = Year(self.name(), self.properties()['Schedule_Type_Limits_Name'])
        duplicate_schedule.update_properties(self.properties())
        for k, v in self.week_schedules().items():
            duplicate_schedule.set_week_schedule(k, v)
        return duplicate_schedule


"""

for k, v in year.properties().items():
        print(f'{k}:{v}')
    
    for k, v in year.week_schedules().items():
        print(f'    {k}:{v}')
        for _k, _v in v.day_schedules().items():
            print(f'        {_k}:{_v}')
            print(f'            typelimits:{_v.type_limits()}')

"""