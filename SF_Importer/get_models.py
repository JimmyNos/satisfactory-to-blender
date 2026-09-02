import math
from pickle import TRUE
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

def get_or_create_collection(name,parent_name = "",col_color = "NONE") -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    parent_col = bpy.data.collections.get(parent_name)
    if not col:
        col = bpy.data.collections.new(name)
        if col_color != "NONE":
            col.color_tag = col_color
        if not parent_name:
            bpy.context.scene.collection.children.link(col)
        else:
            parent_col.children.link(col)
            
    return col

def get_asset_collection() -> bpy.types.Collection:
    return get_or_create_collection('Assets',"COLOR_01")

def get_essential_collection() -> bpy.types.Collection:
    return get_or_create_collection('essentials')

def get_materials(ob,obj_material: str, file: Path,index:int,sf_asset_export_path:str,col):
    print("=================================>")
    print("Getting Matetrals")
    print("=================================<")
    parent_path = file.parent
    print(parent_path)
    exports_parent_path = str(parent_path).replace(sf_asset_export_path,sf_asset_export_path+"Exports")
    
    PRO_MATERIALS = [
        "MI_Factory_01", # base name
        "Decal_Color",
        "Decal_Normal",
        "DecalColor_Masked"
        #"Glass_Mat", # glass mat name
        #"Lights_Mat", # Lights mat name
    ]
    if any(pro in obj_material for pro in PRO_MATERIALS):
        return None
    
    rn_type_tex = [
        "_N",
        "Nor",
        "MREO",
        "Rough",
        "Relf",
        "Refl",
        "REFL",
        "RELF",
        "ORMA"
    ]
    
    nor_type_tex = [
        "_N",
        "Nor",
        "nor",
    ]
    
    rough_type_tex = [
        "MREO",
        "Rough",
        "Refl",
        "Relf",
        "REFL",
        "RELF",
        "ORMA"
    ]
    
    color_type_tex = [
        "BC",
        "BaseColor",
        "Alb"
        #,"Pattern_02"
    ]
    
    extra_type_tex = [
        "Pattern_02",
        "POS",
        "QUAT",
        "TX_PowerLineLights_MASKS"
    ]
    
    exclude_tex = [
        "T_Water_Normal_Large"
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
        "MI_GeneratorNuclear",
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
        "MI_Truckstation",
        "MI_VTX_ANIM_WaterPump_01",
        "MI_VA_CoalGenerator_01"
    ]
    
    force_get_texture = [
        "Light_Vertical_Blinking_Mask"
    ]
    
    extra_uv = [
        "EXTRAUV0"
    ]
    
    mirrored_tex = [ # TODO change to textures
        "SM_BigDoor_01",
        "MI_Foundation_FicsitSet_",
        "MI_SteelWall_",
        "MI_Door_01",
        "MI_WallSetConcrete_",
        "MI_Foundation_Concrete",
        "MI_Ramp_Concrete",
        "MI_GripMetal_Ramp",
        "MI_GripMetal_RampCorner",
        "MI_GripMetal_Foundation",
        "MMU_BigDoorAnimation",
        "MI_AsphaltFoundation",
        "MI_AsphaltRamp",
        "MI_Ramp_PolishedConcrete",
        "MI_Foundation_PolishedConcrete"
    ]
    
    uses_alpha = [
        "HubDecal_Masked",
        "HubFicsmasDecal_Masked",
        "Placeholder_Garland",
        "MMU_LightLine",
        "MI_FicsmasTree_Branches_01"
    ]
    
    con_mat_remap = {
        "Concrete":[
            "MI_Foundation_Concrete",
            "MI_Ramp_Concrete",
            ],
        "Asphalt":[
            "MI_AsphaltFoundation",
            "MI_AsphaltRamp",
            ],
        "Polished":[
            "MI_Foundation_PolishedConcrete",
            "MI_Ramp_PolishedConcrete",
            ],
        #"Ficsit":[
        #    "MI_Foundation_FicsitSet_01",
        #    "MI_Foundation_FicsitSet_Ramp_01",
        #    "MI_Foundation_FicsitSet_CornerRamp_01",
        #    ],
        #"Grip":[
        #    "MI_GripMetal_Foundation",
        #    "MI_GripMetal_Ramp",
        #    "MI_GripMetal_RampCorner",
        #    ],
        #"Metal":[
        #    "MI_GripMetal_Foundation",
        #    "MI_GripMetal_Ramp",
        #    "MI_GripMetal_RampCorner",
        #    ]
        
        
        #"MI_Foundation_Concrete":{
        #    "Asphalt":"MI_AsphaltFoundation",
        #    "Polished":"MI_Foundation_PolishedConcrete"
        #},
        #"MI_Ramp_Concrete":{
        #    "Asphalt":"MI_AsphaltRamp",
        #    "Polished":"MI_Ramp_PolishedConcrete"
        #},
        #"MI_Foundation_FicsitSet_01":{
        #    "Grip":"MI_GripMetal_Foundation",
        #    "Metal":"MI_GripMetal_Foundation",
        #},
        #"MI_Foundation_FicsitSet_CornerRamp_01":{
        #    "Grip":"MI_GripMetal_RampCorner",
        #    "Metal":"MI_GripMetal_RampCorner",
        #},
        #"MI_Foundation_FicsitSet_Ramp_01":{
        #    "Grip":"MI_GripMetal_Ramp",
        #    "Metal":"MI_GripMetal_Ramp",
        #}
    }
    fic_mat_remap = {
        "Ficsit":[
            "MI_Foundation_FicsitSet_01",
            "MI_Foundation_FicsitSet_Ramp_01",
            "MI_Foundation_FicsitSet_CornerRamp_01",
            ],
        "Grip":[
            "MI_GripMetal_Foundation",
            "MI_GripMetal_Ramp",
            "MI_GripMetal_RampCorner",
            ],
        "Metal":[
            "MI_GripMetal_Foundation",
            "MI_GripMetal_Ramp",
            "MI_GripMetal_RampCorner",
            ]
    }
    
    no_gb_mat = [
        "MI_BlueprintDesigner_Foundations_01",
        "MI_BlueprintDesigner_Computer_01",
        "MI_MamMycelia",
        "MI_Book_",
        "MI_MamNutrients",
        "MI_ConveyorFloorHole_01",
        "MI_HubPots",
        "MI_PictureDiploma",
        "MI_ToiletPoster_01",
        "MI_Toothbrush",
        "MI_HubMirror",
        "MI_ToiletBag",
        "MI_LunchTray",
        "MI_OstHyvel",
        "MI_Microwave",
        "MI_Candle",
        "MI_socks",
        "MI_Snus",
        "MI_RubiksCube",
        "MI_Picture_01",
        "MI_Alpaca",
        "MI_Meseekbox",
        "MI_HubSign",
        "MI_Embroidery",
        "MI_PostCard_01",
        "MI_HubComputer",
        "MI_GoldenJoystick",
        "MI_Pencils_01",
        "MI_Picture_02",
        "MM_LavaLamp",
        "MI_Matches",
        "MI_Halmbock",
        "MI_FicsmasCandle",
        "MI_FicsmasBlanket",
        "MI_SnowGlobe",
        "MI_Glogg",
        "MI_GingerBreadCookies",
        "MI_Orange",
        "MI_Bowl",
        "MI_FicsmasCandle",
        "MI_SantaStatue"
    ]
    
    mra_mat = [
        "MI_CPWall",
        "MI_FactoryBaked_Workshop_01",
        "MI_Foundation_LOD0",
        "JumpingStilts02_Inst",
        "parachute_01_Inst",
        "MI_SnowFicsmas_01"
    ]
    
    emision_type_mats = [
        "MI_PriorityLightsLift_01"
    ]
    
    force_replace_mat = {
        #"MI_SK_Constructor":"MI_VAT_Constructorr",
        "MI_Tack_01_NoDeform":"MI_Tack_01",
        "MM_ShutterGate_Inst":"MI_HyperTubeStart_01",
        "HubDecal_Opaque":"HubDecal_Masked",
        "MI_Pipe_Static":"MI_Pipe",
        "MI_HyperTube_Static":"MI_HyperTube"
    }
    
    search_mat = {
        "PipelineMK2":"MI_PipeMK2",
        "Pipeline":"MI_Pipe"
        }
    
    light_type_mat = [
        "MI_PriorityLights"
    ]
    
    beam_mats = [
        "MI_Beams_01",
        "MI_Beam_04",
        "MI_Beam_01",
        "MI_Beam_07",
        "MI_SM_BeamCable_02",
        "MI_SM_BeamCable_01"
    ]
    
    find_path = Path(parent_path,"Material")
    find_path_s = Path(parent_path,"Materials")
    find_path_pl = Path(find_path,"Placeholder") # TODO hub materials
    mat_path = None
    mat_exports_path = None
    new_parent_path = parent_path
    check_parent_path = False
    fact_mat = bpy.data.materials.get("MI_Factory_01")
    is_force = any(obj_material == force for force in force_use_factory_01)
    
    if is_force:# or "_Inst" in obj_material:
        if "SM_Blender_01" != ob.name:
            ob.material_slots[index].material = fact_mat
            return None
    
    for f_mat in force_replace_mat:
        if f_mat == obj_material:
            obj_material = force_replace_mat[f_mat]
            replace_mat = bpy.data.materials.get(obj_material)
            if not replace_mat:
                replace_mat = bpy.data.materials.new(obj_material)
            ob.material_slots[index].material = replace_mat
            
    #opa_name = ""
    #if "HubDecal_Opaque" in obj_material:
    #    opa_name = obj_material
    #    no_opa_name = "HubDecal_Masked"
    #    replace_mat = bpy.data.materials.get(no_opa_name)
    #    if not replace_mat:
    #        replace_mat = bpy.data.materials.new(no_opa_name)
    #    ob.material_slots[index].material = replace_mat
    #    
    #    material_dup = ob.material_slots[index].material.copy()
    #    ob.material_slots[index].material = material_dup
    #    ob.material_slots[index].material.name = obj_material
    
    for s_mat in search_mat:
        if s_mat == col.name:
            new_mat = search_mat[s_mat]
            ob.data = ob.data.copy()
            material_dup = ob.material_slots[index].material.copy()
            ob.material_slots[index].material = material_dup
            replace_mat = bpy.data.materials.get(new_mat)
            if not replace_mat:
                replace_mat = bpy.data.materials.new(new_mat)
            ob.material_slots[index].material = replace_mat
            obj_material = new_mat
    
    foundation_path = "Foundation" in list(parent_path.parts)
    if "Concrete" in col.name and foundation_path:# and not "Wall" in col.name and not "Piller" in col.name and not "Barrier" in col.name:
        mat_re = con_mat_remap["Concrete"]
        if "Ramp" in col.name and not "DCorner" in col.name and not "DownCorner" in col.name:
            obj_material_dup = mat_re[1]
        else:
            obj_material_dup = mat_re[0]
        ob.data = ob.data.copy()
        material_dup = ob.material_slots[index].material.copy()
        ob.material_slots[index].material = material_dup
        replace_mat = bpy.data.materials.get(obj_material_dup)
        if not replace_mat:
            replace_mat = bpy.data.materials.new(obj_material_dup)
        ob.material_slots[index].material = replace_mat
        obj_material = obj_material_dup
    if "Asphalt" in col.name:
        mat_re = con_mat_remap["Asphalt"]
        if "Ramp" in col.name and not "DCorner" in col.name and not "DownCorner" in col.name:
            obj_material_dup = mat_re[1]
        else:
            obj_material_dup = mat_re[0]
        ob.data = ob.data.copy()
        material_dup = ob.material_slots[index].material.copy()
        ob.material_slots[index].material = material_dup
        replace_mat = bpy.data.materials.get(obj_material_dup)
        if not replace_mat:
            replace_mat = bpy.data.materials.new(obj_material_dup)
        ob.material_slots[index].material = replace_mat
        obj_material = obj_material_dup
    if "Polished" in col.name:
        mat_re = con_mat_remap["Polished"]
        if "Ramp" in col.name and not "DCorner" in col.name and not "DownCorner" in col.name:
            obj_material_dup = mat_re[1]
        else:
            obj_material_dup = mat_re[0]
        ob.data = ob.data.copy()
        material_dup = ob.material_slots[index].material.copy()
        ob.material_slots[index].material = material_dup
        replace_mat = bpy.data.materials.get(obj_material_dup)
        if not replace_mat:
            replace_mat = bpy.data.materials.new(obj_material_dup)
        ob.material_slots[index].material = replace_mat
        obj_material = obj_material_dup
    
    if "Ficsit" in col.name:
        mat_re = fic_mat_remap["Ficsit"]
        if "Ramp" in col.name or "Stair" in col.name:
            obj_material_dup = mat_re[1]
        else:
            obj_material_dup = mat_re[0]
        
        ob.data = ob.data.copy()
        material_dup = ob.material_slots[index].material.copy()
        ob.material_slots[index].material = material_dup
        replace_mat = bpy.data.materials.get(obj_material_dup)
        if not replace_mat:
            replace_mat = bpy.data.materials.new(obj_material_dup)
        ob.material_slots[index].material = replace_mat
        obj_material = obj_material_dup
    
    if "Grip" in col.name or "Metal" in col.name and foundation_path:# and not "Wall" in col.name and not "Piller" in col.name and not "Barrier" in col.name:
        mat_re = fic_mat_remap["Grip"]
        if "Corner" in col.name and "Ramp" in col.name and not "DC" in col.name and not "DownCorner" in col.name:
            obj_material_dup = mat_re[2]
        elif "Ramp" in col.name and not "DC" in col.name and not "DownCorner" in col.name:# or "Stair" in col.name:
            obj_material_dup = mat_re[1]
        else:
            obj_material_dup = mat_re[0]
    
        ob.data = ob.data.copy()
        material_dup = ob.material_slots[index].material.copy()
        ob.material_slots[index].material = material_dup
        replace_mat = bpy.data.materials.get(obj_material_dup)
        if not replace_mat:
            replace_mat = bpy.data.materials.new(obj_material_dup)
        ob.material_slots[index].material = replace_mat
        obj_material = obj_material_dup
            
    if "Glass" in obj_material or "MI_HadronEffect_01" in obj_material or "MM_Window_CC" in obj_material or "MI_BlenderPitcher" in obj_material:
        glass_mat = bpy.data.materials.get("Glass_mat")
        ob.material_slots[index].material = glass_mat
        return None

    
    is_hub = False
    search_file = list(Path(sf_asset_export_path,"Exports").rglob(f"{obj_material}.json"))
    if search_file:
        if len(search_file) > 1:
            if "MI_Door_01" in obj_material:
                search_sort = search_file
                if "Door_Basic_01" in search_file[0].parent.name:
                    search_sort = [search_file[1],search_file[0]]
                    
                if "SM_Door_Basic_01" in ob.name:
                    mat_path = search_sort[1]
                elif "SM_InsetDoorway_01" in ob.name:
                    mat_path = search_sort[0]
                    obj_material_dup = "MI_Doorway"
                    material_dup = ob.material_slots[index].material.copy()
                    ob.material_slots[index].material = material_dup
                    replace_mat = bpy.data.materials.get(obj_material_dup)
                    if not replace_mat:
                        replace_mat = bpy.data.materials.new(obj_material_dup)
                    ob.material_slots[index].material = replace_mat
                    obj_material = obj_material_dup
        else:
            mat_path = search_file[0]
    
    
    # search Exports path if not found in mesh path 
    if not mat_path: # TODO
        return None
    
    # Get Material file
    try:
        mat_file = mat_path
        #if mat_path.name.endswith(".json"):
        #    mat_file = mat_path
        #else:
        #    mat_file = Path(mat_path,f"{obj_material}.json")
        print(mat_file)
        with open(mat_file, 'r', encoding='utf-8') as f:
            m_data = json.load(f)
            
    except Exception as e:
        print("⚠️Error opening material file: ",e)
        return None

    
    #if textures:
    #    for tex in textures:
    #        if "TX2D_" in tex:
    #            ob.material_slots[index].material = fact_mat
    #            return None
    
    textures = [] # type: list[dict[str,str]] 
    switch_parameters = [] # type: list[dict[str,str]] 
    vec_parameters = [] # type: list[dict[str,dict]] 
    for item in m_data:
        is_tpv = False
        if item.get("Properties"):
            props = item.get("Properties")
            if props.get("Parent"):
                # default to Factory_01 material if TX2D_ textures found
                if "MI_Factory_Base" in props["Parent"]["ObjectName"]: 
                    ob.material_slots[index].material = fact_mat
                    return None
            
            if props.get("TextureParameterValues"):
                is_tpv = True
                for tex in props["TextureParameterValues"]:
                    skip_tex = False
                    for ext in exclude_tex:
                        if ext in tex["ParameterValue"]["ObjectPath"][6:].split('.')[0]:
                            skip_tex = True
                            break
                    if skip_tex:
                        print(f"skipping {tex["ParameterValue"]["ObjectPath"][6:].split('.')[0]}")
                        continue
                    textures.append(
                        {tex["ParameterInfo"]["Name"]:tex["ParameterValue"]["ObjectPath"][6:].split('.')[0]}
                    )
                if props.get("TextureStreamingData"):
                    for tsd in props["TextureStreamingData"]:
                        skip_tex = False
                        for ext in exclude_tex:
                            if ext in tsd["TextureName"]:
                                skip_tex = True
                                break
                        if skip_tex:
                            print(f"skipping {tsd["TextureName"]}")
                            continue
                        continue
                        if tsd["TextureName"].startswith("TX_") or tsd["TextureName"].startswith("T_"):
                            for t in nor_type_tex:
                                if t in tsd["TextureName"]:
                                    normal_name = tsd["TextureName"]
                                    has_normal = False
                                    alb_tex = ""
                                    for t in textures:
                                        for k in t:
                                            if k.startswith('N'):
                                                has_normal = True
                                            if k.startswith('A'):
                                                alb_tex = t[k]
                                    if not has_normal and alb_tex:    
                                        alb_parts = alb_tex.split('/')
                                        alb_parts[-1] = normal_name
                                        mat_tex = '/'.join(alb_parts)
                                        textures.append(
                                            {"Normal":mat_tex}
                                        )
            
            if props.get("TextureStreamingData") and len(textures) <= 1:# not props.get("TextureParameterValues"):
                found_tex_type = ""
                if textures:
                    found_tex_type = list(textures[0].keys())[0]
                    print(found_tex_type)
                for tsd in props["TextureStreamingData"]:
                    skip_tex = False
                    for ext in exclude_tex:
                        if ext in tsd["TextureName"]:
                            skip_tex = True
                            break
                    if skip_tex:
                        print(f"skipping {tsd["TextureName"]}")
                        continue
                    for t in nor_type_tex:
                        if t in tsd["TextureName"] and "Normal" not in found_tex_type:
                            tex_name = tsd["TextureName"]
                            search_tex_path = mat_path.parent.parent
                            search_tex = list(search_tex_path.rglob(f"{tex_name}.png"))
                            if search_tex:
                                mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                textures.append(
                                    {"Normal":mat_tex.split('.')[0]}
                                )
                                break
                            else:
                                print(f"{tex_name} not found trying wider search")
                                search_tex = list(Path(sf_asset_export_path).rglob(f"{tex_name}.png"))
                                if search_tex:
                                    mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                    textures.append(
                                        {"Normal":mat_tex.split('.')[0]}
                                    )
                                    break
                    if "_AO" in tsd["TextureName"] and "AOMasks" not in found_tex_type:
                        tex_name = tsd["TextureName"]
                        search_tex_path = mat_path.parent.parent
                        search_tex = list(search_tex_path.rglob(f"{tex_name}.png"))
                        if search_tex:
                            mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                            textures.append(
                                {"AOMasks":mat_tex.split('.')[0]}
                            )
                        else:
                            print(f"{tex_name} not found trying wider search")
                            search_tex = list(Path(sf_asset_export_path).rglob(f"{tex_name}.png"))
                            if search_tex:
                                mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                textures.append(
                                    {"Normal":mat_tex.split('.')[0]}
                                )
                                break
                    for t in color_type_tex:
                        if t in tsd["TextureName"] and "Albedo" not in found_tex_type:
                            tex_name = tsd["TextureName"]
                            search_tex_path = mat_path.parent.parent
                            search_tex = list(search_tex_path.rglob(f"{tex_name}.png"))
                            if search_tex:
                                mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                textures.append(
                                    {"Albedo":mat_tex.split('.')[0]}
                                )
                                break
                            else:
                                print(f"{tex_name} not found trying wider search")
                                search_tex = list(Path(sf_asset_export_path).rglob(f"{tex_name}.png"))
                                if search_tex:
                                    mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                    textures.append(
                                        {"Normal":mat_tex.split('.')[0]}
                                    )
                                    break
                    for t in rough_type_tex:
                        if t in tsd["TextureName"] and "ReflectionMap" not in found_tex_type:
                            tex_name = tsd["TextureName"]
                            search_tex_path = mat_path.parent.parent
                            search_tex = list(search_tex_path.rglob(f"{tex_name}.png"))
                            if search_tex:
                                mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                textures.append(
                                    {"ReflectionMap":mat_tex.split('.')[0]}
                                )
                                break
                            else:
                                print(f"{tex_name} not found trying wider search")
                                search_tex = list(Path(sf_asset_export_path).rglob(f"{tex_name}.png"))
                                if search_tex:
                                    mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                    textures.append(
                                        {"Normal":mat_tex.split('.')[0]}
                                    )
                                    break
                    for t in extra_type_tex:
                        if t in tsd["TextureName"]:
                            tex_name = tsd["TextureName"]
                            search_tex_path = mat_path.parent.parent
                            search_tex = list(search_tex_path.rglob(f"{tex_name}.png"))
                            if search_tex:
                                mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                textures.append(
                                    {"Extra":mat_tex.split('.')[0]}
                                )
                            else:
                                print(f"{tex_name} not found trying wider search")
                                search_tex = list(Path(sf_asset_export_path).rglob(f"{tex_name}.png"))
                                if search_tex:
                                    mat_tex = str(search_tex[0]).replace("\\Exports\\","\\")
                                    textures.append(
                                        {"Normal":mat_tex.split('.')[0]}
                                    )
                                    break
            
            if props.get("StaticParametersRuntime"):
                for ssp in props["StaticParametersRuntime"]["StaticSwitchParameters"]:
                    switch_parameters.append(
                        {ssp["ParameterInfo"]["Name"]:ssp["Value"]}
                    )
            if props.get("VectorParameterValues"):
                for vpv in props["VectorParameterValues"]:
                    vec_parameters.append(
                        {vpv["ParameterInfo"]["Name"]:vpv["ParameterValue"]}
                    )
        
        if item.get("ReferencedTextures") and not is_tpv:
            for ref_tex in item["ReferencedTextures"]:
                for t in color_type_tex:
                    if t in ref_tex.get("ObjectName"):
                        textures.append(
                            {"Albedo":ref_tex["ObjectPath"][6:].split('.')[0]}
                        )
                for t in rough_type_tex:
                    if t in ref_tex.get("ObjectName"):
                        textures.append(
                            {"ReflectionMap":ref_tex["ObjectPath"][6:].split('.')[0]}
                        )
                if "_N" in ref_tex.get("ObjectName"):
                    textures.append(
                        {"Normal":ref_tex["ObjectPath"][6:].split('.')[0]}
                    )
                if "_AO" in ref_tex.get("ObjectName"):
                    textures.append(
                        {"AOMasks":ref_tex["ObjectPath"][6:].split('.')[0]}
                    )
    print(f"Found {len(textures)} textures: {textures}")
    b_material = bpy.data.materials.get(obj_material)
    if not b_material:
        print(f"Material not found: {obj_material}")
        return None
    if not b_material.use_nodes:
        b_material.use_nodes = True
    if not b_material.node_tree:
        b_material.use_nodes = True
    b_material.node_tree.nodes.clear()
    nodes = b_material.node_tree.nodes
    links = b_material.node_tree.links
    output_node = nodes.new('ShaderNodeOutputMaterial')
    output_node.location.x = 400
    
    if "MI_Cyberwagon_Window" in obj_material:
        glossy_node = nodes.new(type="ShaderNodeBsdfGlossy")
        glossy_node.location.x = 200
        glossy_node.inputs["Roughness"].default_value = 0.01

        links.new(glossy_node.outputs["BSDF"], output_node.inputs["Surface"])
        return None
    
    for l_mat in light_type_mat:
        if l_mat in obj_material:
            light_shader_node = nodes.new('ShaderNodeGroup')
            if bpy.data.node_groups.get("Light_shader"):
                light_shader_node.node_tree = bpy.data.node_groups['Light_shader']
            else:
                light_shader_node.node_tree = bpy.data.node_groups['FallBack']
            light_shader_node.location.x = 200
            links.new(light_shader_node.outputs["Shader"], output_node.inputs["Surface"])
            return None
    
    if "MI_ConveyorBelt_PowerStrip_MK6_01" == obj_material:
        power_strip_shader_node = nodes.new('ShaderNodeGroup')
        if bpy.data.node_groups.get("MI_ConveyorBelt_PowerStrip_01"):
            power_strip_shader_node.node_tree = bpy.data.node_groups['MI_ConveyorBelt_PowerStrip_01']
        else:
            power_strip_shader_node.node_tree = bpy.data.node_groups['FallBack']
        power_strip_shader_node.location.x = 200
        links.new(power_strip_shader_node.outputs["Shader"], output_node.inputs["Surface"])
        return None
    
    # Start Textures logic
    if textures:
        print("getting mat tex")
        sf_shader_node = nodes.new('ShaderNodeGroup')
        if bpy.data.node_groups.get("SatisfactoryToBlenderShader"):
            sf_shader_node.node_tree = bpy.data.node_groups['SatisfactoryToBlenderShader']
        else:
            sf_shader_node.node_tree = bpy.data.node_groups['FallBack']
        sf_shader_node.location.x = 200
        links.new(sf_shader_node.outputs["Shader"], output_node.inputs["Surface"])
        if any(mat == obj_material for mat in no_gb_mat):
            sf_shader_node.inputs["AO no GB packed?"].default_value = True
        if "SM_Door_Basic_01" in ob.name:
            sf_shader_node.inputs["Swap AO Channels?"].default_value = True
            sf_shader_node.inputs["Emission colour?"].default_value = True
        
        if "SM_BigDoor_01" in ob.name:
            sf_shader_node.inputs["Emission colour?"].default_value = True
            
            
        use_beam_logic = False
        if any(mat in obj_material for mat in beam_mats):
            if bpy.data.node_groups.get("Beam_Logic"):
                beam_logic_node = nodes.new('ShaderNodeGroup')
                beam_logic_node.node_tree = bpy.data.node_groups['Beam_Logic']
                beam_logic_node.location.x = -400
                use_beam_logic = True
        #if any(mat == obj_material for mat in mra_mat):
        #    sf_shader_node.inputs["MRA?"].default_value = True
        has_cbp = False # CanBePainted
        #for sp in switch_parameters:
        #    if not sp.get("CanBePainted"):
        #        has_cbp = True
        for mra in mra_mat:
            if mra in obj_material:
                has_cbp = True
        sf_shader_node.inputs["MRA?"].default_value = has_cbp
        sf_shader_node.inputs["No Paint Finish?"].default_value = has_cbp
        
        for par in vec_parameters:
            light_color_data = par.get("Emissive Color")
            if light_color_data:
                r = light_color_data["R"]
                g = light_color_data["G"]
                b = light_color_data["B"]
                sf_shader_node.inputs["Emission colour?"].default_value = True
                sf_shader_node.inputs["Emission Colour"].default_value = (r, g, b, 1)
        
        pos = 0
        #tex_set = set([textures[tex] for tex in textures])
        #print(tex_set)
        
        for tex in textures:
            print(tex) 
            tex_type = ""
            tex_path = ""
            for tt,tp in tex.items(): #should only have one item {texture type: texture path}
                tex_type = tt # type: str
                tex_path = tp # type: str
                
            if "MI_WallSetConcrete_8x1" in obj_material:
                if "TX_WallSetConcrete_8x1_AOMasks" in tex_path:
                    continue
            
            exports_path = Path(sf_asset_export_path,"FactoryGame","Content")
            print(exports_path)
            tex_file = Path(exports_path,f"{tex_path}.png")    
            print(tex_file)
            model_parent_path = mat_path.parent
            print("---")
                
            print(tex_file.name.startswith("TX_"))
            print(tex_file.name.startswith("T_"))
            print(tex_file.name)
            if not tex_file.exists():
                print(f"Error: texture does not exist: {tex_file}")
                continue
            #if not tex_file.name.startswith("TX_") and not tex_file.name.startswith("T_") and not any(screen in tex_file.name for screen in screen_type_mat):
            #    print(f"Skipping None 'TX_' and 'T_' textures: {tex_file}")
            #    continue
            
            print("========================")
            print(f"Getting {tex_file} texture")
            print("========================")
            try:
                b_texture = b_material.node_tree.nodes.new('ShaderNodeTexImage')
                x = -200
                y = 0-(pos*50)
                print(y)
                pos += 1
                b_texture.location = Vector((x,y))
                #b_texture.image = bpy.data.images.load(os.fspath(tex_file))
                #print(bpy.data.images)
                #img_list = [img.name for img in bpy.data.images]
                #print(img_list)
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
                    if mt in obj_material:#tex_file.name:
                        if "TX_Stencils" not in tex_file.name:
                            b_texture.extension = 'MIRROR'
                for t in rn_type_tex:
                    if t in tex_type or t in tex_file.name:
                    #if '_N' in tex_file.name or 'Refl' in tex_file.name:
                        b_texture.image.colorspace_settings.name = 'Linear Rec.709'
                if "_ORMA" in tex_file.name:
                    sf_shader_node.inputs["ORMA?"].default_value = True
                for ua in uses_alpha:
                    if ua in b_material.name:
                        sf_shader_node.inputs["No AO?"].default_value = False
                        sf_shader_node.inputs["Alpha?"].default_value = True
                        sf_shader_node.inputs["No Paint Finish?"].default_value = True
                        if "TX_HubDecal_BC" in tex_file.name:
                            links.new(b_texture.outputs["Alpha"], sf_shader_node.inputs["Albedo Alpha"])
                            
                if use_beam_logic:
                    links.new(beam_logic_node.outputs["Vector"], b_texture.inputs["Vector"])
                        
                
                tx_type = ""
                tx_type_a = ""
                
                if "_N" in tex_file.name or "N" in tex_type:
                    tx_type = "Normal/Nor/N"
                if "_AO" in tex_file.name or "AO" in tex_type:
                    tx_type = "AO/IDMask"
                    sf_shader_node.inputs["No AO?"].default_value = False
                for rt in rough_type_tex:
                    if rt in tex_file.name or rt in tex_type:
                        tx_type = "Relf/MREA"
                        tx_type_a = tx_type+" Alpha"
                        b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                    if "_MREA" in tex_file.name:
                        sf_shader_node.inputs["Relf or MREA?"].default_value = True
                for bc in color_type_tex:
                    if bc in tex_file.name or bc in tex_type:
                        tx_type = "Color/BC/Albedo"
                        tx_type_a = "Albedo Alpha"
                        b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                
                if not tx_type:
                    continue
                print(b_texture.outputs["Color"])
                print(sf_shader_node.inputs[tx_type])
                if "PolishedConcrete" in tex_file.name and tx_type == "Relf/MREA":
                    rough_multi_node = nodes.new('ShaderNodeGroup')
                    rough_multi_node.node_tree = bpy.data.node_groups['Rough_Multiplier']
                    rough_multi_node.location.x = 200
                    sf_shader_node.location.x = 400
                    output_node.location.x = 600
                    links.new(b_texture.outputs["Color"], rough_multi_node.inputs["Color"])
                    links.new(rough_multi_node.outputs["Color"], sf_shader_node.inputs[tx_type])
                else:
                    links.new(b_texture.outputs["Color"], sf_shader_node.inputs[tx_type])
                if tx_type_a:
                    links.new(b_texture.outputs["Alpha"], sf_shader_node.inputs[tx_type_a])
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
            #obj_data_duplicate = ob.data.copy()
            #obj_duplicate.data = obj_data_duplicate
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
            if not "Props" in str(file):
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
    print(pos)
    print(asset)
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
        
    base_color = "COLOR_01"
    type_color = "COLOR_02"
    sub_color = "COLOR_03"
    sc_col = bpy.context.scene.collection
    as_col = get_asset_collection()
    get_or_create_collection("Utility",base_color)
    conveyor_lifts_col = get_or_create_collection("ConveyorLifts","Utility",type_color)
    get_or_create_collection("Factory","Assets",type_color)
    get_or_create_collection("Building","Assets",type_color)
    get_or_create_collection("Equipment","Assets",type_color)
    get_or_create_collection("Resource","Assets",type_color)
    lift_parts_col = get_or_create_collection("LiftParts","ConveyorLifts",sub_color)
    lifts_col = get_or_create_collection("Lifts","ConveyorLifts",sub_color)
    conveyor_belts_col = get_or_create_collection("ConveyorBelts","Utility",type_color)
    conveyor_belts_col.hide_viewport = True
    conveyor_lifts_col.hide_viewport = True
    
    if ob_sk_mesh != None and ob.type == 'ARMATURE':
        ob.data.display_type = 'STICK'
        
    if sc_col in ob.users_collection:
        bpy.context.scene.collection.objects.unlink(ob) 
    if ob_sk_mesh != None and sc_col in ob_sk_mesh.users_collection:
        bpy.context.scene.collection.objects.unlink(ob_sk_mesh) 
    
    if any(build in buildable_name for build in INTEGRATED_BUILD_LIST):
        col = get_or_create_collection(buildable_name,"Utility",type_color)
    else:
        if "Building" in os.fspath(file) or "Prototype" in os.fspath(file):
            col = get_or_create_collection(buildable_name,"Building",sub_color)
        elif "Equipment" in os.fspath(file):
            col = get_or_create_collection(buildable_name,"Equipment",sub_color)
        elif "Resource" in os.fspath(file) and "Equipment" not in os.fspath(file) and "Sink" not in os.fspath(file):
            col = get_or_create_collection(buildable_name,"Resource",sub_color)
        else:
            col = get_or_create_collection(buildable_name,"Factory",sub_color)
        
        
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
        stg_col = get_or_create_collection("TradingpostStages",buildable_name,sub_color)
        sk_col = get_or_create_collection("SK_Tradingpost",buildable_name,sub_color)
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
        ob_pros = ob
        col_pros = col
        if ob_sk_mesh:
            ob_pros = ob_sk_mesh
            
        obj_materials = [slot.material.name for slot in ob_pros.material_slots if slot.material]
        print(f"Materials on {ob_pros.name}: {obj_materials}")
            
        if "Decal_Normal" in obj_materials:
            node_group = bpy.data.node_groups["Decal_Normal_Copy_Color"]
            mod = ob_pros.modifiers.new(name="GeometryNodes", type="NODES")
            mod.node_group = node_group
            #set_geonode_input(mod, "Material", "Decal_Normal")
        for i,mat in enumerate(obj_materials):
            mat_results = get_materials(ob_pros,mat,file,i,sf_asset_export_path,col_pros)
            if mat_results == None:
                print(f"got {mat} material for {ob_pros}")
            #time.sleep(0.2)
    
    #mark_as_asset = bpy.context.scene.sf_importer_props.mark_as_asset
    #if mark_as_asset:
    #    col.asset_mark()
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