import math
from re import search
import time

import bpy
from pathlib import Path
import json
import os
from mathutils import Quaternion, Matrix, Vector

def set_geonode_input(modifier: bpy.types.Modifier, label: str, value):
    for item in modifier.node_group.interface.items_tree:
        if getattr(item, "in_out", None) == "INPUT" and item.name == label:
            if bpy.app.version < (5, 2, 0):
                modifier[item.identifier] = value
            else:
                input_prop = getattr(modifier.properties.inputs, item.identifier)
                input_prop.value = value
            return
    raise KeyError(f"Input '{label}' not found")

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

def get_materials(ob,obj_material: str, file: Path,index:int,sf_asset_export_path):
    print("---------")
    print("Getting Matetrals")
    parent_path = file.parent
    print(parent_path)
    
    rn_type_tex = [
        "_N",
        "_Nor",
        "_MREO",
        "_Rough",
        "_Relf",
        "_Refl",
        "_REFL",
        "_RELF"
    ]
    
    rough_type_tex = [
        "_MREO",
        "_Rough",
        "_Refl",
        "_Relf",
        "_REFL",
        "_RELF"
    ]
    
    color_type_tex = [
        "_BC",
        "_BaseColor",
        "_Alb"
    ]
    
    ao_type_tex = [
        "_AO",
        #"",
    ]
    
    screen_type_mat = [
        "Display",
        "Monitor"
    ]
    
    force_use_factory_01 = [
        "MI_Elevator",
        "MI_Factory_Base_01",
        "SpaceElevator_Inst",
        "MI_PowerStorage_Inst",
        "MI_ResourceSink_01",
        "Walkways_Inst",
        "MI_InPuts",
        "MI_Fracker_01",
        "MI_Blender",
        "MI_TradingPostStage5",
        "MI_Packager",
        "MI_Pump_01",
        "MI_Truckstation",
    ]
    
    force_get_texture = [
        "Light_Vertical_Blinking_Mask"
    ]
    
    mirrored_tex = [
        "SM_BigDoor_01",
        "MI_Foundation_FicsitSet_",
        "MI_SteelWall_",
        "MI_Door_01",
        "MI_WallSetConcrete_"
    ]
    
    emision_type_mats = [
        "MI_PriorityLightsLift_01"
    ]
    
    force_replace_mat = {
        "MI_SK_Constructor":"MI_VAT_Constructorr"
    }
                
    find_path = Path(parent_path,"Material")
    mat_path = None
    new_parent_path = parent_path
    check_parent_path = False
    for i in range(3):
        if not check_parent_path:
            check_parent_path = True
            if parent_path.parent.name.endswith(".json"):
                parent_path = parent_path.parent
                if parent_path.exists():
                    print("material folder found")
                    mat_path = parent_path
                    break
            if Path(parent_path,f"{obj_material}.json").exists():
                print("material folder found")
                mat_path = parent_path
                break
        print(f"Mat: {find_path}============")
        if find_path.is_dir():
            print("The folder exists in dir.")
            mat_path = find_path
            break
        else:
            print("folder not in dir")
            new_parent_path = new_parent_path.parent
            find_path = Path(new_parent_path,"Material")
    if not mat_path:
        search_file = list(Path(sf_asset_export_path,"Exports").rglob(f"{obj_material}.json"))
        if search_file:
            mat_path = search_file[0]
        else:
            print("No Material file found.")
            return None
    try:
        mat_file = Path(mat_path,f"{obj_material}.json")
        print(mat_file)
        with open(mat_file, 'r', encoding='utf-8') as f:
            m_data = json.load(f)
            #print(m_data)
    except Exception as e:
        print("Error opening material file: ",e)
        return None
    b_material = bpy.data.materials[obj_material]    
    b_material.node_tree.nodes.clear()
    textures = m_data.get('Textures')
    
    for f_mat in force_replace_mat:
        if f_mat == obj_material:
            obj_material = force_replace_mat[f_mat]
    
    if "Glass" in obj_material:
        glass_mat = bpy.data.materials.get("Glass_mat")
        ob.material_slots[index].material = glass_mat
        return None
    
    if textures:
        for tex in textures:
            if "TX2D_" in tex:
                fact_mat = bpy.data.materials.get("MI_Factory_01")
                ob.material_slots[index].material = fact_mat
                return None
    if any(force == obj_material for force in force_use_factory_01):# or "_Inst" in obj_material:
        fact_mat = bpy.data.materials.get("MI_Factory_01")
        ob.material_slots[index].material = fact_mat
    
    if textures:
        print("getting mat tex")
        nodes = b_material.node_tree.nodes
        links = b_material.node_tree.links
        output_node = nodes.new('ShaderNodeOutputMaterial')
        output_node.location.x = 400
        sf_shader_node = nodes.new('ShaderNodeGroup')
        if bpy.data.node_groups.get("SatisfactoryToBlenderShader"):
            sf_shader_node.node_tree = bpy.data.node_groups['SatisfactoryToBlenderShader']
        else:
            sf_shader_node.node_tree = bpy.data.node_groups['FallBack']
        sf_shader_node.location.x = 200
        links.new(sf_shader_node.outputs["Shader"], output_node.inputs["Surface"])
        
        pos = 0
        tex_set = set([textures[tex] for tex in textures])
        #print(tex_set)
        
        for tex in tex_set:
            print(tex)
            tex_dir = tex.replace("/Game", "Content").split('.')[0] + ".png"
            tex_file = Path(sf_asset_export_path,"FactoryGame",tex_dir)    
            print(tex_file)
            model_parent_path = mat_path.parent
            in_parent = os.fspath(tex_file).startswith(str(os.fspath(mat_path.parent)))
            print(os.fspath(tex_file).startswith(str(os.fspath(mat_path.parent))))   
            print(in_parent)
            print("---")
                
            print(tex_file.name.startswith("TX_"))
            print(tex_file.name.startswith("T_"))
            print(tex_file.name)
            if not tex_file.exists():
                print(f"Error: texture does not exist: {tex_file}")
                continue
            if not tex_file.name.startswith("TX_") and not tex_file.name.startswith("T_") and not any(screen in tex_file.name for screen in screen_type_mat):
                print(f"Skipping None 'TX_' and 'T_' textures: {tex_file}")
                continue
            
            if not in_parent:
                print(f"Skipping textures not in parent dir: {tex_file}")
                continue
            
            print("========================>")
            print(f"Getting {tex_file.name} texture")
            print("========================")
            try:
                b_texture = b_material.node_tree.nodes.new('ShaderNodeTexImage')
                x = -200
                y = 0-(pos*50)
                print(y)
                pos += 1
                b_texture.location = Vector((x,y))
                #b_texture.image = bpy.data.images.load(os.fspath(tex_file))
                print(os.fspath(tex_file))
                #print(bpy.data.images)
                img_list = [img.name for img in bpy.data.images]
                #print(img_list)
                print(tex_file)
                img = bpy.data.images.get(tex_file.name)
                if img:
                    print("img in bl")
                    b_texture.image = img
                else:
                    print("img not in bl")
                    b_texture.image = bpy.data.images.load(os.fspath(tex_file))
                print(b_texture.image.name)
                b_texture.hide = True
                for mt in mirrored_tex:
                    if mt in tex_file.name:
                        b_texture.image.extension = 'MIRROR'
                for t in rn_type_tex:
                    if t in tex_file.name:
                    #if '_N' in tex_file.name or 'Refl' in tex_file.name:
                        b_texture.image.colorspace_settings.name = 'Linear Rec.709'
                
                
                sf_tile = ""
                if "_N" in tex_file.name:
                    sf_tile = "Normal/Nor/N"
                
                if "_AO" in tex_file.name:
                    sf_tile = "AO/IDMask"
                    
                for rt in rough_type_tex:
                    if rt in tex_file.name:
                        sf_tile = "Relf/MREA"
                    if "MREA" in tex_file.name:
                        sf_shader_node.inputs[6].default_value = True
                for bc in color_type_tex:
                    if bc in tex_file.name:
                        sf_tile = "Color/BC/Albedo"
                
                if not sf_tile:
                    continue
                print(b_texture.outputs["Color"])
                print(sf_shader_node.inputs[sf_tile])
                links.new(b_texture.outputs["Color"], sf_shader_node.inputs[sf_tile])
            except Exception as e:
                print("Error loading texture: ",e)
                return None         

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
    
    sf_asset_export_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_export_path
    build_materials = bpy.context.scene.sf_importer_props.build_materials
    if build_materials:
        obj_materials = [slot.material.name for slot in ob.material_slots if slot.material]
        print(f"Materials on {ob.name}: {obj_materials}")
        if "Decal_Normal" in obj_materials:
            node_group = bpy.data.node_groups["Decal_Normal_Copy_Color"]
            mod = ob.modifiers.new(name="GeometryNodes", type="NODES")
            mod.node_group = node_group
            #set_geonode_input(mod, "Material", "Decal_Normal")
        for i,mat in enumerate(obj_materials):
            mat_results = get_materials(ob,mat,file,i,sf_asset_export_path)
    
    mark_as_asset = bpy.context.scene.sf_importer_props.mark_as_asset
    if mark_as_asset:
        col.asset_mark()
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

EXPORT_FILE_DIR = r"PATH-TO-FMODEL-EXPORTS"
BASE_FILE_DIR = r"F:\blenber\SF to blend\fmodel export\FactoryGame\Content\FactoryGame\Buildable"
EVENT_FILE_DIR = r"F:\blenber\SF to blend\fmodel export\FactoryGame\Content\FactoryGame\Events"
BUILD_TO_ASSET_DIR = r"F:\blenber\SF to blend\SF-2-Blender addon\satisfactory-to-blender\import models\buildable_to_asset.json"   

INTEGRATED_BUILD_LIST = [
    "ProductionIndicatorInstanced",
    "HubTerminal",
    "Integrate",
    "ElevatorCabin",
    "StorageBlueprint",
    "PipelineFlowIndicator"
]