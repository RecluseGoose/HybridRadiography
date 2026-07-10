from distutils.core import setup, Extension
import numpy as np
import os
import shutil
from glob import glob

wd = os.getcwd()
if (os.path.split(wd)[-1].lower() != 'engine'):
    wd = os.path.join(wd,"engine")
assert os.path.exists(os.path.join(wd,"src")),"{} doesn't appear to be a valid source directory"
sources = [os.path.join(wd,"src",f) for f in os.listdir(os.path.join(wd,"src")) if (".c" in f.lower())]
incl_dir = os.path.join(wd,"include")

modNames =['rays','material_path', 'material_path2']

modulesToBuild = [Extension(mod, sources = sources,extra_compile_args = [],library_dirs =[]) for mod in modNames]

setup (name = 'PackageName',
       version = '1.0',
       description = 'This is a demo package',
       include_dirs = [np.get_include(), incl_dir],
       ext_modules = modulesToBuild,
       )

for mod in modNames:
    try:
        f = glob(os.path.join(wd,mod+'*.pyd'))
        if len(f) == 1:
            os.remove(f[0])
    except:
        pass

    fd = glob(os.path.join('build','lib*'))[0]
    file2copy = glob(os.path.join(fd,mod+'*.pyd'))[0]
    shutil.copy2(os.path.join(file2copy),os.path.join(wd,mod+'.pyd'))

shutil.rmtree('build')
