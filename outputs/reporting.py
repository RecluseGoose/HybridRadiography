# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 10:08:51 2019

@author: robert.culver
"""

import matplotlib.pyplot as plt
import base64
import numpy as np
from io import BytesIO

if __name__== "__main__":
    fig = plt.figure()
    plt.imshow(np.random.random((300,300)))
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format = 'png')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    html = 'some html head' + '<img src=\'data:image/png;base64,{}\'>'.format(encoded) + 'some more html'
    with open('test.html','w') as f:
        f.write(html)
        
