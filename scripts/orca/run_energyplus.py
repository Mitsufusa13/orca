import os
import shutil
import subprocess
import time

class Run:
    def __init__(self, idf_path, epw_path, out_dir, energyplus_dir=None):
        self.__idf_path = idf_path
        self.__epw_path = epw_path
        self.__out_dir = out_dir
        self.set_ep_version('24-2-0')
        self.set_energyplus_dir(energyplus_dir)

        self.__results = {
            'ok': False,
            'elapsed_sec': None,
            'sql_path': None,
            'err_path': None,
            'err_log': None,
        }
    
    @property
    def idf_path(self):
        return self.__idf_path
    
    @property
    def epw_path(self):
        return self.__epw_path
    
    @property
    def out_dir(self):
        return self.__out_dir
    
    @property
    def ep_version(self):
        return self.__ep_version
    
    def set_ep_version(self, ep_version):
        if type(ep_version) != str:
            ep_version = str(ep_version)

        if len(ep_version.split('-')) == 3:
            self.__ep_version = [f'{v}' for v in ep_version.split('-')]
        elif len(ep_version.split('.')) == 3:
            self.__ep_version = [f'{v}' for v in ep_version.split('.')]
        elif len(ep_version.split('-')) == 2:
            self.__ep_version = [f'{v}' for v in ep_version.split('-')] + ['0']
        elif len(ep_version.split('.')) == 2:
            self.__ep_version = [f'{v}' for v in ep_version.split('.')] + ['0']
        elif len(ep_version.split('-')) == 1:
            self.__ep_version = [f'{v}' for v in ep_version.split('-')] + ['0', '0']
        elif len(ep_version.split('.')) == 1:
            self.__ep_version = [f'{v}' for v in ep_version.split('.')] + ['0', '0']
        else:
            raise ValueError('Please submit ep_version in the following format. Example:24-2-0 or 24.2.0')
        
        self.__ep_version = '-'.join(self.__ep_version)
    
    def set_energyplus_dir(self, energyplus_dir=None):
        if energyplus_dir is None:
            energyplus_dir = os.environ.get(
                'ENERGYPLUS_DIR',
                r'C:/EnergyPlusV{}'.format(self.ep_version)
            )
        self.__idd_path = os.path.join(energyplus_dir, 'Energy+.idd')
        self.__energyplus_exe = os.path.join(energyplus_dir, 'energyplus.exe')
    
    @property
    def idd_path(self):
        return self.__idd_path
    
    @property
    def energyplus_exe(self):
        return self.__energyplus_exe
    
    @property
    def results(self):
        return self.__results
    
    def update_results(self, _dict):
        self.__results = {**self.__results, **_dict}
    
    def run(self, overwrite=True, timeout_sec=None, extra_args=None):
        idf_path = self.idf_path
        epw_path = self.epw_path
        energyplus_exe = self.energyplus_exe

        if not idf_path or not os.path.isfile(idf_path):
            raise FileNotFoundError(f'idf_path not found: {idf_path}')
        if not epw_path or not os.path.isfile(epw_path):
            raise FileNotFoundError(f'epw_path not found: {epw_path}')
        if not energyplus_exe or not os.path.isfile(energyplus_exe):
            raise FileNotFoundError(f'energyplus_exe not found: {energyplus_exe}')
        
        out_dir = os.path.abspath(self.out_dir)
        if os.path.exists(out_dir):
            if overwrite:
                shutil.rmtree(out_dir)
            else:
                pass
        os.makedirs(out_dir, exist_ok=True)

        cmd = [energyplus_exe, '-w', epw_path, '-d', out_dir]
        if extra_args:
            cmd.extend(list(extra_args))
        cmd.append(idf_path)

        t0 = time.time()
        p = subprocess.Popen(
            cmd,
            cwd=out_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        exit_code = p.wait()

        dt = time.time() - t0
        ok = (exit_code == 0)
        err_log = self.read_err(os.path.join(self.out_dir, 'eplusout.err'))

        _results = {
            'ok': ok,
            'elapsed_sec': dt,
            'sql_path': os.path.join(out_dir, 'eplusout.sql'),
            'err_path': os.path.join(self.out_dir, 'eplusout.err'),
            'err_log': err_log,
        }
        self.update_results(_results)
    
    def not_run(self, overwrite):
        out_dir = os.path.abspath(self.out_dir)
        if os.path.exists(out_dir):
            if overwrite:
                shutil.rmtree(out_dir)
            else:
                pass
        os.makedirs(out_dir, exist_ok=True)

        if os.path.exists(os.path.join(self.out_dir, 'eplusout.err')):
            err_log = self.read_err(os.path.join(self.out_dir, 'eplusout.err'))
        else:
            err_log = None
        _results = {
            'ok': False,
            'elapsed_sec': None,
            'sql_path': os.path.join(self.out_dir, 'eplusout.sql') if os.path.exists(os.path.join(self.out_dir, 'eplusout.sql')) else None,
            'err_path': os.path.join(self.out_dir, 'eplusout.err') if os.path.exists(os.path.join(self.out_dir, 'eplusout.err')) else None,
            'err_log': err_log,
        }
        self.update_results(_results)
    
    def read_err(self, err_path):
        with open(err_path, mode='r', encoding='utf-8') as f:
            err_log = f.read()
        return err_log


if __name__ == '__main__':
    _run = Run('idf', 'epw', 'output')
    _run.read_err(f'C:\Projects\GHDevelopment\sample\Test2\eplusout.err')
