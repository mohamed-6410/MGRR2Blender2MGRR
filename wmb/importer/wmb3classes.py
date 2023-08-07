import os
import json
import bpy
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64, read_int16, read_int32, read_string
from ...wta_wtp.importer.wta import *


class wmb3_bone(object):
    """docstring for wmb3_bone"""
    def __init__(self, wmb_fp,index):
        super(wmb3_bone, self).__init__()
        self.boneIndex = index
        self.boneNumber = read_uint16(wmb_fp)                
        self.parentIndex = read_uint16(wmb_fp)

        local_positionX = read_float(wmb_fp)         
        local_positionY = read_float(wmb_fp)        
        local_positionZ = read_float(wmb_fp)    
        
        local_rotationX = read_float(wmb_fp)         
        local_rotationY = read_float(wmb_fp)         
        local_rotationZ = read_float(wmb_fp)        

        self.local_scaleX = read_float(wmb_fp)
        self.local_scaleY = read_float(wmb_fp)
        self.local_scaleZ = read_float(wmb_fp)

        world_positionX = read_float(wmb_fp)
        world_positionY = read_float(wmb_fp)
        world_positionZ = read_float(wmb_fp)
        
        world_rotationX = read_float(wmb_fp)
        world_rotationY = read_float(wmb_fp)
        world_rotationZ = read_float(wmb_fp)

        world_scaleX = read_float(wmb_fp)
        world_scaleY = read_float(wmb_fp)
        world_scaleZ = read_float(wmb_fp)

        world_position_tposeX = read_float(wmb_fp)
        world_position_tposeY = read_float(wmb_fp)
        world_position_tposeZ = read_float(wmb_fp)

        self.local_position = (local_positionX, local_positionY, local_positionZ)
        self.local_rotation = (local_rotationX, local_rotationY, local_rotationZ)

        self.world_position = (world_positionX, world_positionY, world_positionZ)
        self.world_rotation = (world_rotationX, world_rotationY, world_rotationZ)
        self.world_scale = (world_scaleX, world_scaleY, world_scaleZ)

        self.world_position_tpose = (world_position_tposeX, world_position_tposeY, world_position_tposeZ)

class wmb3_boneMap(object):
    """docstring for wmb3_boneMap"""
    def __init__(self, wmb_fp):
        super(wmb3_boneMap, self).__init__()
        self.boneMapPointer = read_uint32(wmb_fp)                    
        self.boneMapCount = read_uint32(wmb_fp)    

class wmb3_boneSet(object):
    """docstring for wmb3_boneSet"""
    def __init__(self, wmb_fp, boneSetCount):
        super(wmb3_boneSet, self).__init__()
        self.boneSetArray = []
        self.boneSetCount = boneSetCount
        boneSetInfoArray = []
        #print("Iterating over boneSetCount, length %d" % boneSetCount)
        for index in range(boneSetCount):
            offset = read_uint32(wmb_fp)
            count = read_uint32(wmb_fp)
            boneSetInfoArray.append([offset, count])
        #print("Iterating, really, not using range(), over boneSetInfoArray, length " + str(len(boneSetInfoArray)))
        for boneSetInfo in boneSetInfoArray:
            wmb_fp.seek(boneSetInfo[0])
            #print("Seeking to boneSetInfo[0]: %s" % hex(boneSetInfo[0]))
            boneSet = []
            #print("Iterating over boneSetInfo[1], length %d" % boneSetInfo[1])
            for index in range(boneSetInfo[1]):
                boneSet.append(read_uint16(wmb_fp))
            self.boneSetArray.append(boneSet)

class wmb3_colTreeNode(object):
    """docstring for colTreeNode"""
    def __init__(self, wmb_fp):
        p1_x = read_float(wmb_fp)
        p1_y = read_float(wmb_fp)
        p1_z = read_float(wmb_fp)
        self.p1 = (p1_x, p1_y, p1_z)

        p2_x = read_float(wmb_fp)
        p2_y = read_float(wmb_fp)
        p2_z = read_float(wmb_fp)
        self.p2 = (p2_x, p2_y, p2_z)

        self.left = read_uint32(wmb_fp)
        if self.left == 4294967295:
            self.left = -1

        self.right = read_uint32(wmb_fp)
        if self.right == 4294967295:
            self.right = -1

class wmb3_material(object):
    """docstring for wmb3_material"""
    def __init__(self, wmb_fp):
        super(wmb3_material, self).__init__()
        read_uint16(wmb_fp)
        read_uint16(wmb_fp)
        read_uint16(wmb_fp)
        read_uint16(wmb_fp)
        materialNameOffset = read_uint32(wmb_fp)
        effectNameOffset = read_uint32(wmb_fp)
        techniqueNameOffset = read_uint32(wmb_fp)
        read_uint32(wmb_fp)
        textureOffset = read_uint32(wmb_fp)
        textureNum = read_uint32(wmb_fp)
        paramterGroupsOffset = read_uint32(wmb_fp)
        numParameterGroups = read_uint32(wmb_fp)
        varOffset = read_uint32(wmb_fp)
        varNum = read_uint32(wmb_fp)
        wmb_fp.seek(materialNameOffset)
        #print("Seeking to materialNameOffset: %s" % hex(materialNameOffset))
        self.materialName = to_string(wmb_fp.read(0x100))
        wmb_fp.seek(effectNameOffset)
        #print("Seeking to effectNameOffset: %s" % hex(effectNameOffset))
        self.effectName = to_string(wmb_fp.read(0x100))
        wmb_fp.seek(techniqueNameOffset)
        #print("Seeking to techniqueNameOffset: %s" % hex(techniqueNameOffset))
        self.techniqueName = to_string(wmb_fp.read(0x100))
        self.textureArray = {}

        path_split = wmb_fp.name.split(os.sep)
        mat_list_filepath = os.sep.join(path_split[:-3])
        mat_list_file = open(os.path.join(mat_list_filepath, 'materials.json'), 'a+')
        mat_list_file.seek(0)
        file_dict = {}
        # Try to load json from pre-existing file
        try:
            file_dict = json.load(mat_list_file)
        except Exception as ex:
            print("Could not load json: " , ex)
            pass
        
        # Clear file contents
        mat_list_file.truncate(0)
        file_dict[self.materialName] = {}
        # Append textures to materials in the dictionary
        #print("Iterating over textureNum, length %d" % textureNum)
        for i in range(textureNum):
            wmb_fp.seek(textureOffset + i * 8)
            #print("Seeking to textureOffset + i * 8: %s" % hex(textureOffset + i * 8))
            offset = read_uint32(wmb_fp)
            identifier = "%08x"%read_uint32(wmb_fp)
            wmb_fp.seek(offset)
            #print("Seeking to offset: %s" % hex(offset))
            textureTypeName = to_string(wmb_fp.read(256))
            self.textureArray[textureTypeName] = identifier
            # Add new texture to nested material dictionary

        file_dict[self.materialName]["Textures"] = self.textureArray

        file_dict[self.materialName]["Shader_Name"] = self.effectName
        file_dict[self.materialName]["Technique_Name"] = self.techniqueName
        wmb_fp.seek(paramterGroupsOffset)
        #print("Seeking to paramterGroupsOffset: %s" % hex(paramterGroupsOffset))
        self.parameterGroups = []
        #print("Iterating over numParameterGroups, length %d" % numParameterGroups)
        for i in range(numParameterGroups):
            wmb_fp.seek(paramterGroupsOffset + i * 12)
            #print("Seeking to paramterGroupsOffset + i * 12: %s" % hex(paramterGroupsOffset + i * 12))
            parameters = []
            index = read_uint32(wmb_fp)
            offset = read_uint32(wmb_fp)
            num = read_uint32(wmb_fp)
            wmb_fp.seek(offset)
            #print("Seeking to offset: %s" % hex(offset))
            #print("Iterating over num, length %d" % num)
            for k in range(num):
                param = read_float(wmb_fp)
                parameters.append(param)
            self.parameterGroups.append(parameters)

        wmb_fp.seek(varOffset)
        #print("Seeking to varOffset: %s" % hex(varOffset))
        self.uniformArray = {}
        #print("Iterating over varNum, length %d" % varNum)
        for i in range(varNum):
            wmb_fp.seek(varOffset + i * 8)
            #print("Seeking to varOffset + i * 8: %s" % hex(varOffset + i * 8))
            offset = read_uint32(wmb_fp)
            value = read_float(wmb_fp)
            wmb_fp.seek(offset)
            #print("Seeking to offset: %s" % hex(offset))
            name = to_string(wmb_fp.read(0x100))
            self.uniformArray[name] = value

        file_dict[self.materialName]["ParameterGroups"] = self.parameterGroups
        file_dict[self.materialName]["Variables"] = self.uniformArray

        # Write the current material to materials.json
        json.dump(file_dict, mat_list_file, indent= 4)
        mat_list_file.close()

class wmb3_mesh(object):
    """docstring for wmb3_mesh"""
    def __init__(self, wmb_fp):
        super(wmb3_mesh, self).__init__()
        self.vertexGroupIndex = read_uint32(wmb_fp)
        self.bonesetIndex = read_uint32(wmb_fp)                    
        self.vertexStart = read_uint32(wmb_fp)                
        self.faceStart = read_uint32(wmb_fp)                    
        self.vertexCount = read_uint32(wmb_fp)                
        self.faceCount = read_uint32(wmb_fp)                    
        self.unknown18 = read_uint32(wmb_fp)

class wmb3_meshGroup(object):
    """docstring for wmb3_meshGroupInfo"""
    def __init__(self, wmb_fp):
        super(wmb3_meshGroup, self).__init__()
        nameOffset = read_uint32(wmb_fp)
        self.boundingBox = []
        #print("Iterating over 6, length %d" % 6)
        for i in range(6):
            self.boundingBox.append(read_float(wmb_fp))                                
        materialIndexArrayOffset = read_uint32(wmb_fp)
        materialIndexArrayCount = read_uint32(wmb_fp)
        boneIndexArrayOffset = read_uint32(wmb_fp)
        boneIndexArrayCount = read_uint32(wmb_fp)
        wmb_fp.seek(nameOffset)
        #print("Seeking to nameOffset: %s" % hex(nameOffset))
        self.meshGroupname = to_string(wmb_fp.read(256))
        self.materialIndexArray = []
        self.boneIndexArray = []
        wmb_fp.seek(materialIndexArrayOffset)
        #print("Seeking to materialIndexArrayOffset: %s" % hex(materialIndexArrayOffset))
        #print("Iterating over materialIndexArrayCount, length %d" % materialIndexArrayCount)
        for i in range(materialIndexArrayCount):
            self.materialIndexArray.append(read_uint16(wmb_fp))
        wmb_fp.seek(boneIndexArrayOffset)
        #print("Seeking to boneIndexArrayOffset: %s" % hex(boneIndexArrayOffset))
        #print("Iterating over boneIndexArrayCount, length %d" % boneIndexArrayCount)
        for i in range(boneIndexArrayCount):
            self.boneIndexArray.append(read_uint16(wmb_fp))

class wmb3_groupedMesh(object):
    """docstring for wmb3_groupedMesh"""
    def __init__(self, wmb_fp):
        super(wmb3_groupedMesh, self).__init__()
        self.vertexGroupIndex = read_uint32(wmb_fp)
        self.meshGroupIndex = read_uint32(wmb_fp)
        self.materialIndex = read_uint32(wmb_fp)
        self.colTreeNodeIndex = read_uint32(wmb_fp) 
        if self.colTreeNodeIndex == 0xffffffff:    
            self.colTreeNodeIndex = -1                    
        self.meshGroupInfoMaterialPair = read_uint32(wmb_fp)
        self.unknownWorldDataIndex = read_uint32(wmb_fp)
        if self.unknownWorldDataIndex == 0xffffffff:    
            self.unknownWorldDataIndex = -1

class wmb3_meshGroupInfo(object):
    """docstring for wmb3_meshGroupInfo"""
    def __init__(self, wmb_fp):
        super(wmb3_meshGroupInfo, self).__init__()
        self.nameOffset = read_uint32(wmb_fp)                    
        self.lodLevel = read_uint32(wmb_fp)
        if self.lodLevel == 0xffffffff:    
            self.lodLevel = -1                
        self.meshStart = read_uint32(wmb_fp)                        
        meshGroupInfoOffset = read_uint32(wmb_fp)            
        self.meshCount = read_uint32(wmb_fp)                        
        wmb_fp.seek(self.nameOffset)
        #print("Seeking to self.nameOffset: %s" % hex(self.nameOffset))
        self.meshGroupInfoname = to_string(wmb_fp.read(0x100))
        wmb_fp.seek(meshGroupInfoOffset)
        #print("Seeking to meshGroupInfoOffset: %s" % hex(meshGroupInfoOffset))
        self.groupedMeshArray = []
        #print("Iterating over self.meshCount, length %d" % self.meshCount)
        for i in range(self.meshCount):
            groupedMesh = wmb3_groupedMesh(wmb_fp)
            self.groupedMeshArray.append(groupedMesh)

class wmb3_vertexHeader(object):
    """docstring for wmb3_vertexHeader"""
    def __init__(self, wmb_fp):
        super(wmb3_vertexHeader, self).__init__()
        self.vertexArrayOffset = read_uint32(wmb_fp)        
        self.vertexExDataArrayOffset = read_uint32(wmb_fp)    
        self.unknown08 = read_uint32(wmb_fp)                
        self.unknown0C = read_uint32(wmb_fp)                
        self.vertexStride = read_uint32(wmb_fp)            
        self.vertexExDataStride = read_uint32(wmb_fp)        
        self.unknown18 = read_uint32(wmb_fp)                
        self.unknown1C = read_uint32(wmb_fp)                
        self.vertexCount = read_uint32(wmb_fp)            
        self.vertexFlags = read_uint32(wmb_fp)
        self.faceArrayOffset = read_uint32(wmb_fp)        
        self.faceCount = read_uint32(wmb_fp)                

class wmb3_vertexGroup(object):
    """docstring for wmb3_vertexGroup"""
    def __init__(self, wmb_fp, faceSize):
        super(wmb3_vertexGroup, self).__init__()
        self.faceSize = faceSize
        self.vertexGroupHeader = wmb3_vertexHeader(wmb_fp)

        self.vertexFlags = self.vertexGroupHeader.vertexFlags    
        
        self.vertexArray = [None] * self.vertexGroupHeader.vertexCount
        wmb_fp.seek(self.vertexGroupHeader.vertexArrayOffset)
        #print("Seeking to self.vertexGroupHeader.vertexArrayOffset: %s" % hex(self.vertexGroupHeader.vertexArrayOffset))
        #print("Iterating over self.vertexGroupHeader.vertexCount, length %d" % self.vertexGroupHeader.vertexCount)
        for vertex_index in range(self.vertexGroupHeader.vertexCount):
            vertex = wmb3_vertex(wmb_fp, self.vertexGroupHeader.vertexFlags)
            self.vertexArray[vertex_index] = vertex

        self.vertexesExDataArray = [None] * self.vertexGroupHeader.vertexCount
        wmb_fp.seek(self.vertexGroupHeader.vertexExDataArrayOffset)
        #print("Seeking to self.vertexGroupHeader.vertexExDataArrayOffset: %s" % hex(self.vertexGroupHeader.vertexExDataArrayOffset))
        #print("Iterating over self.vertexGroupHeader.vertexCount, length %d" % self.vertexGroupHeader.vertexCount)
        for vertexIndex in range(self.vertexGroupHeader.vertexCount):
            self.vertexesExDataArray[vertexIndex] = wmb3_vertexExData(wmb_fp, self.vertexGroupHeader.vertexFlags)

        self.faceRawArray = [None] * self.vertexGroupHeader.faceCount
        wmb_fp.seek(self.vertexGroupHeader.faceArrayOffset)
        #print("Seeking to self.vertexGroupHeader.faceArrayOffset: %s" % hex(self.vertexGroupHeader.faceArrayOffset))
        #print("Iterating over self.vertexGroupHeader.faceCount, length %d" % self.vertexGroupHeader.faceCount)
        for face_index in range(self.vertexGroupHeader.faceCount):
            if faceSize == 2:
                self.faceRawArray[face_index] = read_uint16(wmb_fp) + 1
            else:
                self.faceRawArray[face_index] = read_uint32(wmb_fp) + 1

class wmb3_vertex(object):
    smartRead = SmartIO.makeFormat(
        SmartIO.float,
        SmartIO.float,
        SmartIO.float,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartReadUV2 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
    )

    """docstring for wmb3_vertex"""
    def __init__(self, wmb_fp, vertex_flags):
        super(wmb3_vertex, self).__init__()
        # self.positionX = read_float(wmb_fp)
        # self.positionY = read_float(wmb_fp)
        # self.positionZ = read_float(wmb_fp)
        # self.normalX = read_uint8(wmb_fp) * 2 / 255            
        # self.normalY = read_uint8(wmb_fp) * 2 / 255    
        # self.normalZ = read_uint8(wmb_fp) * 2 / 255    
        # wmb_fp.read(1)                                            
        # self.textureU = read_float16(wmb_fp)                
        # self.textureV = read_float16(wmb_fp)
        self.positionX, \
        self.positionY, \
        self.positionZ, \
        self.normalX, \
        self.normalY, \
        self.normalZ, \
        _, \
        self.textureU, \
        self.textureV = wmb3_vertex.smartRead.read(wmb_fp)
        self.normalX = self.normalX * 2 / 255
        self.normalY = self.normalY * 2 / 255
        self.normalZ = self.normalZ * 2 / 255

        if vertex_flags == 0:
            self.normal = hex(read_uint64(wmb_fp))
        if vertex_flags in {1, 4, 5, 12, 14}:
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            self.textureU2, \
            self.textureV2 = wmb3_vertex.smartReadUV2.read(wmb_fp)
        if vertex_flags in {7, 10, 11}:
            self.boneIndices = read_uint8_x4(wmb_fp)
            self.boneWeights = [x / 255 for x in read_uint8_x4(wmb_fp)]
        if vertex_flags in {4, 5, 12, 14}:
            self.color = read_uint8_x4(wmb_fp)

class wmb3_vertexExData(object):
    smartRead5 = SmartIO.makeFormat(
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartRead7 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.uint64,
    )
    smartRead10 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint64,
    )
    smartRead11 = SmartIO.makeFormat(
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint8,
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartRead12 = SmartIO.makeFormat(
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
    )
    smartRead14 = SmartIO.makeFormat(
        SmartIO.uint64,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
        SmartIO.float16,
    )

    """docstring for wmb3_vertexExData"""
    def __init__(self, wmb_fp, vertex_flags):
        super(wmb3_vertexExData, self).__init__()
        
        #0x0 has no ExVertexData

        if vertex_flags in {1, 4}: #0x1, 0x4
            self.normal = hex(read_uint64(wmb_fp))

        elif vertex_flags == 5: #0x5
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            self.normal, \
            self.textureU3, \
            self.textureV3 = wmb3_vertexExData.smartRead5.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 7: #0x7
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            # self.normal = hex(read_uint64(wmb_fp))
            self.textureU2, \
            self.textureV2, \
            self.normal = wmb3_vertexExData.smartRead7.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 10: #0xa
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            # self.color = read_uint8_x4(wmb_fp)
            # self.normal = hex(read_uint64(wmb_fp))
            self.color = [0, 0, 0, 0]
            self.textureU2, \
            self.textureV2, \
            self.color[0], \
            self.color[1], \
            self.color[2], \
            self.color[3], \
            self.normal = wmb3_vertexExData.smartRead10.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 11: #0xb
            # self.textureU2 = read_float16(wmb_fp)                
            # self.textureV2 = read_float16(wmb_fp)
            # self.color = read_uint8_x4(wmb_fp)
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            self.color = [0, 0, 0, 0]
            self.textureU2, \
            self.textureV2, \
            self.color[0], \
            self.color[1], \
            self.color[2], \
            self.color[3], \
            self.normal, \
            self.textureU3, \
            self.textureV3 = wmb3_vertexExData.smartRead11.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 12: #0xc
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            # self.textureU4 = read_float16(wmb_fp)                
            # self.textureV4 = read_float16(wmb_fp)
            # self.textureU5 = read_float16(wmb_fp)                
            # self.textureV5 = read_float16(wmb_fp)
            self.normal, \
            self.textureU3, \
            self.textureV3, \
            self.textureU4, \
            self.textureV4, \
            self.textureU5, \
            self.textureV5 = wmb3_vertexExData.smartRead12.read(wmb_fp)
            self.normal = hex(self.normal)

        elif vertex_flags == 14: #0xe
            # self.normal = hex(read_uint64(wmb_fp))
            # self.textureU3 = read_float16(wmb_fp)                
            # self.textureV3 = read_float16(wmb_fp)
            # self.textureU4 = read_float16(wmb_fp)                
            # self.textureV4 = read_float16(wmb_fp)
            self.normal, \
            self.textureU3, \
            self.textureV3, \
            self.textureU4, \
            self.textureV4 = wmb3_vertexExData.smartRead14.read(wmb_fp)
            self.normal = hex(self.normal)

class wmb3_worldData(object):
    """docstring for wmb3_unknownWorldData"""
    def __init__(self, wmb_fp):
        self.unknownWorldData = []
        #print("Iterating over 6, length %d" % 6)
        for entry in range(6):
            self.unknownWorldData.append(wmb_fp.read(4))
