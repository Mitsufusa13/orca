import os
import csv
import json
import datetime
import math


HEADER_COLUMNS = [
    'LOCATION',
    'DESIGN CONDITIONS',
    'TYPICAL/EXTREME PERIODS',
    'GROUND TEMPERATURES',
    'HOLIDAYS/DAYLIGHT SAVINGS',
    'COMMENTS 1',
    'COMMENTS 2',
    'DATA PERIODS',
]

HEADER_DEFAULT = {
    'LOCATION': {
        'City': '',
        'State Province Region': '',
        'Country': '',
        'Source': '',
        'WMO': 999999,
        'Latitude': 0.0,
        'Longitude': 0.0,
        'TimeZone': 0.0,
        'Elevation': 0.0,
    },
    'DESIGN CONDITIONS': [0],
    'TYPICAL/EXTREME PERIODS': [0],
    'GROUND TEMPERATURES': [0],
    'HOLIDAYS/DAYLIGHT SAVINGS': {
        'Leap Year': 'No',
        'DST Start': 0,
        'DST End': 0,
        'Number of Holidays': 0,
    },
    'COMMENTS 1': '',
    'COMMENTS 2': '',
    'DATA PERIODS': {
        'Number of Periods': 1,
        'Records per Hour': 1,
        'Data Name': 'Data',
        'Start Day of Week': 'Sunday',
        'Start Date': '1/1',
        'End Date': '12/31',
    },
}

WEATHERDATA_COLUMNS = [
    'Year',
    'Month',
    'Day',
    'Hour',
    'Minute',
    'Data Source and Uncertainty Flags',
    'Dry Bulb Temperature {C}',
    'Dew Point Temperature {C}',
    'Relative Humidity {%}',
    'Atmospheric Station Pressure {Pa}',
    'Extraterrestrial Horizontal Radiation {Wh/m2}',
    'Extraterrestrial Direct Normal Radiation {Wh/m2}',
    'Horizontal Infrared Radiation Intensity from Sky {Wh/m2}',
    'Global Horizontal Radiation {Wh/m2}',
    'Direct Normal Radiation {Wh/m2}',
    'Diffuse Horizontal Radiation {Wh/m2}',
    'Global Horizontal Illuminance {lux}',
    'Direct Normal Illuminance {lux}',
    'Diffuse Horizontal Illuminance {lux}',
    'Zenith Luminance {Cd/m2}',
    'Wind Direction {deg}',
    'Wind Speed {m/s}',
    'Total Sky Cover {tenths}',
    'Opaque Sky Cover {tenths}',
    'Visibility {km}',
    'Ceiling Height {m}',
    'Present Weather Observation',
    'Present Weather Codes',
    'Precipitable Water {mm}',
    'Aerosol Optical Depth {thousandths}',
    'Snow Depth {cm}',
    'Days Since Last Snowfall',
    'Albedo',
    'Liquid Precipitation Depth {mm}',
    'Liquid Precipitation Quantity {hr}'
]

MISSING_WEATHERDATA = {
    'Year': 9999,
    'Month': 99,
    'Day': 99,
    'Hour': 99,
    'Minute': 60,
    'Data Source and Uncertainty Flags': '?9?9?9?9E0?9?9?9?9*9*9*9*9',
    'Dry Bulb Temperature {C}': 99.9,
    'Dew Point Temperature {C}': 99.9,
    'Relative Humidity {%}': 999,
    'Atmospheric Station Pressure {Pa}': 999999,
    'Extraterrestrial Horizontal Radiation {Wh/m2}': 9999,
    'Extraterrestrial Direct Normal Radiation {Wh/m2}': 9999,
    'Horizontal Infrared Radiation Intensity from Sky {Wh/m2}': 9999,
    'Global Horizontal Radiation {Wh/m2}': 9999,
    'Direct Normal Radiation {Wh/m2}': 9999,
    'Diffuse Horizontal Radiation {Wh/m2}': 9999,
    'Global Horizontal Illuminance {lux}': 999999,
    'Direct Normal Illuminance {lux}': 999999,
    'Diffuse Horizontal Illuminance {lux}': 999999,
    'Zenith Luminance {Cd/m2}': 9999,
    'Wind Direction {deg}': 999,
    'Wind Speed {m/s}': 999,
    'Total Sky Cover {tenths}': 99,
    'Opaque Sky Cover {tenths}': 99,
    'Visibility {km}': 9999,
    'Ceiling Height {m}': 99999,
    'Present Weather Observation': '9',
    'Present Weather Codes': '999999999',
    'Precipitable Water {mm}': 999,
    'Aerosol Optical Depth {thousandths}': 999,
    'Snow Depth {cm}': 999,
    'Days Since Last Snowfall': 99,
    'Albedo': 999,
    'Liquid Precipitation Depth {mm}': 999,
    'Liquid Precipitation Quantity {hr}': 99
}

MJ_TO_WH = 1000000.0 / 3600.0


def copy_header_default():
    return json.loads(json.dumps(HEADER_DEFAULT))


def ensure_directory(directory):
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)


def saturation_vapor_pressure_pa(t_c):
    return 611.21 * math.exp((18.678 - t_c / 234.5) * (t_c / (257.14 + t_c)))


def vapor_pressure_from_humidity_ratio(w_kg_per_kgda, p_pa):
    return p_pa * w_kg_per_kgda / (0.621945 + w_kg_per_kgda)


def relative_humidity_from_humidity_ratio_gpkg(w_g_per_kgda, dry_bulb_c, pressure_pa):
    w = float(w_g_per_kgda) / 1000.0
    pw = vapor_pressure_from_humidity_ratio(w, pressure_pa)
    pws = saturation_vapor_pressure_pa(dry_bulb_c)
    rh = 100.0 * pw / pws
    rh = max(0.0, min(100.0, rh))
    return round(rh, 1)


def dew_point_from_humidity_ratio_gpkg(w_g_per_kgda, pressure_pa):
    w = float(w_g_per_kgda) / 1000.0
    pw = vapor_pressure_from_humidity_ratio(w, pressure_pa)
    if pw <= 0.0:
        return MISSING_WEATHERDATA['Dew Point Temperature {C}']
    ln_ratio = math.log(pw / 611.2)
    dp = (243.5 * ln_ratio) / (17.67 - ln_ratio)
    return round(dp, 1)


def validate_epw_weather_data(weather_data, weather_data_columns):
    errors = []
    warnings = []

    n = None
    for col in weather_data_columns:
        if col not in weather_data:
            errors.append('Missing column: {0}'.format(col))
            continue
        if n is None:
            n = len(weather_data[col])
        elif len(weather_data[col]) != n:
            errors.append('Column length mismatch: {0} -> {1}, expected {2}'.format(col, len(weather_data[col]), n))

    if n is None:
        errors.append('No weather data found.')
        return errors, warnings

    if n != 8760:
        errors.append('Row count must be 8760 for this converter. got {0}'.format(n))

    for i in range(n):
        month = weather_data['Month'][i]
        day = weather_data['Day'][i]
        hour = weather_data['Hour'][i]
        minute = weather_data['Minute'][i]

        if not (1 <= month <= 12):
            errors.append('Row {0}: Month out of range: {1}'.format(i + 1, month))
        if not (1 <= day <= 31):
            errors.append('Row {0}: Day out of range: {1}'.format(i + 1, day))
        if not (1 <= hour <= 24):
            errors.append('Row {0}: Hour out of range for EPW: {1}'.format(i + 1, hour))
        if minute != 60:
            errors.append('Row {0}: Minute should be 60 for hourly EPW: {1}'.format(i + 1, minute))

        dry_bulb = weather_data['Dry Bulb Temperature {C}'][i]
        dew_point = weather_data['Dew Point Temperature {C}'][i]
        rh = weather_data['Relative Humidity {%}'][i]
        pressure = weather_data['Atmospheric Station Pressure {Pa}'][i]

        hir = weather_data['Horizontal Infrared Radiation Intensity from Sky {Wh/m2}'][i]
        ghi = weather_data['Global Horizontal Radiation {Wh/m2}'][i]
        dni = weather_data['Direct Normal Radiation {Wh/m2}'][i]
        dhi = weather_data['Diffuse Horizontal Radiation {Wh/m2}'][i]

        wind_dir = weather_data['Wind Direction {deg}'][i]
        wind_speed = weather_data['Wind Speed {m/s}'][i]
        rain = weather_data['Liquid Precipitation Depth {mm}'][i]
        rain_hr = weather_data['Liquid Precipitation Quantity {hr}'][i]

        if dry_bulb != MISSING_WEATHERDATA['Dry Bulb Temperature {C}']:
            if dry_bulb < -100.0 or dry_bulb > 100.0:
                warnings.append('Row {0}: Dry bulb looks suspicious: {1}'.format(i + 1, dry_bulb))

        if dew_point != MISSING_WEATHERDATA['Dew Point Temperature {C}']:
            if dew_point < -100.0 or dew_point > 100.0:
                warnings.append('Row {0}: Dew point looks suspicious: {1}'.format(i + 1, dew_point))

        if rh != MISSING_WEATHERDATA['Relative Humidity {%}']:
            if rh < 0.0 or rh > 110.0:
                errors.append('Row {0}: Relative humidity out of range: {1}'.format(i + 1, rh))

        if pressure != MISSING_WEATHERDATA['Atmospheric Station Pressure {Pa}']:
            if pressure < 31000.0 or pressure > 120000.0:
                errors.append('Row {0}: Pressure out of range for EPW: {1}'.format(i + 1, pressure))

        for name, val in [
            ('Horizontal Infrared Radiation Intensity from Sky {Wh/m2}', hir),
            ('Global Horizontal Radiation {Wh/m2}', ghi),
            ('Direct Normal Radiation {Wh/m2}', dni),
            ('Diffuse Horizontal Radiation {Wh/m2}', dhi),
        ]:
            if val != MISSING_WEATHERDATA[name]:
                if val < 0.0:
                    errors.append('Row {0}: Negative radiation not allowed: {1} = {2}'.format(i + 1, name, val))
                elif val > 2000.0:
                    warnings.append('Row {0}: Radiation looks high: {1} = {2}'.format(i + 1, name, val))

        if wind_dir != MISSING_WEATHERDATA['Wind Direction {deg}']:
            if wind_dir < 0.0 or wind_dir > 360.0:
                errors.append('Row {0}: Wind direction out of range: {1}'.format(i + 1, wind_dir))

        if wind_speed != MISSING_WEATHERDATA['Wind Speed {m/s}']:
            if wind_speed < 0.0:
                errors.append('Row {0}: Negative wind speed: {1}'.format(i + 1, wind_speed))
            elif wind_speed > 60.0:
                warnings.append('Row {0}: Wind speed looks high: {1}'.format(i + 1, wind_speed))

        if rain != MISSING_WEATHERDATA['Liquid Precipitation Depth {mm}']:
            if rain < 0.0:
                errors.append('Row {0}: Negative precipitation depth: {1}'.format(i + 1, rain))

        if rain_hr != MISSING_WEATHERDATA['Liquid Precipitation Quantity {hr}']:
            if rain_hr < 0.0:
                errors.append('Row {0}: Negative precipitation quantity: {1}'.format(i + 1, rain_hr))
            elif rain > 0.0 and rain_hr <= 0.0:
                warnings.append('Row {0}: Rain depth > 0 but precipitation quantity <= 0'.format(i + 1))

    return errors, warnings


def validate_epw_timestep_sequence(weather_data):
    errors = []

    if len(weather_data['Year']) != 8760:
        errors.append('Timestep sequence check requires 8760 rows.')
        return errors

    year0 = int(weather_data['Year'][0])
    expected = []
    dt = datetime.datetime(year0, 1, 1, 0, 0)

    while len(expected) < 8760:
        if not (dt.month == 2 and dt.day == 29):
            expected.append((dt.month, dt.day, dt.hour + 1, 60))
        dt += datetime.timedelta(hours=1)

    for i, exp in enumerate(expected):
        got = (
            weather_data['Month'][i],
            weather_data['Day'][i],
            weather_data['Hour'][i],
            weather_data['Minute'][i],
        )
        if got != exp:
            errors.append('Row {0}: DateTime mismatch. got={1}, expected={2}'.format(i + 1, got, exp))

    return errors


class EPW(object):
    def __init__(self, year=2020):
        self.__year = int(year)
        self.__header_columns = HEADER_COLUMNS[:]
        self.__header = copy_header_default()
        self.__weather_data_columns = WEATHERDATA_COLUMNS[:]
        self.__weather_data = {k: [MISSING_WEATHERDATA[k]] * 8760 for k in self.__weather_data_columns}
        self.__datetimes = self.create_datetimes()
        self.__datetime_index = self.create_datetime_index(self.__datetimes)
        self.__fft_result = {
            'Heating': {
                'Datetime': None,
                'Date': None,
                'Temperature_Data': None,
                'Temperature_FT': None,
            },
            'Cooling': {
                'Datetime': None,
                'Date': None,
                'Temperature_Data': None,
                'Temperature_FT': None,
            },
        }
        self.__heating_dict = None
        self.__cooling_dict = None

    @property
    def year(self):
        return self.__year

    @property
    def header_columns(self):
        return self.__header_columns

    @property
    def header(self):
        return self.__header

    @property
    def weather_data_columns(self):
        return self.__weather_data_columns

    @property
    def weather_data(self):
        return self.__weather_data

    @property
    def datetimes(self):
        return self.__datetimes

    @property
    def datetime_index(self):
        return self.__datetime_index
    
    @property
    def fft_result(self):
        return self.__fft_result
    
    @property
    def heating_dict(self):
        return self.__heating_dict
    
    @property
    def cooling_dict(self):
        return self.__cooling_dict
    
    def set_year(self, year):
        self.__year = year

    def create_datetimes(self):
        out = []
        s = datetime.datetime(self.year, 1, 1, 0, 0)
        e = datetime.datetime(self.year + 1, 1, 1, 0, 0)
        dt = s
        while dt < e:
            if not (dt.month == 2 and dt.day == 29):
                out.append(dt)
            dt += datetime.timedelta(hours=1)
        return out

    def create_datetime_index(self, datetimes):
        return {dt.strftime('%Y-%m-%d %H:%M'): i for i, dt in enumerate(datetimes)}

    def set_header_location(self, City, State_Province_Region, Country, Source, WMO=999999, Latitude=0.0, Longitude=0.0, TimeZone=0.0, Elevation=0.0):
        self.__header['LOCATION'] = {
            'City': City,
            'State Province Region': State_Province_Region,
            'Country': Country,
            'Source': Source,
            'WMO': WMO,
            'Latitude': Latitude,
            'Longitude': Longitude,
            'TimeZone': TimeZone,
            'Elevation': Elevation,
        }

    def set_header_comments1(self, text):
        self.__header['COMMENTS 1'] = text

    def set_header_comments2(self, text):
        self.__header['COMMENTS 2'] = text

    def set_header_data_periods(self):
        weekday = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        start_day = weekday[datetime.datetime(self.year, 1, 1).weekday()]
        self.__header['DATA PERIODS'] = {
            'Number of Periods': 1,
            'Records per Hour': 1,
            'Data Name': 'Data',
            'Start Day of Week': start_day,
            'Start Date': '1/1',
            'End Date': '12/31',
        }

    def set_header_ground_temperature(self, temperatures, depth=0.5, conductivity=1.5, density=1600.0, specific_heat=840.0):
        values = self.calculate_ground_temperature(depth, conductivity, density, specific_heat, temperatures)
        self.__header['GROUND TEMPERATURES'] = [1, depth, conductivity, density, specific_heat] + [round(v, 2) for v in values]
        return values

    def calculate_ground_temperature(self, depth, conductivity, density, specific_heat, temperatures):
        t_mean_annual = sum(temperatures) / len(temperatures)
        alpha = conductivity / (density * specific_heat) * 86400.0
        omega = 2.0 * math.pi / 365.0
        delta = math.sqrt(2.0 * alpha / omega)
        beta = depth / delta

        x = [t - t_mean_annual for t in temperatures]
        c = 0.0
        s = 0.0
        t_ref = self.datetimes[0]
        for i, dt in enumerate(self.datetimes):
            tt = (dt - t_ref).days + (dt - t_ref).seconds / 86400.0
            c += x[i] * math.cos(omega * tt)
            s += x[i] * math.sin(omega * tt)
        c *= 2.0 / len(temperatures)
        s *= 2.0 / len(temperatures)

        a_s = math.sqrt(c ** 2 + s ** 2)
        phi = math.atan2(s, c)
        t0 = phi / omega

        out = []
        sdt = datetime.datetime(self.year, 1, 1, 0, 0)
        for month in range(1, 13):
            vals = []
            for dt in self.datetimes:
                if dt.month == month:
                    tt = (dt - sdt).days + (dt - sdt).seconds / 86400.0
                    tg = t_mean_annual + a_s * math.exp(-beta) * math.cos(omega * (tt - t0) - beta)
                    vals.append(tg)
            out.append(sum(vals) / len(vals))
        return out

    def read_design_weather_csv(self, filepath, year=None, encoding='shift-jis'):
        if year is None:
            year = self.year
        year = int(year)

        data = {k: [MISSING_WEATHERDATA[k]] * 8760 for k in self.weather_data_columns}

        with open(filepath, mode='r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames

        if len(rows) != 8760:
            raise ValueError('Expected 8760 hourly rows, but got {0}.'.format(len(rows)))

        required = [
            '月', '日', '時', '気温', '絶対湿度', '推定日射量', '下向き大気放射',
            '気圧', '降水量', '風速', '風向', '法線面直達日射量', '水平面天空日射量'
        ]
        for col in required:
            if col not in fieldnames:
                raise ValueError('Missing required column: {0}'.format(col))

        for i, row in enumerate(rows):
            month = int(row['月'])
            day = int(row['日'])
            hour0 = int(row['時'])

            if hour0 < 0 or hour0 > 23:
                raise ValueError('Hour must be 0-23 in source CSV. got {0} at row {1}'.format(hour0, i + 2))

            dry_bulb = float(row['気温'])
            humidity_ratio_gpkg = float(row['絶対湿度'])
            pressure = float(row['気圧'])

            data['Year'][i] = year
            data['Month'][i] = month
            data['Day'][i] = day
            data['Hour'][i] = hour0 + 1
            data['Minute'][i] = 60
            data['Data Source and Uncertainty Flags'][i] = MISSING_WEATHERDATA['Data Source and Uncertainty Flags']

            data['Dry Bulb Temperature {C}'][i] = dry_bulb
            data['Dew Point Temperature {C}'][i] = dew_point_from_humidity_ratio_gpkg(humidity_ratio_gpkg, pressure)
            data['Relative Humidity {%}'][i] = relative_humidity_from_humidity_ratio_gpkg(humidity_ratio_gpkg, dry_bulb, pressure)
            data['Atmospheric Station Pressure {Pa}'][i] = pressure

            data['Horizontal Infrared Radiation Intensity from Sky {Wh/m2}'][i] = float(row['下向き大気放射']) * MJ_TO_WH
            data['Global Horizontal Radiation {Wh/m2}'][i] = float(row['推定日射量']) * MJ_TO_WH
            data['Direct Normal Radiation {Wh/m2}'][i] = float(row['法線面直達日射量']) * MJ_TO_WH
            data['Diffuse Horizontal Radiation {Wh/m2}'][i] = float(row['水平面天空日射量']) * MJ_TO_WH

            data['Wind Direction {deg}'][i] = float(row['風向'])
            data['Wind Speed {m/s}'][i] = float(row['風速'])

            rain = float(row['降水量'])
            data['Liquid Precipitation Depth {mm}'][i] = rain
            data['Liquid Precipitation Quantity {hr}'][i] = 1.0 if rain > 0.0 else 0.0

        self.__weather_data = data
        return data

    def validate(self):
        errors, warnings = validate_epw_weather_data(self.__weather_data, self.__weather_data_columns)
        seq_errors = validate_epw_timestep_sequence(self.__weather_data)
        errors.extend(seq_errors)
        return errors, warnings

    def header_to_lines(self):
        lines = []

        loc = self.__header['LOCATION']
        lines.append(
            'LOCATION,{City},{State Province Region},{Country},{Source},{WMO},{Latitude},{Longitude},{TimeZone},{Elevation}'.format(**loc)
        )

        for key in ['DESIGN CONDITIONS', 'TYPICAL/EXTREME PERIODS', 'GROUND TEMPERATURES']:
            values = self.__header[key]
            if isinstance(values, list):
                lines.append(key + ',' + ','.join(str(v) for v in values))
            else:
                lines.append(key + ',0')

        h = self.__header['HOLIDAYS/DAYLIGHT SAVINGS']
        lines.append(
            'HOLIDAYS/DAYLIGHT SAVINGS,{Leap Year},{DST Start},{DST End},{Number of Holidays}'.format(**h)
        )

        lines.append('COMMENTS 1,' + str(self.__header['COMMENTS 1']))
        lines.append('COMMENTS 2,' + str(self.__header['COMMENTS 2']))

        d = self.__header['DATA PERIODS']
        lines.append(
            'DATA PERIODS,{Number of Periods},{Records per Hour},{Data Name},{Start Day of Week},{Start Date},{End Date}'.format(**d)
        )

        return lines

    def weather_rows(self):
        n = len(self.__weather_data['Year'])
        for i in range(n):
            yield [self.__weather_data[col][i] for col in self.__weather_data_columns]
    
    # ----- read data
    def read_epw(self, filepath, encoding='utf-8'):
        if not os.path.isfile(filepath):
            raise ValueError('EPW file not found: {0}'.format(filepath))
        if not filepath.lower().endswith('.epw'):
            raise ValueError('Please provide an .epw file: {0}'.format(filepath))

        with open(filepath, mode='r', encoding=encoding, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        if len(rows) < 9:
            raise ValueError('Invalid EPW file. Expected at least 9 lines, got {0}.'.format(len(rows)))

        header_rows = rows[:8]
        data_rows = rows[8:]

        self.__header = copy_header_default()

        for row in header_rows:
            if not row:
                continue

            key = row[0].strip()

            if key == 'LOCATION':
                self.__header['LOCATION'] = {
                    'City': row[1] if len(row) > 1 else '',
                    'State Province Region': row[2] if len(row) > 2 else '',
                    'Country': row[3] if len(row) > 3 else '',
                    'Source': row[4] if len(row) > 4 else '',
                    'WMO': int(float(row[5])) if len(row) > 5 and row[5] != '' else 999999,
                    'Latitude': float(row[6]) if len(row) > 6 and row[6] != '' else 0.0,
                    'Longitude': float(row[7]) if len(row) > 7 and row[7] != '' else 0.0,
                    'TimeZone': float(row[8]) if len(row) > 8 and row[8] != '' else 0.0,
                    'Elevation': float(row[9]) if len(row) > 9 and row[9] != '' else 0.0,
                }

            elif key == 'DESIGN CONDITIONS':
                self.__header['DESIGN CONDITIONS'] = row[1:]

            elif key == 'TYPICAL/EXTREME PERIODS':
                self.__header['TYPICAL/EXTREME PERIODS'] = row[1:]

            elif key == 'GROUND TEMPERATURES':
                self.__header['GROUND TEMPERATURES'] = row[1:]

            elif key == 'HOLIDAYS/DAYLIGHT SAVINGS':
                self.__header['HOLIDAYS/DAYLIGHT SAVINGS'] = {
                    'Leap Year': row[1] if len(row) > 1 else 'No',
                    'DST Start': row[2] if len(row) > 2 else 0,
                    'DST End': row[3] if len(row) > 3 else 0,
                    'Number of Holidays': row[4] if len(row) > 4 else 0,
                }

            elif key == 'COMMENTS 1':
                self.__header['COMMENTS 1'] = ','.join(row[1:]) if len(row) > 1 else ''

            elif key == 'COMMENTS 2':
                self.__header['COMMENTS 2'] = ','.join(row[1:]) if len(row) > 1 else ''

            elif key == 'DATA PERIODS':
                self.__header['DATA PERIODS'] = {
                    'Number of Periods': row[1] if len(row) > 1 else 1,
                    'Records per Hour': row[2] if len(row) > 2 else 1,
                    'Data Name': row[3] if len(row) > 3 else 'Data',
                    'Start Day of Week': row[4] if len(row) > 4 else 'Sunday',
                    'Start Date': row[5] if len(row) > 5 else '1/1',
                    'End Date': row[6] if len(row) > 6 else '12/31',
                }

        data = {k: [] for k in self.__weather_data_columns}

        for r_i, row in enumerate(data_rows):
            if not row:
                continue

            if len(row) < len(self.__weather_data_columns):
                raise ValueError(
                    'Invalid EPW data row at line {0}. Expected at least {1} columns, got {2}.'.format(
                        r_i + 9, len(self.__weather_data_columns), len(row)
                    )
                )

            for i, col in enumerate(self.__weather_data_columns):
                val = row[i]

                if col in ['Data Source and Uncertainty Flags', 'Present Weather Observation', 'Present Weather Codes']:
                    data[col].append(val)
                elif col in ['Year', 'Month', 'Day', 'Hour', 'Minute']:
                    data[col].append(int(float(val)) if val != '' else MISSING_WEATHERDATA[col])
                else:
                    data[col].append(float(val) if val != '' else MISSING_WEATHERDATA[col])

        self.__weather_data = data

        if len(data['Year']) > 0:
            self.__year = int(data['Year'][0])
            self.__datetimes = self.create_datetimes()
            self.__datetime_index = self.create_datetime_index(self.__datetimes)

        return self

    # ----- save data
    def to_epw(self, directory, filename, validate=True):
        if validate:
            errors, warnings = self.validate()
            if errors:
                raise ValueError('EPW validation failed.\n' + '\n'.join(errors[:100]))
        ensure_directory(directory)
        if not filename.lower().endswith('.epw'):
            filename += '.epw'
        filepath = os.path.join(directory, filename)

        with open(filepath, mode='w', encoding='utf-8', newline='') as f:
            for line in self.header_to_lines():
                f.write(line + '\n')
            writer = csv.writer(f, lineterminator='\n')
            for row in self.weather_rows():
                writer.writerow(row)
        return filepath

    def to_json(self, directory, filename):
        ensure_directory(directory)

        header_path = os.path.join(directory, filename + '_header.json')
        data_path = os.path.join(directory, filename + '_weather_data.json')

        with open(header_path, mode='w', encoding='utf-8') as f:
            json.dump(self.header, f, indent=2, ensure_ascii=False)

        with open(data_path, mode='w', encoding='utf-8') as f:
            json.dump(self.weather_data, f, indent=2, ensure_ascii=False)

        return header_path, data_path
    

    # -----calculate air conditioner season
    def month_days(self, month:int):
        year = self.year
        _s = datetime.datetime(year, month, 1, 0 ,0, 0)
        if month != 12:
            _e = datetime.datetime(year, month+1, 1, 0 ,0, 0)
        else:
            _e = datetime.datetime(year+1, 1, 1, 0 ,0, 0)
        _d = _e - _s
        days = _d.days

        if month == 2:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                days -= 1
        
        return days
    
    def calculate_daily_mean(self, _temperature:list):
        list_mean = []

        hour_number = 0
        for month in range(1, 13):
            for _ in range(1, self.month_days(month)+1):
                _temp_day = _temperature[hour_number:hour_number+24]
                _mean = round(sum(_temp_day) / len(_temp_day), 2)
                list_mean.append(_mean)
                hour_number += 24

        return list_mean
    
    def calculate_daily_max(self, _temperature:list):
        list_max = []

        hour_number = 0
        for month in range(1, 13):
            for _ in range(1, self.month_days(month)+1):
                _temp_day = _temperature[hour_number:hour_number+24]
                _max = round(max(_temp_day), 2)
                list_max.append(_max)
                hour_number += 24

        return list_max
    
    def calculate_air_conditioner_season(self, _temperature:list,
                                         set_point:float,
                                         heating_cooling:str='heating'):
        
        array_datetime = self.datetimes
        _date = [d.date() for i,d in enumerate(array_datetime) if i%24==0]
        T = len(_date)
        if heating_cooling == 'heating':
            values = self.calculate_daily_mean(_temperature)
        elif heating_cooling == 'cooling':
            values = self.calculate_daily_max(_temperature)

        _t = [i - int(T / 2) for i in range(T)]
        _theta = [2*math.pi*_t[i]/T for i in range(T)]
        _xcos = [values[i]*math.cos(_theta[i]) for i in range(T)]
        _xsin = [values[i]*math.sin(_theta[i]) for i in range(T)]
        
        a0 = 2 * sum(values) / T
        a1 = 2 * sum(_xcos) / T
        b1 = 2 * sum(_xsin) / T
        
        _x = [0 for _ in range(T)]
        for i in range(T):
            _x[i] = a0 / 2
            _x[i] += a1 * math.cos(_theta[i])
            _x[i] += b1 * math.sin(_theta[i])
        
        self.__fft_result[heating_cooling.capitalize()]['Datetime'] = array_datetime
        self.__fft_result[heating_cooling.capitalize()]['Date'] = _date
        self.__fft_result[heating_cooling.capitalize()]['Temperature_Data'] = _temperature
        self.__fft_result[heating_cooling.capitalize()]['Temperature_FT'] = _x

        ac_schedule = [0 for i in range(T)]
        ac_schedule_hourly = [0 for i in range(T*24)]
        for i in range(T):
            if _x[i] <= set_point and heating_cooling == 'heating':
                ac_schedule[i] = 1
            elif _x[i] >= set_point and heating_cooling == 'cooling':
                ac_schedule[i] = 1
            else:
                ac_schedule[i] = 0
        
        for i in range(T):
            for j in range(24):
                ac_schedule_hourly[i*24+j] = ac_schedule[i]
        
        if sum(ac_schedule) == 0:
            _start_date = None
            _end_date = None
            datetimes = None
        elif sum(ac_schedule) == len(ac_schedule):
            _start_date = _date[0]
            _end_date = _date[-1]
            datetimes = _start_date.strftime('%m/%d') + '-' + _end_date.strftime('%m/%d')
        else:
            if ac_schedule[0] == 1 and ac_schedule[-1] == 0:
                _start_date = _date[0]
            if ac_schedule[0] == 0 and ac_schedule[-1] == 1:
                _end_date = _date[-1]

            for i in range(T-1):
                if ac_schedule[i] < ac_schedule[i+1]:
                    _start_date = _date[i+1]
                elif ac_schedule[i] > ac_schedule[i+1]:
                    _end_date = _date[i]
            
            try:
                datetimes = _start_date.strftime('%m/%d') + '-' + _end_date.strftime('%m/%d')
            except:
                print(ac_schedule)
                raise ValueError('_start_date or/and _end_date has not been defined.')
            
        
        self.__fft_result[heating_cooling.capitalize()]['Schedule'] = ac_schedule
        self.__fft_result[heating_cooling.capitalize()]['Schedule_Hourly'] = ac_schedule_hourly
        
        season_dict = {
            'start_date': _start_date,
            'end_date': _end_date,
            'datetimes': datetimes,
            'days': sum(ac_schedule),
            'start_months': [1],
            'start_days': [1],
            'end_months': [],
            'end_days': [],
        }
        for i in range(T-1):
            if ac_schedule[i] < ac_schedule[i+1]:
                season_dict['end_months'].append(_date[i].month)
                season_dict['end_days'].append(_date[i].day)
                season_dict['start_months'].append(_date[i+1].month)
                season_dict['start_days'].append(_date[i+1].day)
            elif ac_schedule[i] > ac_schedule[i+1]:
                season_dict['end_months'].append(_date[i].month)
                season_dict['end_days'].append(_date[i].day)
                season_dict['start_months'].append(_date[i+1].month)
                season_dict['start_days'].append(_date[i+1].day)
            
        season_dict['end_months'].append(12)
        season_dict['end_days'].append(31)
        
        return season_dict, ac_schedule_hourly
    
    def calculate_air_conditioner_seasons(self):
        _temperatures = self.weather_data['Dry Bulb Temperature {C}']
        self.__heating_dict, _ = self.calculate_air_conditioner_season(_temperatures, 15, heating_cooling='heating')
        self.__cooling_dict, _ = self.calculate_air_conditioner_season(_temperatures, 23, heating_cooling='cooling')


if __name__ == '__main__':
    csv_path = r'C:\Projects\GHDevelopment\sample\weather.csv'
    output_dir = r'C:\Projects\GHDevelopment\sample'
    filename = 'weather_2020'

    epw = EPW(2020)
    epw.read_design_weather_csv(csv_path, year=2020, encoding='shift-jis')

    epw.set_header_location(
        City='TOKYO',
        State_Province_Region='TOKYO',
        Country='JPN',
        Source='BuildingDesignWeatherData',
        Latitude=35.70776307199293,
        Longitude=139.75245337976943,
        TimeZone=9.0,
        Elevation=20.0
    )

    epw.set_header_data_periods()

    temps = epw.weather_data['Dry Bulb Temperature {C}']
    valid_temps = [t for t in temps if t != MISSING_WEATHERDATA['Dry Bulb Temperature {C}']]
    if len(valid_temps) == 8760:
        epw.set_header_ground_temperature(valid_temps)

    epw.set_header_comments1('Converted from downloaded building design weather CSV')
    epw.set_header_comments2('Radiation converted from MJ/m2 to Wh/m2; humidity ratio converted from g/kgDA')

    errors, warnings = epw.validate()
    print('errors:', len(errors))
    print('warnings:', len(warnings))
    if errors:
        for e in errors[:20]:
            print(e)
        raise ValueError('Validation failed.')

    epw_path = epw.to_epw(output_dir, filename, validate=False)
    header_json_path, data_json_path = epw.to_json(output_dir, filename)

    print(epw_path)
    print(header_json_path)
    print(data_json_path)