# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 12:13:17 2020

@author: robert.culver
"""

from _utilities import img_manip
from simulation import transformations
import numpy as np

try:
    stack[::10]
except:
    stack = np.load("finstack.npy")

#projdir = r"D:/drama/JS_32296-11_16477_FINAL STEEL ARA_NATHAN TURNER"
#stack = img_manip.loadAll(projdir)

input("PAK to play...")
transformations.playStack(stack[::10], rate = 60, loops = 1)