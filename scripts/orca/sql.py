import os
import json
import sqlite3
import datetime

try:
    import Rhino.Geometry as rg
except ImportError:
    raise ImportError('Rhino.Geometry could not import.')

try:
    import scriptcontext as sc
except ImportError:
    raise ImportError('scriptcontext could not import.')

Tol = 1e-6

from orca import zone
from orca import window
from orca import shading
from orca.idf import IDF

class SQL:
    def __init__(self, idf:IDF, sql_path):
        self.__idf = idf
        self.__output_variables = [ov['Variable_Name'] for ov in idf.idfobjects['OUTPUT:VARIABLE']]
        self.__output_variables_zone = [ov['Variable_Name'] for ov in idf.idfobjects['OUTPUT:VARIABLE'] if 'Zone' in ov['Variable_Name']]
        self.__output_variables_surface = [ov['Variable_Name'] for ov in idf.idfobjects['OUTPUT:VARIABLE'] if ('Surface' in ov['Variable_Name']) and ('Window' not in ov['Variable_Name'])]
        self.__output_variables_window = [ov['Variable_Name'] for ov in idf.idfobjects['OUTPUT:VARIABLE'] if 'Window' in ov['Variable_Name']]
        self.__result_dict = self.read_eplus_sql_dict(sql_path, self.output_variables)
        self.datetime_index()
    
    @property
    def idf(self):
        return self.__idf
    
    @property
    def output_variables(self):
        return self.__output_variables
    
    @property
    def output_variables_zone(self):
        return self.__output_variables_zone
    
    @property
    def output_variables_surface(self):
        return self.__output_variables_surface
    
    @property
    def output_variables_window(self):
        return self.__output_variables_window
    
    @property
    def result_all(self):
        return self.__result_dict
    
    @property
    def datetime_index_dict(self):
        return self.__datetime_index_dict
    
    def datetime_index(self):
        _datetime = self.result_all['Datetime']
        datetime_index_dict = {}
        for i, _d in enumerate(_datetime):
            datetime_index_dict[_d.strftime('%m-%d %H:00')] = i
        self.__datetime_index_dict = datetime_index_dict

    def make_column_name(self, name, keyvalue, unit):
        kv = keyvalue
        u = unit
        if kv and str(kv).strip() != "":
            if u and str(u).strip() != "":
                return "{} [{}] ({})".format(name, kv, u)
            return "{} [{}]".format(name, kv)
        else:
            if u and str(u).strip() != "":
                return "{} ({})".format(name, u)
            return "{}".format(name)

    def read_eplus_sql_dict(
        self,
        sql_path,
        variables,
        frequency="Hourly",
        key_filters=None,
        fill_value=None,
        datetime_key="Datetime",
        year_if_zero=2025,
    ):
        variables_set = set(variables)
        key_filters_u = [kf.upper() for kf in key_filters] if key_filters else None

        with sqlite3.connect(sql_path) as con:
            cur = con.cursor()

            cur.execute("SELECT TimeIndex, Year, Month, Day, Hour, Minute FROM Time ORDER BY TimeIndex")
            time_rows = cur.fetchall()
            if not time_rows:
                raise ValueError("Time テーブルが空です。")

            n_time = time_rows[-1][0]
            dt_list = [None] * n_time

            for time_index, y, m, d, h, minute in time_rows:
                y = int(y) if y is not None else year_if_zero
                if y == 0:
                    y = year_if_zero
                m = int(m)
                d = int(d)
                h = int(h) if h is not None else 0
                minute = int(minute) if minute is not None else 0
                h = h - 1
                if h < 0:
                    h = 0
                if h > 23:
                    h = 23
                if minute < 0:
                    minute = 0
                if minute > 59:
                    minute = 59
                dt_list[time_index - 1] = datetime.datetime(y, m, d, h, minute)

            cur.execute(
                """
                SELECT ReportDataDictionaryIndex, Name, KeyValue, Units
                FROM ReportDataDictionary
                WHERE ReportingFrequency = ?
                """,
                (frequency,),
            )
            dict_rows_all = cur.fetchall()

            dict_rows = []
            for idx, name, kv, unit in dict_rows_all:
                if name not in variables_set:
                    continue
                if key_filters_u:
                    kv_u = (kv or "").upper()
                    if not any(kf in kv_u for kf in key_filters_u):
                        continue
                dict_rows.append((idx, name, kv, unit))

            if not dict_rows:
                raise ValueError("指定条件に一致する ReportDataDictionary が見つかりません。")

            id_to_col = {}
            meta = []
            for idx, name, kv, unit in dict_rows:
                col = self.make_column_name(name, kv, unit)
                id_to_col[idx] = col
                meta.append((name, kv, col))

            ids = tuple(id_to_col.keys())
            if not ids:
                raise ValueError("対象の ReportDataDictionaryIndex が空です。")

            data = {col: [fill_value] * n_time for col in id_to_col.values()}

            placeholders = ",".join("?" * len(ids))
            cur.execute(
                f"""
                SELECT TimeIndex, ReportDataDictionaryIndex, Value
                FROM ReportData
                WHERE ReportDataDictionaryIndex IN ({placeholders})
                ORDER BY TimeIndex
                """,
                ids,
            )
            for time_index, var_id, value in cur:
                data[id_to_col[var_id]][time_index - 1] = value

            ordered = []
            if key_filters_u:
                for var in variables:
                    for kf in key_filters_u:
                        for name, kv, col in meta:
                            if name == var and kf in (str(kv or "").upper()):
                                ordered.append(col)
            else:
                for var in variables:
                    for name, kv, col in meta:
                        if name == var:
                            ordered.append(col)

            seen = set()
            ordered_cols = [c for c in ordered if not (c in seen or seen.add(c))]

            out = {datetime_key: dt_list}
            for c in ordered_cols:
                if c in data:
                    out[c] = data[c]
            return out
