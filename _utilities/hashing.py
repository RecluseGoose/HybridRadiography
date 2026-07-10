# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 12:43:30 2019

@author: robert.culver
"""
import hashlib

def getHashString(*args, outputLength = 10):
    string = '_'.join([str(a) for a in args])
    # get integeter representation
    hashed = str(int(hashlib.sha256(string.encode()).hexdigest(),16) % (10**(outputLength*2)))
    hashed += (len(hashed)%2)*'0'
    # for shorter strings, convert from numbers
    chars = [chr(i) for i in list(range(48,58)) + list(range(65,91))]
    lenchars = len(chars)
    output = ''.join([chars[int((hashed[i*2:i*2+2]))%lenchars] for i in range(int(len(hashed)/2))])
    return output