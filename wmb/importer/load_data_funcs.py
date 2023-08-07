import os
import json
import bpy
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64, read_int16, read_int32, read_string
from ...wta_wtp.importer.wta import *

class int16(object):
    """
    int16 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_int16(wmb_fp)

class uint16(object):
    """
    uint16 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint16(wmb_fp)

class uint8(object):
    """
    uint8 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint8(wmb_fp)

class uint32(object):
    """
    uint32 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint32(wmb_fp)

class filestring(object):
    """
    filestring class for reading data and
    returning to original location via load_data
    """
    type = "string"
    def __init__(self):
        self.val = ""
    def read(self, wmb_fp):
        self.val = read_string(wmb_fp)


def load_data(wmb_fp, pointer, chunkClass, other=None):
    pos = wmb_fp.tell()
    final = None
    if pointer > 0:
        wmb_fp.seek(pointer)
        #print("Seeking to %sPointer: %s" % (chunkClass.__name__, hex(pointer)))
        final = chunkClass()
        if other is not None:
            final.read(wmb_fp, other)
        else:
            final.read(wmb_fp)
        wmb_fp.seek(pos)
        if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
            return final.val
    return final

def load_data_array(wmb_fp, pointer, count, chunkClass, other=None, useIndex=False):
    array = []
    pos = wmb_fp.tell()
    if pointer > 0:
        wmb_fp.seek(pointer)
        #print("Seeking to %sPointer: %s" % (chunkClass.__name__, hex(pointer)))
        
        # putting the for in the if is, uh, maybe optimized idk
        if other is not None:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp, other)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        elif useIndex:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp, itemIndex)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        else:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        wmb_fp.seek(pos)
        #print("Seeking to return position: %s" % hex(pos))
    return array
