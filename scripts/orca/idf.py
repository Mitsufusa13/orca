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

class IDF:
    def __init__(self, idf_path, encoding='utf-8-sig'):
        self.__idfobjects = {}
        self.__epobjects = self.read_epobjects()
        self.read_idf(idf_path, encoding)
        
    @property
    def idfobjects(self):
        return self.__idfobjects
    
    def read_idfobjects(self, empty_skip=True):
        for epclass in self.idfobjects:
            if empty_skip and len(self.idfobjects[epclass]) == 0:
                continue
            t = ''
            t += f'{epclass}\n'
            for i, obj in enumerate(self.idfobjects[epclass]):
                t += f'{" "*4}object {i+1}\n'
                for f, v in obj.items():
                    t += f'{" "*8}{f}:{v}\n'
            print(t)
    
    @property
    def epobjects(self):
        return self.__epobjects
    
    def append_idfobjects(self, key, values):
        self.__idfobjects[key].append(values)
    
    def delete_leading_whitespace(self, text:str):
        if text != '':
            while text[0] == ' ':
                text = text[1:]
                if text== '':
                    break
        return text
    
    def delete_trailing_whitespace(self, text:str):
        if text != '':
            while text[-1] == ' ':
                text = text[:-1]
                if text== '':
                    break
        return text
    
    def read_idf(self, idf_path, encoding):
        with open(idf_path, 'r', encoding=encoding, errors='replace') as f:
            file_texts = f.read()

        file_texts = file_texts.split('\n\n')[1:]
        for k in self.epobjects.keys():
            self.idfobjects[k] = []

        for file_text in file_texts:
            try:
                _obj = {}
                file_text = file_text.split('\n')
                epclass = file_text[0].replace(',', '').upper()
                fields = self.epobjects[epclass]
                if file_text[-1] == '':
                    file_text = file_text[:-1]
                for i, _file_text in enumerate(file_text[1:]):
                    field = [k for k in fields.keys()][i]
                    default_value = fields[field]               
                    if '!-' in _file_text:
                        _file_text = _file_text.split('!- ')
                        value = _file_text[0].replace(',', '').replace(';', '')
                        value = self.delete_leading_whitespace(value)
                        value = self.delete_trailing_whitespace(value)
                    else:
                        value = _file_text
                    
                    if value == '':
                        value = default_value
                    _obj[field] = value
                self.idfobjects[epclass.upper()].append(_obj)
            except Exception:
                pass
        return
    
    def read_epobjects(self):
        cur_dir = os.path.dirname(__file__)
        epobjects_name = 'epobjects.json'
        epobjects_path = os.path.join(cur_dir, epobjects_name)

        with open(epobjects_path, mode='r') as f:
            epobjects = json.load(f)
        
        return epobjects