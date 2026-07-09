import math

import bpy
from pathlib import Path
import json
import os
from mathutils import Quaternion, Matrix, Vector


def read_transform(transform: dict,attach_bone_pos,ob_parent):
    print(transform)
    if "RelativeLocation" in transform:
        t = transform['RelativeLocation'] or {'X': 0, 'Y': 0, 'Z': 0}
        r = transform['RelativeRotation'] or {'Pitch': 0, 'Yaw': 0, 'Roll': 0}
        s = transform['RelativeScale3D'] or {'X': 1, 'Y': 1, 'Z': 1}
        
        if len(r) > 3:
            quat = Quaternion((-r['W'], r['X'], -r['Y'], r['Z']))
            euler = quat.to_euler("XYZ")
            rot = euler.x, euler.y, euler.z
        else:
            rot = (math.radians(r['Roll']), math.radians(-r['Pitch']), math.radians(-r['Yaw'])) # X=Z Y=X Z=X
    else:
        t = {'X': 0, 'Y': 0, 'Z': 0}
        rot = (math.radians(0), math.radians(0), math.radians(0))
        s = {'X': 1, 'Y': 1, 'Z': 1}
        
    # unreal is in CM with the Y inverted
    if attach_bone_pos:
        print(attach_bone_pos)
        pos = t['X']+(attach_bone_pos[0]*100), -t['Y']+(attach_bone_pos[1]*100), t['Z']+(attach_bone_pos[2]*100)
        print(pos)
    else:
        if not ob_parent:
            pos = t['X'] / 100.0, -t['Y'] / 100.0, t['Z'] / 100.0
        else:
            pos = t['X'], -t['Y'], t['Z']
        
    if not ob_parent:
        scale = s['X'] / 100.0, s['Y'] / 100.0, s['Z'] / 100.0
    else:
        scale = s['X'], s['Y'], s['Z']

    return pos, rot, scale

def import_model(
    asset: dict,
    buildable_name:str,
    file: Path,
    parent_name:str,
    parent_attach:str,
    support_name:str = "",
    pole_height:float = 0.0):
    file_name = file.name.split('.')[0]
    sk_mesh_name = file.name.split('.')[0]+".001"
    
    file_type = file.name.split('.')[1]
    #if file_type.endswith('psk'):
    #    file_name = file_name+".001"
    print(f"file_name {file_name}")
    ob_parent = None
    attach_bone_pos = None
    support_ob_org = None
    support_ob_dp = None
    ob_sk_mesh = None
    
    #parent_name = ""
    #parent_attach = ""
    
    
    ob = bpy.data.objects.get(file_name)
    if ob != None:
        print(f"{file_name} already in blend file.")
        
        if ob.type == "ARMATURE":
            ob_sk_mesh = bpy.data.objects.get(sk_mesh_name.replace(".001","_mesh"))
            print(f"ob_sk_mesh: {ob_sk_mesh}")
        if ob_sk_mesh != None:
            sk_duplicate = ob.copy()
            sk_data_duplicate = ob.data.copy()
            sk_duplicate.data = sk_data_duplicate
            ob = sk_duplicate
            
            mesh_duplicate = ob_sk_mesh.copy()
            mesh_data_duplicate = ob_sk_mesh.data.copy()
            mesh_duplicate.data = mesh_data_duplicate
            ob_sk_mesh = mesh_duplicate
            
            for mod in ob_sk_mesh.modifiers:
                if mod.type == 'ARMATURE':
                    mod.object = ob
                    
            ob_sk_mesh.parent = ob
        else:
            obj_duplicate = ob.copy()
            ob = obj_duplicate
        
    else:
        if 'pskx' in os.fspath(file):
            is_pskx = "MESH"
        else:
            is_pskx = "ALL"
        print(f"{file_name} not in blend file. Needs to be imported")
        bpy.ops.psk.import_file(
            filepath=os.fspath(file),
            should_import_mesh=True, 
            should_import_armature=True,
            bone_length=30,
            #scale=.01,
            components=is_pskx
        )
        ob = bpy.data.objects.get(file_name)
        if ob.type == "ARMATURE":
            ob_sk_mesh = bpy.data.objects.get(sk_mesh_name)
            if ob_sk_mesh != None:
                ob_sk_mesh.name = sk_mesh_name.replace(".001","_mesh")
    
    if parent_name:
        ob_parent = bpy.data.objects.get(parent_name)
        print(f"parent_name: {parent_name}")
        
        if parent_attach:
            attach_bone = ob_parent.data.bones[parent_attach]
            attach_bone_pos_head = ob_parent.matrix_world @ attach_bone.head_local
            attach_bone_pos_tail = ob_parent.matrix_world @ attach_bone.tail_local
            attach_bone_pos = attach_bone_pos_head-attach_bone_pos_tail
            print(f"attach_bone_pos: {attach_bone_pos}")
            
    pos, rot, scale = read_transform(asset,attach_bone_pos,ob_parent)
    if parent_attach:
        ob.parent = ob_parent
        ob.parent_type = 'BONE'
        ob.parent_bone = parent_attach 
    else:
        ob.parent = ob_parent
    ob.location = pos
    ob.rotation_euler = rot
    ob.scale = scale
    
    print(f"{support_name}:{pole_height}")
    if support_name:
        print("duplicating support mesh..")
        support_ob_org = bpy.data.objects.get(support_name)
        support_ob_org.scale = (1.0, 1.0, 1.0)
        support_ob_dp = support_ob_org.copy()
        support_ob_dp.data = support_ob_org.data.copy()
        support_ob_dp_loc = support_ob_dp.location * 100 
        support_ob_dp.parent = ob
        #support_ob_dp.location = support_ob_dp_loc*100
        support_ob_dp.location.z = support_ob_dp_loc.z + pole_height
        support_ob_dp.location = support_ob_dp.location
        print(f"support name:{support_ob_dp.name}⚠️")
        

    sc_col = bpy.context.scene.collection
    
    if ob_sk_mesh != None and ob.type == 'ARMATURE':
        ob.data.display_type = 'STICK'
        
    if sc_col in ob.users_collection:
        bpy.context.scene.collection.objects.unlink(ob) 
    if ob_sk_mesh != None and sc_col in ob_sk_mesh.users_collection:
        bpy.context.scene.collection.objects.unlink(ob_sk_mesh) 
    col = bpy.data.collections.get(buildable_name)
    if not col:
        col = bpy.data.collections.new(buildable_name)
        bpy.context.scene.collection.children.link(col)
    
    if col not in ob.users_collection:
        col.objects.link(ob)
        if support_ob_dp:
            if col not in support_ob_dp.users_collection:
                col.objects.link(support_ob_dp)
        #if support_ob_dp:
        #    col.objects.link(support_ob_dp)
        #    #if "." in support_ob_org.name:
        #    #    col.objects.link(support_ob_org)

    if ob_sk_mesh != None and col not in ob_sk_mesh.users_collection:
        col.objects.link(ob_sk_mesh)
    
    return ob.name#,ob_sk_mesh.name
    # Extract material names from the object's slots
        #obj_materials = [slot.material.name for slot in ob.material_slots if slot.material]
        #print(f"Materials on {ob.name}: {obj_materials}")
        #continue
    
print("---------------------------------------------------------")
#bpy.ops.psk.import_file(psk=file,should_import_mesh=True, should_import_armature=True)

BASE_FILE_DIR = r"PATH-TO-FMODEL-EXPORTS\FactoryGame\Content\FactoryGame\Buildable"
BUILD_TO_ASSET_DIR = r"PROJECT-PATH\impot models\buildable_to_asset.json"

FILE_EXTENTIONS = [
    "png",
    "tga"
]

psk_files = list(Path(BASE_FILE_DIR).rglob("*.psk"))
pskx_files = list(Path(BASE_FILE_DIR).rglob("*.pskx"))
asset_files = psk_files + pskx_files

is_pskx = "ALL"

bpy.ops.outliner.orphans_purge(do_recursive=True)

with open(BUILD_TO_ASSET_DIR, 'r', encoding='utf-8') as f:
    build_to_asset = json.load(f)
count = 0
for build in build_to_asset:
    buildable = build_to_asset[build]
    buildable_name = buildable['ObjectName']
    
    count += 1
    if count > 5:
        #break
        ...
    asset_list = {}
    support_name = ""
    support_mesh = []
    for component in buildable:
        if component == 'ObjectName':# or asset == 'ProductionIndicator':
            continue
        asset = buildable.get(component)
        if not asset:
            continue
        
        print(component)
        print("===============")
        if type(asset) == list:
            
            for ast in asset:
                print("--------------")
                asset_name = ast.get('Mesh')
                multiple_files = []
                pole_height = ast.get('Height')
                
                builable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
                
                if builable_file:
                    if 1 < len(builable_file):
                        print("Multiple files found:")
                        #multiple_files = builable_filea
                        file = builable_file[1]
                    else:
                        file = builable_file[0]
                else:
                    print(f"Not Found: {asset_name}")
                    continue
                
                parent_name = ""
                parent_attach = ""
                parent_comp_name = ast.get('Parent')
                print(f"asset.get('Mesh') {ast.get('Mesh')}")
                if parent_comp_name:
                    print(asset_list.get(parent_comp_name))
                    if asset_list.get(parent_comp_name):
                        parent_name = asset_list.get(parent_comp_name,"") 
                    else:
                        parent_name = buildable[parent_comp_name].get('Mesh',"")
                    print(f"parent_name: {parent_name}")
                    parent_attach = ast.get('ParentAttach',"")
                    print(f"parent_attach: {parent_attach}")
                
                ob_name = import_model(asset=ast,
                    buildable_name=buildable_name,
                    file=file,
                    parent_name=parent_name,
                    parent_attach=parent_attach,
                    support_name=support_name,
                    pole_height = pole_height
                    )
                
                asset_list[component] = ob_name
                print(asset_list)
            
            support_ob_org = bpy.data.objects.get(support_name)    
            if support_ob_org:
                bpy.data.objects.remove(support_ob_org, do_unlink=True)
        else:   
            asset_name = asset.get('Mesh')
            multiple_files = []
            if "mSupportMeshInstanceData" in component:
                support_name = asset_name
            print(f"does {build} have mSupportMeshInstanceData: {support_name}")
            
            builable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
            
            if builable_file:
                if 1 < len(builable_file):
                    print(f"Multiple files found: {builable_file}")
                    #multiple_files = builable_filea
                    if "TradingPost" in str(builable_file[0]):
                        file = builable_file[1]
                    else:   
                        file = builable_file[0]
                else:
                    file = builable_file[0]
            else:
                print(f"Not Found: {asset_name}")
                continue
            
            parent_name = ""
            parent_attach = ""
            parent_comp_name = asset.get('Parent')
            
            if parent_comp_name:
                if asset_list.get(parent_comp_name):
                    parent_name = asset_list.get(parent_comp_name,"") 
                else:
                    parent_name = buildable[parent_comp_name].get('Mesh',"")
                print(f"parent_name: {parent_name}")
                parent_attach = asset.get('ParentAttach',"")
                print(f"parent_attach: {parent_attach}")
            
            ob_name = import_model(asset=asset,
                buildable_name=buildable_name,
                file=file,
                parent_name=parent_name,
                parent_attach=parent_attach,
                )
            
            asset_list[component] = ob_name
            print(asset_list)