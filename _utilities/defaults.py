# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 03:44:21 2019

@author: robert.culver
"""
import os

USER_DOCS = os.path.join(os.environ['USERPROFILE'],'documents')
if "system32" in USER_DOCS:
    USER_DOCS = "C:/testdocs"
TEMP_STACK_DIR = os.path.join(USER_DOCS,'temp/volumes')
TEST_DATA_DIR = os.path.join(USER_DOCS,'testdata')