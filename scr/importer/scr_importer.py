import bpy
import os
import struct
from pathlib import Path
import shutil
# Replace the import statement below with the correct path to your WMB importer
from ...wmb.importer import wmb_importer  # Assuming wmb_importer.py is in root/wmb/importer
from ...dat_dtt.importer import datImportOperator

class ImportSCR:
    def main(file_path, context):
        print('Beginning export')
        #print(file_path, context)
        trueFilePath = file_path # thanks for the var reuse
        head = os.path.split(file_path)[0]
        with open(file_path, 'rb') as f:
            id = f.read(4)
            print('ID read')
            if id != b'SCR\x00':
                raise ValueError("Wrong file type")
    
            f.seek(0)
            header = struct.unpack('<4s2hI', f.read(12))
            num_models = header[2]
            offset_offsets_models = header[3]
        
            f.seek(offset_offsets_models)
            offsets_models = struct.unpack(f'<{num_models}I', f.read(num_models * 4))
            print('Offsets found')
        
            model_headers = []
            for i in range(num_models):
                f.seek(offsets_models[i])
                model_header = struct.unpack('<I64s9f18h', f.read(140))
                model_headers.append(model_header)
                print('Model header read')
        
            model_data = []
            for i in range(num_models):
                f.seek(model_headers[i][0])
                if i == num_models - 1:
                    size = os.path.getsize(file_path) - model_headers[i][0]
                else:
                    size = offsets_models[i+1] - model_headers[i][0]
                if size > 0:
                    model = f.read(size)
                    model_data.append(model)
                    print('SCR read completed')
                    print('Beginning extract')
                    if not os.path.exists(head + '/extracted_scr'):
                        os.makedirs(head + '/extracted_scr')
                
                    for i, (header, model) in enumerate(zip(model_headers, model_data)):
                        file_name = header[1].decode('utf-8').rstrip('\x00')
                        file_path = f"{head}/extracted_scr/{file_name}.wmb"
                        with open(file_path, 'wb') as f2:
                            f2.write(model)
                    print('SCR extract completed')
                    if not (context):
                        print('Beginning WMB import')                    
                        ImportSCR.import_models(file_path, header)  
                        
                print('SCR extract completed')
        
        if os.path.exists(trueFilePath[:-3] + "ly2"):
            # prop import
            # bad practice but I'll be, uh, not making an LY2 format
            ly2 = open(trueFilePath[:-3] + "ly2", "rb")
            if ly2.read(4) != b'LY2\x00':
                print("Error in prop load: not LY2 format")
                return {'FINISHED'}
            
            print("Loading props")
            ly2.seek(8) # yeah we skip the flags
            propTypeCount = struct.unpack("<I", ly2.read(4))[0]
            ly2.seek(0x14) # start of main data
            for i in range(propTypeCount):
                ly2.read(8) # some flags
                prop_category = ly2.read(2).decode("ascii")
                if prop_category not in {"ba", "bh", "bm"}:
                    print("Prop category (%s) not in data001, skipping" % prop_category)
                    continue
                prop_id = "%04x" % struct.unpack("<H", ly2.read(2))[0]
                prop_name = prop_category + prop_id
                # for my next trick, I shall escape the Matrix
                if os.path.exists(head + "/../" + prop_name + ".dat"):
                    # already extracted to n2b2n_extracted
                    import_mode = "wmb"
                    prop_path = head + "/../" + prop_name + ".dat/" + prop_name + ".wmb"
                elif os.path.exists(head + "/../../../" + prop_category + "/" + prop_name + ".dtt"):
                    # go up to its original home
                    import_mode = "dtt"
                    prop_path = head + "/../../../" + prop_category + "/" + prop_name + ".dtt"
                else:
                    # no i'm not making an extra cpk extractor
                    print("Could not find %s to extract, skipping" % prop_name)
                    continue
                
                instancesPointer = struct.unpack("<I", ly2.read(4))[0]
                instancesCount = struct.unpack("<I", ly2.read(4))[0]
                resumePos = ly2.tell()
                
                ly2.seek(instancesPointer)
                for j in range(instancesCount):
                    posX, posY, posZ = struct.unpack("<fff", ly2.read(12))
                    scaleX, scaleY, scaleZ = struct.unpack("<fff", ly2.read(12))
                    rotX = rotZ = 0 # rotation is weirder
                    ly2.read(4)
                    rotY = struct.unpack("BBBB", ly2.read(4))[0]
                    ly2.read(8)
                    rotY *= 3.1415926535 / 0x80
                    prop_transform = [posX, posY, posZ, rotX, rotY, rotZ, scaleX, scaleY, scaleZ]
                    if import_mode == "dtt":
                        datImportOperator.importDtt(False, prop_path, prop_transform)
                    elif import_mode == "wmb":
                        wmb_importer.main(False, prop_path, prop_transform)
                    
                
                ly2.seek(resumePos)
                
            
            ly2.close()
        
        return {'FINISHED'}

    @staticmethod
    def import_models(file_path, scr_header):
            wmb_importer.main(False, file_path, scr_header[2:11])

def reset_blend():
    #bpy.ops.object.mode_set(mode='OBJECT')
    for collection in bpy.data.collections:
        for obj in collection.objects:
            collection.objects.unlink(obj)
        bpy.data.collections.remove(collection)
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.libraries):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for amt in bpy.data.armatures:
        bpy.data.armatures.remove(amt)
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
        obj.user_clear()