import math
import time

import bpy
from pathlib import Path
import json
import os
from mathutils import Quaternion, Matrix, Vector

def get_or_create_collection(name,parent_name = "") -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    parent_col = bpy.data.collections.get(parent_name)
    if not col:
        col = bpy.data.collections.new(name)
        if not parent_name:
            bpy.context.scene.collection.children.link(col)
        else:
            parent_col.children.link(col)
            
    return col

def get_asset_collection() -> bpy.types.Collection:
    return get_or_create_collection('Assets')

def get_essential_collection() -> bpy.types.Collection:
    return get_or_create_collection('essentials')

def read_transform(transform: dict,attach_bone_pos,ob_parent):
    #print(transform)
    if "RelativeLocation" in transform:
        if transform['RelativeLocation'] == None:
            t = {'X': 0, 'Y': 0, 'Z': 0}
        else:
            t = transform['RelativeLocation']
        if transform['RelativeRotation'] == None:
            r = {'Pitch': 0, 'Yaw': 0, 'Roll': 0}
        else:
            r = transform['RelativeRotation']
        if transform['RelativeScale3D'] == None:
            s = {'X': 1, 'Y': 1, 'Z': 1}
        else:
            s = transform['RelativeScale3D']
        
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
        pos = t['X']+(attach_bone_pos[0]*100), -t['Y']+(attach_bone_pos[1]*100), t['Z']+(attach_bone_pos[2]*100)
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
    print(f"file_name: {file_name}")
    ob_parent = None
    attach_bone_pos = None
    support_ob_org = None
    support_ob_dp = None
    ob_sk_mesh = None
    parent_col = None
    
    #parent_name = ""
    #parent_attach = ""
    
    
    ob = bpy.data.objects.get(file_name)
    if ob != None:
        print(f"{file_name} already in blend file.")
        
        if ob.type == "ARMATURE":
            ob_sk_mesh = bpy.data.objects.get(sk_mesh_name.replace(".001","_mesh"))
            #print(f"ob_sk_mesh: {ob_sk_mesh}")
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
        if 'pskx' in os.fspath(file) and "SK_Tradingpost" not in os.fspath(file):
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
        
        if "SM_Blender_01" in ob.name:
            ob.name = "SM_Blender_factory"
            
            
        if ob.type == "ARMATURE":
            ob_sk_mesh = bpy.data.objects.get(sk_mesh_name)
            if ob_sk_mesh != None:
                ob_sk_mesh.name = sk_mesh_name.replace(".001","_mesh")
    
    if parent_name:
        ob_parent = bpy.data.objects.get(parent_name)
        if ob_parent:
            if len(ob_parent.users_collection) == 1:
                for p_col in ob_parent.users_collection:
                    #if p_col.name == ob_parent.name:
                    #    parant_col = p_col
                    parent_col = p_col
        #print(f"parent_name: {parent_name}")
        
        if parent_attach:
            attach_bone = ob_parent.data.bones[parent_attach]
            attach_bone_pos_head = ob_parent.matrix_world @ attach_bone.head_local
            attach_bone_pos_tail = ob_parent.matrix_world @ attach_bone.tail_local
            attach_bone_pos = attach_bone_pos_head-attach_bone_pos_tail
            #print(f"attach_bone_pos: {attach_bone_pos}")
            
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
    
    #print(f"{support_name}:{pole_height}")
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
    as_col = get_asset_collection()
    get_or_create_collection("Utility")
    get_or_create_collection("ConveyorLifts","Utility")
    get_or_create_collection("Factory","Assets")
    get_or_create_collection("Building","Assets")
    lift_parts_col = get_or_create_collection("LiftParts","ConveyorLifts")
    lifts_col = get_or_create_collection("Lifts","ConveyorLifts")
    conveyor_belts_col = get_or_create_collection("ConveyorBelts","Utility")
    
    if ob_sk_mesh != None and ob.type == 'ARMATURE':
        ob.data.display_type = 'STICK'
        
    if sc_col in ob.users_collection:
        bpy.context.scene.collection.objects.unlink(ob) 
    if ob_sk_mesh != None and sc_col in ob_sk_mesh.users_collection:
        bpy.context.scene.collection.objects.unlink(ob_sk_mesh) 
    
    if any(build in buildable_name for build in INTEGRATED_BUILD_LIST):
        col = get_or_create_collection(buildable_name,"Utility")
    else:
        if "Building" in os.fspath(file) or "Prototype" in os.fspath(file):
            col = get_or_create_collection(buildable_name,"Building")
        else:
            col = get_or_create_collection(buildable_name,"Factory")
        
    if parent_col:
        col = parent_col
    
    if "ConveyorBeltMk" in buildable_name:
        if conveyor_belts_col not in ob.users_collection:
            conveyor_belts_col.objects.link(ob)
    if "ConveyorLiftMk" in buildable_name:
        if "ConveyorLiftMid_M" in file_name:
            if not "." in ob.name:
                if lifts_col not in ob.users_collection:
                    lifts_col.objects.link(ob)
        if "ConveyorLift_" in file_name:
            if not "." in ob.name:
                if lift_parts_col not in ob.users_collection:
                    lift_parts_col.objects.link(ob)
        
    is_SK_Tradingpost = False
    if "TradingPost" in buildable_name:
        stg_col = get_or_create_collection("TradingpostStages",buildable_name)
        sk_col = get_or_create_collection("SK_Tradingpost",buildable_name)
        #props_col = get_or_create_collection("TradingpostProps",buildable_name)
        
        if "SM_Hub_Stg_" in file_name:
            if stg_col not in ob.users_collection:
                stg_col.objects.link(ob)
        elif "SK_Tradingpost" in file_name:
            if sk_col not in ob.users_collection:
                sk_col.objects.link(ob)
                if ob_sk_mesh != None and sk_col not in ob_sk_mesh.users_collection:
                    sk_col.objects.link(ob_sk_mesh)
                    is_SK_Tradingpost = True
        else:
            if col not in ob.users_collection:
                col.objects.link(ob)
                if support_ob_dp:
                    if col not in support_ob_dp.users_collection:
                        col.objects.link(support_ob_dp)
    else:    
        if col not in ob.users_collection:
            col.objects.link(ob)
            if support_ob_dp:
                if col not in support_ob_dp.users_collection:
                    col.objects.link(support_ob_dp)
            #if support_ob_dp:
            #    col.objects.link(support_ob_dp)
            #    #if "." in support_ob_org.name:
            #    #    col.objects.link(support_ob_org)

    if "TradingPost" not in buildable_name:
        if ob_sk_mesh != None and col not in ob_sk_mesh.users_collection and is_SK_Tradingpost == False:
            col.objects.link(ob_sk_mesh)
    
    return ob.name
        
def import_empty(
    asset: dict,
    buildable_name:str,
    empty_name:str = ""):
    print(f"file_name: {empty_name}")
    attach_bone_pos = None
    
    
    ob = bpy.data.objects.get(empty_name)
    if ob != None:
        print(f"{empty_name} already in blend file.")
        
        obj_duplicate = ob.copy()
        ob = obj_duplicate
        
    else:
        print(f"{empty_name} not in blend file. Needs to be imported")
        # TODO
        ob = bpy.data.objects.new(empty_name, None)
        ob.empty_display_type = 'CUBE'
        #bpy.ops.object.empty_add(type='CUBE')
        #ob = bpy.data.objects.get(empty_name)
        ob.scale = ob.scale*100
        ctx = bpy.context.copy()
        ctx["active_object"] = ob
        ctx["selected_editable_objects"] = [ob]
         
        with bpy.context.temp_override(**ctx):
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            
    pos, rot, scale = read_transform(asset,None,None)
    
    ob.location = pos
    ob.rotation_euler = rot
    ob.scale = scale

    sc_col = bpy.context.scene.collection
        
    if sc_col in ob.users_collection:
        bpy.context.scene.collection.objects.unlink(ob) 
        
    get_or_create_collection("Factory","Assets")
    get_or_create_collection(buildable_name,"Factory")
    get_or_create_collection("TradingpostProps",buildable_name)
    col = get_or_create_collection(empty_name,"TradingpostProps")
   
    if col not in ob.users_collection:
        col.objects.link(ob)
    
    return ob

def main():
    print("---------------------------------------------------------")
    start_time = time.perf_counter()
    #bpy.ops.psk.import_file(psk=file,should_import_mesh=True, should_import_armature=True)

    FILE_EXTENTIONS = [
        "png",
        "tga"
    ]

    psk_files = list(Path(BASE_FILE_DIR).rglob("*.psk"))
    pskx_files = list(Path(BASE_FILE_DIR).rglob("*.pskx"))
    event_psk_files = list(Path(EVENT_FILE_DIR).rglob("*.psk"))
    event_pskx_files = list(Path(EVENT_FILE_DIR).rglob("*.pskx"))
    asset_files = psk_files + pskx_files + event_psk_files + event_pskx_files

    is_pskx = "ALL"
    clear_asset_col = True
    
    if clear_asset_col:
        col = get_or_create_collection('Assets')
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for col in list(col.children):
            bpy.data.collections.remove(col, do_unlink=True)
        
        col = get_or_create_collection('Utility')
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for col in list(col.children):
            bpy.data.collections.remove(col, do_unlink=True)
            
    else:
        get_asset_collection()

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
                    asset_dir = ""
                    buildable_file = ""
                    if '/' in asset_name:
                        asset_dir =Path(asset_name)
                        asset_name = asset_name.split('/')[-1]
                    
                    pole_height = ast.get('Height')
                    
                    if asset_dir:
                        for asset_file in asset_files:
                            if os.fspath(asset_dir) in os.fspath(asset_file):
                                if asset_file.name.startswith(asset_name+'.'):
                                    buildable_file = asset_file
                    else:
                        buildable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
                        
                    
                    if buildable_file:
                        if type(buildable_file) == list:
                            file = buildable_file[0]
                        else:
                            file = buildable_file
                    else:
                        print(f"Not Found: {asset_name}")
                        continue
                    
                    parent_name = ""
                    parent_attach = ""
                    parent_comp_name = ast.get('Parent')
                    if parent_comp_name:
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
                    #print(asset_list)
                
                support_ob_org = bpy.data.objects.get(support_name)    
                if support_ob_org:
                    bpy.data.objects.remove(support_ob_org, do_unlink=True)
            elif "Props" in component:
                
                asset_name = asset.get('Mesh')
                empty_name =component.split('_')[0]
                prop_components = asset["Props"]
                
                prop_perant = import_empty(asset=asset,
                    buildable_name=buildable_name,
                    empty_name=empty_name
                    )
                
                
                for prop in prop_components:
                    print("--------------")
                    ast = prop_components[prop]
                    asset_name = ast.get('Mesh')
                    asset_dir = ""
                    buildable_file = ""
                    if '/' in asset_name:
                        asset_dir =Path(asset_name)
                        asset_name = asset_name.split('/')[-1]
                    
                    if asset_dir:
                        for asset_file in asset_files:
                            
                            if os.fspath(asset_dir) in os.fspath(asset_file):
                                buildable_file = asset_file
                    else:
                        buildable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
                    
                    if buildable_file:
                        if type(buildable_file) == list:
                            file = buildable_file[0]
                        else:
                            file = buildable_file
                    else:
                        print(f"Not Found: {asset_name}")
                        continue
                    
                    parent_name = prop_perant.name
                    parent_attach = ""
                    parent_comp_name = ast.get('Parent')
                    
                    ob_name = import_model(asset=ast,
                        buildable_name=buildable_name,
                        file=file,
                        parent_name=parent_name,
                        parent_attach=parent_attach
                        )
                    
                    asset_list[prop] = ob_name
                    #print(asset_list)
            else:   
                
                asset_name = asset.get('Mesh')
                asset_dir = ""
                buildable_file = ""
                if '/' in asset_name:
                    asset_dir =Path(asset_name)
                    
                    asset_name = asset_name.split('/')[-1] # type: str
                    
                if "mSupportMeshInstanceData" in component:
                    support_name = asset_name
                print(f"does {build} have mSupportMeshInstanceData: {support_name}")
                    
                if asset_dir:
                    for asset_file in asset_files:
                        if os.fspath(asset_dir) in os.fspath(asset_file):
                            if asset_file.name.startswith(asset_name+'.'):
                                buildable_file = asset_file
                                print(buildable_file)
                        
                        if asset_dir.name in asset_file.parent.name:
                            asset_file_l = asset_file.stem.lower()
                            if asset_file_l == asset_name.lower():
                                buildable_file = asset_file
                                print(buildable_file)
                else:
                    buildable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
                    print(buildable_file)
                    
                    
                if buildable_file:
                    #if type(buildable_file) == list:
                    #    file = buildable_file[0]
                    #else:
                    #    file = buildable_file
                    if type(buildable_file) == list:
                        if 1 < len(buildable_file):
                            print(f"Multiple files found: {buildable_file}")
                            #multiple_files = builable_filea
                            if "TradingPost" in str(buildable_file[0]):
                                file = buildable_file[1]
                            else:   
                                file = buildable_file[0]
                        else:
                            file = buildable_file[0]
                    else:
                        file = buildable_file
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
                    parent_attach=parent_attach
                    )
                
                asset_list[component] = ob_name
                #print(asset_list)
                
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Importing models time: {execution_time:.6f} seconds")

EXPORT_FILE_DIR = r"PATH-TO-FMODEL-EXPORTS"
BASE_FILE_DIR = r"PATH-TO-FMODEL-EXPORTS\fmodel export\FactoryGame\Content\FactoryGame\Buildable"
EVENT_FILE_DIR = r"PATH-TO-FMODEL-EXPORTS\fmodel export\FactoryGame\Content\FactoryGame\Events"
BUILD_TO_ASSET_DIR = r"PROJECT-PATH\import models\buildable_to_asset.json"   

INTEGRATED_BUILD_LIST = [
    "ProductionIndicatorInstanced",
    "HubTerminal",
    "Integrate",
    "ElevatorCabin",
    "StorageBlueprint",
    "PipelineFlowIndicator"
]

if __name__ == "__main__":
    main()