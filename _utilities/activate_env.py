# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 09:54:35 2019

@author: robert.culver
"""
import os
import sys
import subprocess

ANACONDA3_DIR = "C:\\Anaconda3\\envs\\hy_rad"
PYTHON_EXE_PATH = os.path.abspath(os.path.join(ANACONDA3_DIR,"python.exe"))

def _get_clean_env():
    '''cleans path of altair and program files'''
    new_env = os.environ.copy()
    path = new_env['PATH'].split(";")
    path = [p for p in path if ((len(p)>0) and not ('altair' in p.lower() and 'program files' in p.lower()))]
    new_env['PATH'] = ";".join(path) + ";"
    return new_env

def _checkdir(d):
    assert os.path.isdir(d), 'directory not found: {}'.format(d)

def _append_anaconda3(env):
    new_env = env.copy()
    dirs = new_env['PATH'].split(";")
    for d in ["scripts",
             "library/bin",
             "lib/site-packages/numpy/core/lib"]:
        path = os.path.join(ANACONDA3_DIR,d)
        _checkdir(path)
        dirs.append(path)
    new_env['PATH'] = ";".join(dirs) + ";"
    return new_env
    
def build_env():
    env = _get_clean_env()
    env = _append_anaconda3(env)
    return env

def filecheck(filename):
    assert os.path.exists(filename), "file not found: {}".format(filename)
    
def runcmd(cmd):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    p = subprocess.Popen(cmd, shell = False,startupinfo = startupinfo, env=build_env(), stdout = subprocess.PIPE, universal_newlines = True)
    failed = False
    for stdout_line in iter(p.stdout.readline,""):
        failed = ('== FAILURES ==' in stdout_line) or ('== ERRORS ==' in stdout_line) or failed
        print(stdout_line)
    p.stdout.close()
    assert(not failed)
    

if __name__ == "__main__":
    lastArg = sys.argv[-1]
    if lastArg == 'build':
        scriptpath = sys.argv[-2]
        cmd = '"{0}" "{1}" build'.format(PYTHON_EXE_PATH, scriptpath)
    else:
        scriptpath = lastArg
        cmd = '"{0}" "{1}"'.format(PYTHON_EXE_PATH, scriptpath)
    print("Running comand: {}".format(cmd))
    runcmd(cmd)