import json
import math
import os
from pathlib import Path
import random
from typing import Any, List, Tuple
import bpy
import time
from mathutils import Quaternion,Vector
import sys

from PIL import Image

def get_materials(obj_material: str = "",sf_asset_export_path:str = ""):
    print("=================================")
    print("Getting Materials")
    print("=================================")
    
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
        "nor",
        "MREO",
        "Rough",
        "Relf",
        "Refl",
        "REFL",
        "RELF",
        "ORMA",
        "HRA"
    ]
    
    nor_type_tex = [
        "_N",
        "Nor",
        "nor",
    ]
    
    rough_type_tex = [
        "MREO",
        "MREA",
        "Rough",
        "Refl",
        "Relf",
        "REFL",
        "RELF",
        "ORMA",
        "HRA"
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
        "T_Water_Normal_Large",
        "Default",
        "PigmentMap",
        "Cell_Bombing_Noise_basecolor",
        "NoizesBig",
        "Mask_Factory_02",
        "NoiseStorm",
        "T_WeatherNoise",
        "Far"
    ]
    
    ao_type_tex = [
        "_AO",
        #"",
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
        "MI_FicsmasTree_Branches_01",
        "DioTree_LeafMap"
    ]
    
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
    
    emission_type_mats = [
        "MI_PriorityLightsLift_01"
    ]
    
    force_replace_mat = {
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
    
    use_tiling = {
        "Grass_RedJungle":"Top Vector",
        "Grass_01":"Top Vector",
        "Sand":"Top Vector",
        "Moss":"Top Vector",
        "Puddles":"Top Vector",
        "Soil":"Top Vector",
        "Gravel":"Top Vector",
        "CliffRock":"Vector",
        "DesertRock":"Vector",
        "Cliff_Sediment_Alb":"Vector",
        "TX_DesertRock_Cracked_01":"Vector",
        "DesertRock_Rough_01":"Vector",
        "FlatRock":"Vector",
        "Arc_Rock":"Vector",
        "Arc_Inside":"Vector",
        "OriginStaligtite":"Vector",
        "Cliff_Detail_Alb":"Vector",
        "Plateau1and3":"Vector",
        "TX_TitanTree_TilingBark_N":"Vector",
        "SeaRock_Detail_Nor":"Vector",
    }
    
    use_tiling_group = [
        "Grass_RedJungle",
        "Grass_01",
        "Sand",
        "Moss",
        "Puddles",
        "Soil",
        "Gravel",
        "Cliff",
        "DesertRock",
        "Cliff_Sediment_Alb",
        "DesertRock_Rough_01",
        "FlatRock",
        "Arc_Rock",
        "Arc_Inside",
        "SmallShell_Inst",
        "CaveFloor_Inst",
        "OriginStaligtite",
        "Cliff_Detail_Alb",
        "Plateau1and3",
        "MI_Bigshell_01",
        "MI_TitanTree_01",
        "MI_SmallShell_Desert",
    ]
    
    detail_normal_tex = [
        "TX_DesertRock_Cracked_01_normal",
        "TX_DesertRock_Rough_01_normal",
        "TX_CliffRock_A_2x2_1K_normal",
        "Cliff_Sediment_Nor",
        "CliffSediment_Nor",
        #"TX_Arc_Rock_N",
        "TX_Arc_Inside_N",
        "T_Detail_Rocky_N",
        "SeaRock_Detail_Nor",
        "Cliff_Nor_03",
        "lambert1_Normal_DirectX"
    ]
    
    detail_tex = [
        "Cliff_Sediment_Alb",
        "TX_FlatRock_01_Alb"
    ]
    
    no_a_orma_mats = [
        "_Bark",
        "FieldFlower",
        "SnailBottom",
        "Trunk",
        "MI_TitanTreeMushrooms_01",
        "ubkmehzya"
    ]
    
    parameters = {
        "color tint": [
            {
                "R":1.0,
                "G":1.0,
                "B":1.0
            },
            "BC Tint"
        ],
    
        "SSS Intensity":[0.0,"SSS Intensity"],
        "Specular":[1.0,"Specular"],
        "Saturation":[0.0,"Saturation"],
        "Emissive Strength":[0.0,"Emission Strength"],
        "EmissiveIntensity":[0.0,"Emission Strength"],
        "Cliff Roughness":[1.0,"Relf/MREA Strength"],
        "TiledNormal_Intensity":[1.0,"Tiled Normal Strength"],
        "Normal_Intensity":[1.0,"Normal Strength"],
        "Roughness":[1.0,"Relf/MREA Strength"],
        "Normal Strength":[1.0,"Normal Strength"],
        
        "CliffTop_Or_Grass":[False],
        "Moss ":[False],
        "Blend Material on Top":[False],
        "Use Moss Mask":[False],
    }
    
    mapping_tex = {
        "Lianas":"Liana",
        "ubkmehzya":"Kapok"
    }
    
    tex_type_used = [
        "PM_Normals",
        "PM_SpecularMasks",
        "Normal",
        "ORMA Map",
        "PM_Diffuse",
        "Albedo",
        "Detail Albedo",
        "PM_Emissive",
        "Emissive",
        "Reflection",
        "ReflectionMap",
        "HRA",
        "Nor",
        "Baked Normal",
        "Detail_Normal",
        "ORMA",
        "Reflection Map",
        "DestructibleRocks_Refl",
        "DestructibleRocks_Alb",
        "DestructibleRocks_Nor",
        "FunnelTree_01_Refl",
        "NormalMap",
        "TilingBarkMREO",
        "TilingBarkBC",
        "TX_Grass_Dried_BC",
        "TX_Grass_Dried_MREO",
        "TX_Grass_Dried_N",
        "TX_TitanTree_01_N",
        "TX_TitanTree_masks_01",
        "TX_TubeCoral_BC"
    ]
    
    # TODO: materials with textures packed not according to name
    unique_mats = {
        "DioTree_LeafMap":{
            "No Alpha?":True
        }
    }
    
    top_mat_types = [
        "Grass",
        "Sand",
        "RedJungle",
        "RedGrass",
        "Moss",
        "WetSand",
        "Sandy",
    ]
    
    top_ao_mask = [
        "Desert"
    ]
    
    not_top_tex = [
        "MI_GrassTuftDry_01",
        "MI_CraterGrass_01",
        "MI_Grass_01",
        "MI_Grass_03",
        "MI_DryGrassStraws_01",
        "MI_Grass_Pink_01",
        "MI_TallGrass_01_Dry",
        "MI_Grass_BigTuft_01",
        "MI_TitanTree"
    ]
    
    mat_path = None
    
    exports_path = Path(sf_asset_export_path,"FactoryGame","Content")
    
    #search_file = list(Path(sf_asset_export_path,"Exports").rglob(f"{obj_material}.json"))
    search_file = list(Path(sf_asset_export_path,"FactoryGame").rglob(f"{obj_material}.json"))
    #print(search_file)
    if search_file:
        mat_path = search_file[0]
    
    # search Exports path if not found in mesh path 
    if not mat_path: # TODO
        print("mat file not found")
        return None
    
    # Get Material file
    try:
        mat_file = mat_path
        #if mat_path.name.endswith(".json"):
        #    mat_file = mat_path
        #else:
        #    mat_file = Path(mat_path,f"{obj_material}.json")
        
        with open(mat_path, 'r', encoding='utf-8') as f:
            m_data = json.load(f)
            
    except Exception as e:
        print("⚠️Error opening material file: ",e)
        return None
    
    textures = {} # type: dict[str,dict]
    switch_parameters = [] # type: list[dict[str,str]] 
    vec_parameters = [] # type: list[dict[str,dict]] 
    is_wrong_format = False
    is_cliff_mat = False
    use_tile_group = any(ut in obj_material for ut in use_tiling_group) and all(ntt not in obj_material for ntt in not_top_tex)
    has_top_mat = False
    use_alpha = False
    for item in m_data:
        if is_wrong_format:
            break
        #print(item)
        if type(item) == str:
            if item == "Parameters" or item == "Switches" or item == "Colors" or item == "Scalars":
                par_data = m_data[item]
                color_data = par_data.get("Colors") if item == "Parameters" else m_data["Colors"]
                scalar_data = par_data.get("Scalars") if item == "Parameters" else m_data["Scalars"]
                switch_data = par_data.get("Switches") if item == "Parameters" else m_data["Switches"]
            
                if color_data:
                    for color in color_data:
                        if "moss" in color.lower():
                            continue
                        if "tint" in color.lower() or "base" in color.lower():
                            parameters["color tint"][0]["R"] = color_data[color]["R"]
                            parameters["color tint"][0]["G"] = color_data[color]["G"]
                            parameters["color tint"][0]["B"] = color_data[color]["B"]
                            break
                if scalar_data:
                    for scalar in scalar_data:
                        if scalar in parameters:
                            parameters[scalar][0] = scalar_data[scalar]
                if switch_data:
                    for switch in switch_data:
                        if switch in parameters:
                            parameters[switch][0] = switch_data[switch]

                if not item == "Parameters":
                    break
            if item == "Textures":
                
                tex_data = m_data[item]
                for tex_name in tex_data:
                    if is_wrong_format:
                        break
                    set_colorspace = False
                    is_tex_tilling = ""
                    is_tex_detail = False
                    set_alpha_mode = ""
                    
                    if "cliff" in obj_material.lower():
                        is_cliff_mat = True
                    skip_tex = False
                    if "Desert" in tex_name and "cliff" in obj_material.lower():
                        skip_tex = True
                    if tex_name not in detail_normal_tex and not any(ut in tex_name for ut in use_tiling):
                            
                        if tex_name not in tex_type_used:
                            skip_tex = True
                    
                    if "desert" in obj_material.lower():
                        if "sand" in tex_name:
                            skip_tex = False
                    if skip_tex:
                        continue
                    
                    tex_path_tmp = tex_data[tex_name]
                    if tex_path_tmp == None:
                        continue
                    tex_path = tex_path_tmp
                    if type(tex_path_tmp) == dict:
                        if tex_path_tmp.get('AssetPathName'):
                            continue
                            tex_path = tex_path_tmp['AssetPathName']
                        elif tex_path_tmp.get('ObjectPath'):
                            tex_path = tex_path_tmp['ObjectPath']
                        else:
                            continue
                        #print(f"■■■ skipping wrong format mats: {mat_path}")
                        #is_wrong_format = True
                        #break
                        
                    if tex_path.startswith("/Engine"):
                        print("skipping engine tex",tex_name)
                        continue
                    
                    #if "Moss" in tex_path and "_Moss" not in obj_material:
                    #    if parameters["Moss "][0] == False:
                    #        print("skipping moss tex",tex_name)
                    #        continue
                    
                    is_exclude = False
                    for exc in exclude_tex:
                        if exc in tex_path:
                            is_exclude = True
                            print("skipping ",tex_name)
                            break
                    if is_exclude:
                        continue
                    
                    if all("_"+tm not in obj_material for tm in top_mat_types)and "Desert" not in obj_material:
                    #if "_Grass" not in obj_material and "_Sand" not in obj_material and "_RedJungle" not in obj_material and "Desert" not in obj_material: 
                        if any(tm in tex_path for tm in top_mat_types) and all(ntt not in obj_material for ntt in not_top_tex):
                        #if "Sand" in tex_path or "RedJungle" in tex_path or "Grass_01" in tex_path:
                            print("skipping top tex 1",tex_name)
                            continue
                    
                    if all(ntt not in obj_material for ntt in not_top_tex):
                        top_mat = ""
                        skip_tex = False
                        #if any(tm not in obj_material for tm in top_mat_types) and any(tm in tex_name for tm in top_mat_types):
                        #    print("skipping ",tex_name)
                        #    continue
                        for tm in top_mat_types:
                            if tm in obj_material:
                                top_mat = tm
                                has_top_mat = True
                                break
                        if any(tm in tex_name and tm != top_mat for tm in top_mat_types):
                            print("skipping top tex 2",tex_name)
                            continue
                    #for tm in top_mat_types:
                    #    if tm in tex_name and tm != top_mat:
                    #        skip_tex = True
                    #        break   
                    #if not skip_tex:
                    #    print("skipping ",tex_name)
                    #    continue
                    #if not top_mat:
                    #    print("skipping ",tex_name)
                    #    continue
                    #
                    #if "_Grass" in obj_material:
                    #    if "Sand" in tex_name or "RedJungle" in tex_name:
                    #        print("skipping ",tex_name)
                    #        continue
                    #
                    #if "_Sand" in obj_material:
                    #    if "Grass_01" in tex_name or "RedJungle" in tex_name:
                    #        print("skipping ",tex_name)
                    #        continue
                    #
                    #if "_RedJungle" in obj_material:
                    #    if "Sand" in tex_name or "Grass_01" in tex_name:
                    #        print("skipping ",tex_name)
                    #        continue
                    
                    tex_file = Path(exports_path,f"{tex_path[6:].split('.')[0]}.png")    
                    if not tex_file.exists():
                        print(f"Error: texture does not exist in search folder: {tex_file}")
                        continue
                    
                    if any(t in tex_name or t in tex_file.name for t in rn_type_tex):
                        set_colorspace = True
                    
                    
                    for tile in use_tiling:
                        if tile in tex_file.name:
                            is_tex_tilling = use_tiling[tile]
                    
                    if any(dnt in tex_file.name for dnt in detail_normal_tex):
                        if "Desert" in tex_file.name and any("Cliff_Sediment_Alb" in tex for tex in textures):
                            print(f"not setting {tex_file.name} as detail normal")
                        else:
                            is_tex_detail = True
                            
                    
                    # find out if tex is AO,BC,Relf or Nor
                    
                    tx_type = ""
                    tx_type_a = ""
                    mrea = False
                    if any(tm in tex_file.name for tm in top_mat_types) and all(ntt not in obj_material for ntt in not_top_tex):
                        
                        if "_N" in tex_file.name or "N" in tex_name:
                            #if "wet" not in tex_file.name.lower():
                            tx_type = "Top Normal/Nor/N"
                        if "_AO" in tex_file.name or "AO" in tex_name:
                            tx_type = "Top AO/IDMask"
                        for rt in rough_type_tex:
                            if rt in tex_file.name or rt in tex_name:
                                tx_type = "Top Relf/MREA"
                                tx_type_a = tx_type+" Alpha"
                                set_alpha_mode = 'CHANNEL_PACKED'
                            if "_MREA" in tex_file.name:
                                mrea = True
                        for bc in color_type_tex:
                            if bc in tex_file.name or bc in tex_name:
                                tx_type = "Top Color/BC/Albedo"
                                tx_type_a = "Top Albedo Alpha"
                                set_alpha_mode = 'CHANNEL_PACKED'
                    elif not is_tex_detail or not "FlatRock" in tex_file.name:
                        if "_N" in tex_file.name or "N" in tex_name:
                            tx_type = "Normal/Nor/N"
                        if "_AO" in tex_file.name or "AO" in tex_name:
                            tx_type = "AO/IDMask"
                        for rt in rough_type_tex:
                            if rt in tex_file.name or rt in tex_name:
                                for nt in nor_type_tex:
                                    if nt not in tex_file.name and nt not in tex_name:
                                        tx_type = "Relf/MREA"
                                        tx_type_a = tx_type+" Alpha"
                                        set_alpha_mode = 'CHANNEL_PACKED'
                            if "_MREA" in tex_file.name:
                                mrea = True
                        for bc in color_type_tex:
                            if bc in tex_file.name or bc in tex_name:
                                tx_type = "Color/BC/Albedo"
                                tx_type_a = "Albedo Alpha"
                                set_alpha_mode = 'CHANNEL_PACKED'
                    
                    if any(ua in obj_material for ua in uses_alpha):
                        use_alpha = True
                    
                    is_dup = False
                    for t in textures:
                        if tex_file == textures[t]["path"]:
                                is_dup = True
                        #for dt in t:
                        #    if tex_file in t[dt]:
                        #        is_dup = True
                    if not is_dup:
                        textures.update(
                            {tex_name:{
                                "path":tex_file,
                                "set_colorspace":set_colorspace,
                                "is_tex_detail":is_tex_detail,
                                "is_tex_tilling":is_tex_tilling,
                                "tx_type":tx_type,
                                "tx_type_a":tx_type_a,
                                "set_alpha_mode":set_alpha_mode,
                                "mrea":mrea
                                }}
                        )
            print(textures)
        
    print(f"Found {len(textures)} textures: {textures}")
    print(f"parameters: {parameters}")
    if is_wrong_format:
        print(f"Material file in wrong format: {obj_material}")
        return None
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
    
    
    # Start Textures logic
    if textures:
        print("Getting mat tex")
        sf_env_shader_node = nodes.new('ShaderNodeGroup')
        if bpy.data.node_groups.get("SFEnvShader"):
            sf_env_shader_node.node_tree = bpy.data.node_groups['SFEnvShader']
        else:
            # TODO: cancel or generate fallback group
            #sf_env_shader_node.node_tree = bpy.data.node_groups['FallBack']
            ...
        sf_env_shader_node.location.x = 200
        links.new(sf_env_shader_node.outputs["Shader"], output_node.inputs["Surface"])
        if use_alpha:
            sf_env_shader_node.inputs["Alpha?"].default_value = True
            
        set_par = []
        for par in parameters:
            if len(parameters[par]) == 1:
                continue
            if parameters[par][1] in set_par:
                continue
            if type(parameters[par][0] ) == float:
                set_par.append(parameters[par][1])
                sf_env_shader_node.inputs[parameters[par][1]].default_value = parameters[par][0]
            elif type(parameters[par][0]) == bool:
                set_par.append(parameters[par][1])
                sf_env_shader_node.inputs[parameters[par][1]].default_value = parameters[par][0]
            elif type(parameters[par][0]) == dict and "color" in par:
                set_par.append(parameters[par][1])
                
                color_par = parameters[par][0]
                sf_env_shader_node.inputs["BC Tint"].default_value = (color_par["R"], color_par["G"], color_par["B"], 1.0)
        
        tiling_shader_node = None
        if use_tile_group:
            if is_cliff_mat:
                sf_env_shader_node.inputs["Cliff Relf?"].default_value = True
            tiling_shader_node = nodes.new('ShaderNodeGroup')
            if bpy.data.node_groups.get("Tiling"):
                tiling_shader_node.node_tree = bpy.data.node_groups['Tiling']
                tiling_shader_node.location.x = -400
            if has_top_mat:
                sf_env_shader_node.inputs["Use Top?"].default_value = True
            
                
        pos = 0
        
        for tex in textures:
            tex_type = tex
            tex_file = textures[tex]["path"] # type: Path
            colorspace = textures[tex]["set_colorspace"] # type: bool
            tex_tilling = textures[tex]["is_tex_tilling"] # type: str
            is_detail_normal = textures[tex]["is_tex_detail"] # type: bool
            tx_type = textures[tex]["tx_type"] # type: str
            tx_type_a = textures[tex]["tx_type_a"] # type: str
            mrea = textures[tex]["mrea"] # type: bool
            set_alpha_mode = 'CHANNEL_PACKED' # type: str
            #for tt,tp in tex.items(): #should only have one item {texture type: texture path}
            #    tex_type = tt # type: str
            #    tex_file = tp["path"] # type: Path
            
            print("========================")
            print(f"Getting {tex_file} texture")
            print("========================")
            try:
                b_texture = b_material.node_tree.nodes.new('ShaderNodeTexImage')
                x = -200
                y = 0-(pos*50)
                pos += 1
                b_texture.location = Vector((x,y))
                img = bpy.data.images.get(tex_file.name)
                if img:
                    print("img in bl")
                    b_texture.image = img
                else:
                    print("img not in bl")
                    b_texture.image = bpy.data.images.load(os.fspath(tex_file))
                b_texture.hide = True
                for mt in mirrored_tex: # NOTE: not used
                    if mt in obj_material:#tex_file.name:
                        if "TX_Stencils" not in tex_file.name:
                            b_texture.extension = 'MIRROR'
                
                if colorspace:
                    #if '_N' in tex_file.name or 'Refl' in tex_file.name:
                    b_texture.image.colorspace_settings.name = 'Linear Rec.709'
                
                #is_detail_normal = False
                if tiling_shader_node:
                    if tex_tilling:
                        links.new(tiling_shader_node.outputs[tex_tilling], b_texture.inputs["Vector"])
                    #for tile in use_tiling:
                    #    if tile in tex_file.name:
                    #        links.new(tiling_shader_node.outputs[use_tiling[tile]], b_texture.inputs["Vector"])
                    
                    if is_detail_normal:
                        links.new(tiling_shader_node.outputs["Vector"], b_texture.inputs["Vector"])
                        links.new(b_texture.outputs["Color"], sf_env_shader_node.inputs["Normal/Nor/N top"])
                        continue
                    #links.new(tiling_shader_node.outputs["Vector"], b_texture.inputs["Vector"])
                    #for detail in detail_normal_tex:
                    #    if detail in tex_file.name:
                    #        if "Desert" in detail and "Cliff_Sediment_Alb" in textures:
                    #            continue
                    #        is_detail_normal = True
                    #        links.new(tiling_shader_node.outputs["Vector"], b_texture.inputs["Vector"])
                    #        links.new(b_texture.outputs["Color"], sf_env_shader_node.inputs["Normal/Nor/N top"])
                    #if is_detail_normal:    
                    #    continue
                if "FlatRock" in tex_file.name:#"Desert" in tex_file.name or "Flat" in tex_file.name:
                    continue
                #if "Sand" in tex_file.name or "RedJungle" in tex_file.name or "Grass_01" in tex_file.name:
                if any(tm in tex_file.name for tm in top_mat_types) and all(ntt not in obj_material for ntt in not_top_tex):
                    if any(tam in obj_material for tam in top_ao_mask):
                        sf_env_shader_node.inputs["Use AO Mask?"].default_value = True
                    if "_ORMA" in tex_file.name:
                        sf_env_shader_node.inputs["Top ORMA?"].default_value = True
                
                    if "_HRA" in tex_file.name:
                        sf_env_shader_node.inputs["Top HRA?"].default_value = True
                
                    #for ua in uses_alpha:
                    #    if ua in b_material.name:
                    #        continue
                
                    #tx_type = ""
                    #tx_type_a = ""
                    if mrea:
                        sf_env_shader_node.inputs["Top Relf or MREA?"].default_value = True
                    
                    if tex_type == "Top Color/BC/Albedo" or tex_type == "Top Relf/MREA":
                        b_texture.image.alpha_mode = set_alpha_mode
                        
                    #if "_N" in tex_file.name or "N" in tex_type:
                    #    if "wet" not in tex_file.name.lower():
                    #        tx_type = "Top Normal/Nor/N"
                    #if "_AO" in tex_file.name or "AO" in tex_type:
                    #    tx_type = "Top AO/IDMask"
                    #for rt in rough_type_tex:
                    #    if rt in tex_file.name or rt in tex_type:
                    #        tx_type = "Top Relf/MREA"
                    #        tx_type_a = tx_type+" Alpha"
                    #        b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                    #    if mrea:
                    #        sf_env_shader_node.inputs["Top Relf or MREA?"].default_value = True
                    #for bc in color_type_tex:
                    #    if bc in tex_file.name or bc in tex_type:
                    #        tx_type = "Top Color/BC/Albedo"
                    #        tx_type_a = "Top Albedo Alpha"
                    #        b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                
                    if not tx_type:
                        continue
                
                    links.new(b_texture.outputs["Color"], sf_env_shader_node.inputs[tx_type])
                    if tx_type_a:
                        links.new(b_texture.outputs["Alpha"], sf_env_shader_node.inputs[tx_type_a])
                else:
                    if "_ORMA" in tex_file.name:
                        if any(nao in tex_file.name for nao in no_a_orma_mats):
                            sf_env_shader_node.inputs["ORMA No Alpha?"].default_value = True
                        elif "Desert" in tex_file.name:
                            sf_env_shader_node.inputs["Desert ORMA?"].default_value = True
                        else:
                            sf_env_shader_node.inputs["ORMA?"].default_value = True
                    
                    #if "_HRA" in tex_file.name:
                    #    sf_env_shader_node.inputs["HRA?"].default_value = True
                    
                    #for ua in uses_alpha:
                    #    if ua in b_material.name:
                    #        continue
                            
                    #tx_type = ""
                    #tx_type_a = ""
                    if mrea:
                        sf_env_shader_node.inputs["Relf or MREA?"].default_value = True
                    
                    if tx_type == "Color/BC/Albedo" or tx_type == "Relf/MREA":
                        b_texture.image.alpha_mode = set_alpha_mode
                    
                    #if "_N" in tex_file.name or "N" in tex_type:
                    #    tx_type = "Normal/Nor/N"
                    #if "_AO" in tex_file.name or "AO" in tex_type:
                    #    tx_type = "AO/IDMask"
                    #for rt in rough_type_tex:
                    #    if rt in tex_file.name or rt in tex_type:
                    #        for nt in nor_type_tex:
                    #            if nt not in tex_file.name and nt not in tex_type:
                    #                
                    #                tx_type = "Relf/MREA"
                    #                tx_type_a = tx_type+" Alpha"
                    #                b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                    #    if "_MREA" in tex_file.name:
                    #        sf_env_shader_node.inputs["Relf or MREA?"].default_value = True
                    #for bc in color_type_tex:
                    #    if bc in tex_file.name or bc in tex_type:
                    #        tx_type = "Color/BC/Albedo"
                    #        tx_type_a = "Albedo Alpha"
                    #        b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                    
                    if not tx_type:
                        continue
                    
                    links.new(b_texture.outputs["Color"], sf_env_shader_node.inputs[tx_type])
                    
                    if tx_type_a:
                        links.new(b_texture.outputs["Alpha"], sf_env_shader_node.inputs[tx_type_a])
                
            except Exception as e:
                print("Error loading texture: ",e)
                return None         


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

def convert_heightmap(source_path: Path, output_path: Path) -> None:
    """Decode Unreal's packed red/green height values into a grayscale image."""
    with Image.open(source_path) as source:
        if source.mode != "RGBA":
            raise ValueError(
                f"Expected an RGBA height map, got {source.mode}: {source_path}"
            )

        rgba = source.tobytes()
        height_pixels = bytearray(source.width * source.height * 2)
        for pixel_index in range(source.width * source.height):
            source_index = pixel_index * 4
            height = (rgba[source_index] << 8) | rgba[source_index + 1]
            destination_index = pixel_index * 2
            height_pixels[destination_index : destination_index + 2] = height.to_bytes(
                2, sys.byteorder
            )

        grayscale = Image.frombytes("I;16", source.size, bytes(height_pixels))
        grayscale.save(output_path, format="PNG")
        grayscale.close()

def create_gs_heightmap(umap_path: Path, height_output_dir: Path | None = None):
    input_path = umap_path.expanduser()
    if input_path.is_file():
        sources = [input_path]
        default_output_dir = input_path.parent / "Heightmaps_Grayscale"
    elif input_path.is_dir():
        sources = sorted(input_path.glob("Heightmap_*.png"))
        default_output_dir = input_path / "Heightmaps_Grayscale"
    else:
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    
    if not sources:
        raise FileNotFoundError(f"No Heightmap_*.png files found in {input_path}")
    
    output_dir = (height_output_dir or default_output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for source_path in sources:
        output_path = output_dir / source_path.name
        if output_path.exists():
            print(f"Skipping {source_path.name}, already exists: {output_path}")
            continue
        convert_heightmap(source_path, output_path)
        print(f"Converted {source_path.name} -> {output_path}")
    
    print(f"Converted {len(sources)} height map(s) to 16-bit grayscale.")

fmodel_export_path = r"F:\blenber\SF to blend\fmodel export"
search_path = fmodel_export_path + r"\FactoryGame\Content\FactoryGame\Map\GameLevel01\Persistent_Level\_Generated_"
FOLDER_PATH = Path(fmodel_export_path + r"\Exports\FactoryGame\Content\FactoryGame\Map\GameLevel01\Persistent_Level\_Generated_")



actor = ""
root = ""
meshes = ""

umap_processed = {
    "root" : {
        "name":"", # root index
        "transform":{}
        },
    "mesh" : '',  # mesh name
    "transform" : {
        "location" : {},
        "rotation" : {},
        "scale" : {}
    }
}
umap_dict = {}
umap_type = {}
land_umap_dict = {}

exclude_actors = [
    "Spawn",
    "Spline",
    "BP_",
    "NiagaraActor",
    "Emitter",
    "LandscapeStreamingProxy",
    "FGItemPickup",
    "Volume",
    "Ambient",
    "Decal"
]

ex_dump = []
models_used = {}
#for file_path in sorted(FOLDER_PATH.rglob("0C0EB0SNHH89X7G16DXI46BC3.json")):
#for file_path in sorted(FOLDER_PATH.rglob("1IRGQ236BGL3067IY2HJARLHO.json")):
count = 0
is_skip = False

def find_translation_points(data: Any, path: str = "",u_type: int = 0,parent_coords:dict = {}) -> List[Tuple[str, float, float]]:
    """Return list of (path, x, y) for Translation objects that have both X and Y as floats.

    The path points to the parent object containing `Translation`.
    """
    #if not has_foliage:
    #    return []
    results: List[Tuple[str, float, float]] = []
    if isinstance(data, dict):
        if u_type == 1:
            if data.get("Name") == "RootComponent0":
                root_props = data.get("Properties", {})
                translation = root_props.get("RelativeLocation", {})
                if isinstance(translation, dict) and "X" in translation and "Y" in translation:
                    try:
                        x_val = float(translation["X"])
                        y_val = float(translation["Y"])
                        results.append((path + "/Translation", x_val, y_val))
                        #return results
                    except (TypeError, ValueError):
                        pass
            #if "CachedBounds" in data:
            #    translation = data["CachedBounds"]["Value"]["Origin"]
            #
            #    if isinstance(translation, dict) and "X" in translation and "Y" in translation:
            #        try:
            #            x_val = float(translation["X"])
            #            y_val = float(translation["Y"])
            #            results.append((path + "/Translation", x_val, y_val))
            #        except (TypeError, ValueError):
            #            pass
            for key, value in data.items():
                new_path = f"{path}/{key}" if path else str(key)
                results.extend(find_translation_points(value, new_path,u_type))
        elif u_type == 2:
            #if data.get("Name") == "RootComponent0":
            #    parent_coords = []
            #    root_props = data.get("Properties", {})
            #    translation = root_props.get("RelativeLocation", {})
            #    if isinstance(translation, dict) and "X" in translation and "Y" in translation:
            #        try:
            #            x_val = float(translation["X"])
            #            y_val = float(translation["Y"])
            #            parent_coords.append(x_val)
            #            parent_coords.append(y_val)
            #            results.append((path + "/Translation", x_val, y_val))
            #            #return results
            #        except (TypeError, ValueError):
            #            pass
            
            if data.get("Type") == "LandscapeComponent" and parent_coords:
            #if "RelativeLocation" in data and parent_coords:
                props = data.get("Properties", {})
                translation = props.get("RelativeLocation", {})
                #translation = data["RelativeLocation"]
                if isinstance(translation, dict) and "X" in translation and "Y" in translation:
                    try:
                        x_val = float(translation["X"])*100 + parent_coords["X"]
                        y_val = float(translation["Y"])*100 + parent_coords["Y"]
                        results.append((path + "/Translation", x_val, y_val))
                        #return results
                    except (TypeError, ValueError):
                        pass
            #if "CachedBounds" in data:
            #    translation = data["CachedBounds"]["Value"]["Origin"]
            #
            #    if isinstance(translation, dict) and "X" in translation and "Y" in translation:
            #        try:
            #            x_val = float(translation["X"])
            #            y_val = float(translation["Y"])
            #            results.append((path + "/Translation", x_val, y_val))
            #        except (TypeError, ValueError):
            #            pass
            for key, value in data.items():
                new_path = f"{path}/{key}" if path else str(key)
                results.extend(find_translation_points(value, new_path,u_type,parent_coords=parent_coords))
        elif u_type == 0:
                
            if "Translation" in data or "RelativeLocation" in data:
                translation = data["Translation"] if "Translation" in data else data["RelativeLocation"]
                
                if isinstance(translation, dict) and "X" in translation and "Y" in translation:
                    try:
                        x_val = float(translation["X"])
                        y_val = float(translation["Y"])
                        results.append((path + "/Translation", x_val, y_val))
                    except (TypeError, ValueError):
                        pass
            for key, value in data.items():
                new_path = f"{path}/{key}" if path else str(key)
                results.extend(find_translation_points(value, new_path,u_type))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            new_path = f"{path}[{index}]"
            results.extend(find_translation_points(item, new_path,u_type,parent_coords=parent_coords))
    return results



def scan_file(file_path: Path) -> List[Tuple[str, float, float]]:
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    u_type = 0
    #print("type:", end="\r")
    for i in data:
        if "Foliage" in i["Type"]:
            u_type = 1
            #print("type: Foliage")
            break
    
    parent_coords = {}
    for i in data:
        if "LandscapeComponent" in i["Type"]:
            if i.get("Properties"):
                root_idx = int(i["Properties"]["AttachParent"]["ObjectPath"].split(".")[-1])
                root_component = data[root_idx]
                parent_coords = root_component["Properties"]["RelativeLocation"]
                
            u_type = 2
            #print("type: Landscape")
            break
    #print()
    return find_translation_points(data,u_type=u_type,parent_coords=parent_coords)


def main() -> None:
    print("------------------------------------------------------------")
    if not FOLDER_PATH.exists():
        print(f"Folder not found: {FOLDER_PATH}")
    if not FOLDER_PATH.is_dir():
        print(f"Not a folder: {FOLDER_PATH}")

    print(f"Scanning folder: {FOLDER_PATH}")
    print(f"Target X: {TARGET_X}")
    print(f"Target Y: {TARGET_Y}")
    print(f"Tolerance: {TOLERANCE}")
    print("---")

    matched_files = 0
    no_matches = 0
    import_files = {}
    umap_names = set()
    delete_files = []
    #map_col = bpy.data.collections.get("map")
    #if not map_col:
    #    map_col = bpy.data.collections.new("map")
    #    bpy.context.scene.collection.children.link(map_col)
        
    for file_path in sorted(FOLDER_PATH.rglob("*.json")):
        matches = scan_file(file_path)
        close_matches = []
        if not matches:
            continue
        for path, x_val, y_val in matches:
            if x_val == 0.0 and y_val == 0.0:
                continue
            dx = abs(x_val - TARGET_X)
            dy = abs(y_val - TARGET_Y)
            if dx <= TOLERANCE and dy <= TOLERANCE:
                close_matches.append((path, x_val, y_val, dx, dy))
        if close_matches:
            #print()
            matched_files += 1
            #print(f"File: {file_path.stem}")
            umap_names.add(file_path.stem)
            search_file = list(Path(search_path,file_path.stem).rglob("Persistent_Level.usda"))
            #print(f"found File: {search_file[0]}")
            import_files.update({
                file_path.stem:search_file[0]
                })
            print(f" total imported umap files: {matched_files}/{no_matches} files", end="\r")
            
            #time.sleep(1)
            #for path, x_val, y_val, dx, dy in close_matches:
            #    print(f"  {path}: X={x_val} (dx {dx:.6f}), Y={y_val} (dy {dy:.6f})")
            #print("---")
        else:
            no_matches += 1
            print(f" total imported umap files: {matched_files}/{no_matches} files", end="\r")

    print()
    if matched_files == 0:
        print("No files with close Translation/X or Translation/Y values found.")
    print(f"Found {matched_files} file(s) with close Translation/X and Translation/Y values.")
    
    print(f"Importing {len(import_files)} files into Blender...")
    
    
    
    for un in umap_names:
        file_path = Path(FOLDER_PATH,un+".json")

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        umap_dict.update({
            file_path.stem:[]
        })
        
        land_umap_dict.update({
            file_path.stem:[]
        })
        
        #print(data[194])
        actor_indexes = []
        instance_indexes = []
        root_indexes = []
        
        umap_meshes = {}
        
        #if "Audio" in data[0]["Name"]:
        #    continue
        
        u_type = 0
        for item in data:
            if "Foliage" in item["Type"]:
                u_type = 1
                
            elif "LandscapeComponent" in item["Type"]:
                u_type = 2
                
            
            umap_type.update({
                file_path.stem:u_type
            })
        
        for item in data:
            if is_skip:
                break
            #if u_type == 2:
            #    break
            #print("type:", end="\r")
            
            i_type = item.get("Type")
            if "Level" in i_type:
                #print(i_type)
        
                for actor in item["Actors"]:
                    if is_skip:
                        break
                    if not actor:
                        continue
        
                    actor_index = int(actor["ObjectPath"].split('.')[-1])
                    actor_indexes.append(actor_index)
        
                ex_temp = []
                for act_idx in actor_indexes:
                    if is_skip:
                        break
                    actor_data = data[act_idx]
                    if actor_data["Type"] == "FGWorldSettings":
                        continue
                    if not actor_data.get("Properties"):
                        continue
                    if not actor_data["Properties"].get("RootComponent"):
                        continue
                    root_index = int(actor_data["Properties"]["RootComponent"]["ObjectPath"].split('.')[-1])
                    root_indexes.append(root_index)
                    if actor_data["Properties"].get("StaticMeshComponent"):
                        static_comp = actor_data["Properties"]["StaticMeshComponent"]
                        instance_index = int(static_comp["ObjectPath"].split('.')[-1])
                        instance_indexes.append(instance_index)
                        #is_skip = True
                        #break
                    elif actor_data["Properties"].get("mStaticMesh"):
                        static_comp = actor_data["Properties"]["mStaticMesh"]
                        instance_index = int(static_comp["ObjectPath"].split('.')[-1])
                        instance_indexes.append(instance_index)
                    elif actor_data["Properties"].get("StaticMesh"):
                        static_comp = actor_data["Properties"]["StaticMesh"]
                        instance_index = int(static_comp["ObjectPath"].split('.')[-1])
                        instance_indexes.append(instance_index)
        
                    elif actor_data["Properties"].get("mDepositMeshComponent"):
                        static_comp = actor_data["Properties"]["mDepositMeshComponent"]
                        instance_index = int(static_comp["ObjectPath"].split('.')[-1])
                        instance_indexes.append(instance_index)
                    elif actor_data["Properties"].get("InstanceComponents"):
                        for int_comp in actor_data["Properties"]["InstanceComponents"]:
                            if not int_comp:
                                continue
                            instance_index = int(int_comp["ObjectPath"].split('.')[-1])
                            instance_indexes.append(instance_index)
                    
                    elif actor_data["Properties"].get("LandscapeComponents"):
                        for int_comp in actor_data["Properties"]["LandscapeComponents"]:
                            if not int_comp:
                                continue
                            instance_index = int(int_comp["ObjectPath"].split('.')[-1])
                            instance_indexes.append(instance_index)
                    else:
                        actor_props = actor_data["Properties"]
                        actor_type = actor_data["Type"]
                        if any(ex in actor_type for ex in exclude_actors):
                            ex_dump.append(actor_type)
                            continue
                        if actor_type.startswith("BP_"):
                            ...
                        ex_temp.append(actor_type)
                        print(actor_type)
                        #continue
        
                if ex_temp:
                    print(ex_temp)
                    break
                #    print()
        
                if len(ex_temp) == (len(actor_indexes)-1):
                    break
        
                #umap_lists = [umap_processed] * len(root_indexes)
                all_root_dict = {}
                for idx,root_idx in enumerate(root_indexes):
                    if is_skip:
                        break
                    root_data = data[root_idx]
                    if root_data.get("PerInstanceSMData"):
                        root_trans = root_data["PerInstanceSMData"][0]["TransformData"]["Translation"]
                    elif root_data["Properties"].get("RelativeLocation"):
                        root_trans = root_data["Properties"]["RelativeLocation"]
                    else:
                        root_trans = {
                            "X": 0.0,
                            "Y": 0.0,
                            "Z": 0.0
                        }
        
                    all_root_dict.update({
                        root_idx:root_trans
                    })
        
                    #print()
        
                for instance_idx in instance_indexes:
                    if is_skip:
                        break
                    instance_data = data[instance_idx]
                    instance_props = instance_data["Properties"]
        
                    root_parent_name = None
                    if not instance_props.get("AttachParent"):
                        root_parent = None
                    elif "RootComponent0" in instance_props["AttachParent"]["ObjectName"]:
                        root_parent = int(instance_props["AttachParent"]["ObjectPath"].split('.')[-1])
                    else:
                        root_parent = int(instance_props["AttachParent"]["ObjectPath"].split('.')[-1])
                        root_parent_name = data[root_parent]["Name"]
        
                    mesh = instance_props.get("StaticMesh") # maybe add to list of meshes used in umap?
                    height_map = instance_props.get("HeightmapTexture")
                    if not mesh and not height_map:
                        continue
                    
                    if height_map:
                        s_base_x = instance_props.get("SectionBaseX")
                        s_base_y = instance_props["SectionBaseY"]
                    
                        if instance_props.get("RelativeLocation"):
                            offset = (
                                instance_props["RelativeLocation"]["X"] if instance_props["RelativeLocation"]["X"] > 0 else 0,
                                (instance_props["RelativeLocation"]["Y"] * -1) - 127 if instance_props["RelativeLocation"]["Y"] > 0 else -127,
                            )
                        else:
                            offset = (
                                0,
                                -127,
                            )
                        mega_tile_name = height_map["ObjectName"].split('.')[1]
                        height_map_path = Path(height_map["ObjectPath"][6:].split('.')[0],"PersistentLevel",height_map["ObjectName"].split('.')[1],"Heightmaps_Grayscale",height_map["ObjectName"].split('.')[2][:-1]+".png")
                    
                        weightmaps = [ 
                                    Path(weight["ObjectPath"][6:].split('.')[0],"PersistentLevel",weight["ObjectName"].split('.')[1],weight["ObjectName"].split('.')[2][:-1]+".png") 
                                    for weight in instance_props["WeightmapTextures"] 
                                    ]
                        layer_maps = {
                            "Cliff_LayerInfo":{},
                            "CoralRock_LayerInfo":{},
                            "DesertRock_LayerInfo":{},
                            "Foliage_Eraser_LayerInfo":{},
                            "Forest_LayerInfo":{},
                            "Grass_LayerInfo":{},
                            "GrassRed_LayerInfo":{},
                            "Gravel_WeightLayerInfo":{},
                            "Puddles_LayerInfo":{},
                            "PurpleForest_LayerInfo":{},
                            "RedJungle_LayerInfo":{},
                            "Sand_LayerInfo":{},
                            "SandCracks_LayerInfo":{},
                            "SandPebbles_LayerInfo":{},
                            "SandRipples_LayerInfo":{},
                            "SandRock_LayerInfo":{},
                            "Soil_LayerInfo":{},
                            "WetSand_LayerInfo":{}
                        }
                        for weight in instance_props["WeightmapLayerAllocations"]:
                            weightmap_index = weight["WeightmapTextureIndex"]
                            weightmap_Channel = weight["WeightmapTextureChannel"]
                    
                            layer_maps[weight["LayerInfo"]["ObjectName"].split("'")[1]] = {
                                "weightmap":weightmap_index,
                                "channel":weightmap_Channel
                            }
                    
                        #height_maps.update({
                        #    height_map["ObjectName"].split("'")[1]:height_map["ObjectPath"].split('.')[0]
                        #})
                    
                    
                        mesh_object_name = instance_data["Name"]
                        root_name = f"RootComponent0.{root_parent}"
                        root_transform = all_root_dict[root_parent]
                    
                        land_umap_dict[file_path.stem].append(
                                        {
                                            "ObjectName": mesh_object_name,
                                            "root" : {
                                                "name":root_name,
                                                "transform":root_transform
                                                },
                                            "mesh" : mesh_object_name,
                                            "height_map_path" : height_map_path,
                                            "weightmaps" : weightmaps,
                                            "layer_maps" : layer_maps,
                                            "s_base_x" : s_base_x,
                                            "s_base_y" : s_base_y,
                                            "offset":offset,
                                            "mega_tile_name":mega_tile_name
                                        }
                                        )
                        continue
                    
                    
                    models_used.update({
                        mesh["ObjectName"].split("'")[1]:mesh["ObjectPath"].split('.')[0]
                    })
                    instance_count = 1
                    instance_bounds = {}
                    if instance_props.get("TranslatedInstanceSpaceOrigin"):
                        translations = instance_props["TranslatedInstanceSpaceOrigin"]
                        if instance_props["InstanceCountToRender"] > 1:
                            instance_count = instance_props["InstanceCountToRender"]
                            instance_bounds = instance_props["BuiltInstanceBounds"]
                    elif instance_props.get("RelativeLocation"):
                        translations = instance_props["RelativeLocation"]
                    else:
                        translations = None # replace if more translations found
                    rotation = instance_props.get("RelativeRotation") or instance_props.get("Rotation") # replace if more translations found
                    scale = instance_props.get("RelativeScale3D") # replace if more translations found
                    override_materials = None
                    mesh_object_name = instance_data["Name"]
                    if instance_props.get("OverrideMaterials"):
                        #if len(instance_props["OverrideMaterials"]) > 2:
                        #    print(instance_props["OverrideMaterials"])
                        if instance_props["OverrideMaterials"][0]:
                            override_materials = instance_props["OverrideMaterials"][0]["ObjectName"].split("'")[1]
        
                    transform_data = {
                        "location" : translations,
                        "rotation" : rotation,
                        "scale" : scale
                    }
        
                    per_instance_data = instance_data.get("PerInstanceSMData")
                    if per_instance_data:
                        per_transform_data = []
                        for int_trans in per_instance_data:
                            translations = int_trans["TransformData"]["Translation"]
                            rotation = {
                                "X":float(int_trans["TransformData"]["Rotation"]["X"]),
                                "Y":float(int_trans["TransformData"]["Rotation"]["Y"]),
                                "Z":float(int_trans["TransformData"]["Rotation"]["Z"]),
                                "W":float(int_trans["TransformData"]["Rotation"]["W"]),
                                }
                            scale = int_trans["TransformData"]["Scale3D"]
                            per_transform_data.append({
                                "location" : translations,
                                "rotation" : rotation,
                                "scale" : scale
                            })
                            transform_data = per_transform_data
        
        
                    umap_meshes.update({
                        mesh["ObjectName"].split("'")[1]:mesh["ObjectPath"].split(".")[0]
                        })
        
                    if not root_parent:
                        root_name = None
                        root_transform = None
                    elif root_parent_name:
                        root_name = f"{root_parent_name}"
                        root_transform = all_root_dict[root_parent]
                    else:
                        root_name = f"RootComponent0.{root_parent}"
                        root_transform = all_root_dict[root_parent]
        
                    umap_dict[file_path.stem].append(
                                    {
                                        "ObjectName": mesh_object_name,
                                        "root" : {
                                            "name":root_name,
                                            "transform":root_transform
                                            },
                                        "mesh" : mesh["ObjectName"].split("'")[1],  # mesh name
                                        "transform" : transform_data,
                                        "OverrideMaterials" : override_materials,
                                        "instance_count" : instance_count,
                                        "instance_bounds":instance_bounds
                                    }
                                    )
        
                    #print()

                print(f"processed {un}")
                break
        
        
        
        sc_col = bpy.context.scene.collection
        map_col = bpy.data.collections.get("umaps")
        if not map_col:
            map_col = bpy.data.collections.new("umaps")
            sc_col.children.link(map_col)
        
        type_idx = {
            0:"rock",
            1:"foliage",
            2:"landscape"
        }
        umap_type_col = type_idx[umap_type[file_path.stem]]
        type_col = bpy.data.collections.get(umap_type_col)
        if not type_col:
            type_col = bpy.data.collections.new(umap_type_col)
            map_col.children.link(type_col)
        
        if land_umap_dict.get(file_path.stem):
            tile_names = set()
            for i in land_umap_dict[file_path.stem]:
                tile_names.add(i["mega_tile_name"])
            for tile in tile_names:
                umap_path = Path(search_path) / file_path.stem / "PersistentLevel" / tile
                create_gs_heightmap(umap_path)
            for i in land_umap_dict[file_path.stem]:
                if i == []:
                    continue
        
                #break
                point_positions = []
        
                if "RootComponent0" in i["root"]["name"]:
                    ob_parent = bpy.data.objects.get(file_path.stem+"_"+i["root"]["name"])
                    if not ob_parent:
                        ob_parent = bpy.data.objects.new(file_path.stem+"_"+i["root"]["name"],None)
                    pos = i["root"]["transform"]['X'] / 100.0, -i["root"]["transform"]['Y'] / 100.0, i["root"]["transform"]['Z'] / 100.0
                    ob_parent.location = pos
                    ob_parent.scale = ob_parent.scale
                    point_positions = [pos]
                else:
                    ob_parent = None
        
                has_attr = True
        
                if not point_positions:
                    continue
                mesh = bpy.data.meshes.new(f"{file_path.stem+"_"+i["mesh"]}_Points")
                mesh.from_pydata(point_positions, [], [])
                # object from the mesh
                point_obj = bpy.data.objects.new(f"{file_path.stem+"_"+i["mesh"]}_Points", mesh)
                if ob_parent:
                    point_obj.parent = ob_parent
        
                if has_attr:
                    for layer in i["layer_maps"]:
                        if i["layer_maps"][layer]:
                            layer_attr = (i["layer_maps"][layer]["weightmap"],i["layer_maps"][layer]["channel"],0)
                            mesh.attributes.new(layer, "FLOAT_VECTOR", "POINT")
                            mesh.attributes[layer].data.foreach_set("vector", layer_attr)
        
        
                heightmap_path = Path(fmodel_export_path,r"FactoryGame\Content") / i["height_map_path"]
                if not heightmap_path.exists():
                    print(f"Heightmap not found: {heightmap_path}")
                    continue
                heightmap_img = bpy.data.images.load(os.fspath(heightmap_path))
                heightmap_img.colorspace_settings.name = 'Linear Rec.709'
        
                weightmap_img = []
                for w in i["weightmaps"]:
                    weightmap_path = Path(fmodel_export_path,r"FactoryGame\Content") / w
                    if not weightmap_path.exists():
                        print(f"Weightmap not found: {weightmap_path}")
                        continue
                    weightmap_img.append(bpy.data.images.load(os.fspath(weightmap_path)))
                if bpy.data.node_groups.get("landscape_builder"):
                    node_group = bpy.data.node_groups["landscape_builder"]
                    mod = point_obj.modifiers.new(name="LandscapeBuilder", type="NODES")
                    mod.node_group = node_group
        
                    if mesh:
        
                        set_geonode_input(mod, "Heightmap", heightmap_img)
        
                        set_geonode_input(mod, "Pos", i["offset"])
        
                        section_base = (i.get("s_base_x", 0) or 0, i.get("s_base_y", 0))
                        print(f"Section Base: {section_base}")
                        set_geonode_input(mod, "Section Base", section_base)
                        for idx, we in enumerate(weightmap_img,1):
                            we.colorspace_settings.name = 'Linear Rec.709'
                            we.alpha_mode = 'CHANNEL_PACKED'
                            set_geonode_input(mod, f"Weightmap {idx}", we)
        
                #node_group = bpy.data.node_groups["instance env"]
                #mod = point_obj.modifiers.new(name="InstanceEnv", type="NODES")
                #mod.node_group = node_group
        
                col = bpy.data.collections.get(file_path.stem)
                if not col:
                    col = bpy.data.collections.new(file_path.stem)
                    type_col.children.link(col)
        
                if ob_parent:
                    if sc_col in ob_parent.users_collection:
                        sc_col.objects.unlink(ob_parent) 
        
                    if col not in ob_parent.users_collection:
                        col.objects.link(ob_parent)
        
                if sc_col in point_obj.users_collection:
                    sc_col.collection.objects.unlink(point_obj) 
        
                if col not in point_obj.users_collection:
                    col.objects.link(point_obj)
            
        else:
            models_col = bpy.data.collections.get("models")
            if not models_col:
                models_col = bpy.data.collections.new("models")
                sc_col.children.link(models_col)
            models_col.hide_viewport = True
            models_col.hide_render = True
            
            print(f"--------------Total models to import {len(models_used)}")
            for model in models_used:
                #continue
                print(model)
                ob = bpy.data.objects.get(model)
                if ob == None: 
                    model_in_path = models_used[model].replace("/Game",r"FactoryGame\Content")
                    model_file = Path(fmodel_export_path,model_in_path+".psk") #os.fspath(FOLDER_PATH+model_in_path+".psk")
                    is_pskx = "ALL"
                    if not model_file.exists():
                        model_file = Path(fmodel_export_path,model_in_path+".pskx")
                        is_pskx = "MESH"
                        if not model_file.exists():
                            continue
                    print(f"{model_file.stem} not in blend file. Needs to be imported")
                    try:
                        bpy.ops.psk.import_file(
                            filepath=os.fspath(model_file),
                            should_import_mesh=True, 
                            should_import_armature=True,
                            bone_length=30,
                            #scale=.01,
                            components=is_pskx
                        )
                    except Exception as e:
                        print(f"⚠️Error importing {model_file.stem}: {e}")
                        #continue
                    ob = bpy.data.objects.get(model_file.stem)
                else:
                    continue
                    
            
                if not ob:
                    print(f"⚠️Error: {models_used[model]} did not import into blend file.")
                    continue
                
                obj_materials = [slot.material.name for slot in ob.material_slots if slot.material]
                for i,mat in enumerate(obj_materials):
                    mat_results = get_materials(obj_material=mat,sf_asset_export_path=fmodel_export_path)
                    if mat_results == None:
                        print(f"got {mat} material")
                
                if sc_col in ob.users_collection:
                    sc_col.objects.unlink(ob) 
                if models_col not in ob.users_collection:
                    models_col.objects.link(ob)
            
            
            #if umap_type[file_path.stem] == 2:
            #    usd_file_path = import_files[file_path.stem]
            #    #break
            #    umap_name = usd_file_path.parent.name
            #
            #
            #    umap_col = bpy.data.collections.get(umap_name)
            #    #if map_col.children.get(umap_name):
            #    #    print(f"Removing existing collection: {umap_name}")
            #    #    bpy.data.collections.remove(umap_col)
            #    #    umap_col = bpy.data.collections.new(umap_name)
            #    #    map_col.children.link(umap_col)
            #    if not umap_col:
            #        umap_col = bpy.data.collections.new(umap_name)
            #        #bpy.context.scene.collection.children.link(umap_col)
            #        type_col.children.link(umap_col)
            #
            #    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[map_col.name].children[type_col.name].children[umap_col.name]
            #
            #    bpy.ops.wm.usd_import(
            #        filepath=str(usd_file_path),
            #        import_materials=True,
            #        import_meshes=True,
            #        import_volumes=True,
            #        scale=1.0,
            #        read_mesh_uvs=True,
            #        read_mesh_colors=True,
            #        read_mesh_attributes = True,
            #        import_textures_mode  = 'IMPORT_NONE',
            #        mtl_name_collision_mode = 'REFERENCE_EXISTING',
            #        support_scene_instancing = True,
            #        mtl_purpose = 'MTL_FULL',
            #        import_skeletons=True,
            #        import_blendshapes=True,
            #        import_shapes =True,
            #        #create_collection=True,
            #        set_frame_range = False,
            #    )
            
            count = 0
            maxx = 10
            for i in umap_dict[file_path.stem]:
                count+=1
                #if count == maxx:
                #    break
            
                if i == []:
                    continue
            
                #break
            
                if i["root"]["name"] == None:
                    ob_parent = None
                elif "RootComponent0" in i["root"]["name"]:
                    ob_parent = bpy.data.objects.get(file_path.stem+"_"+i["root"]["name"])
                    if not ob_parent:
                        ob_parent = bpy.data.objects.new(file_path.stem+"_"+i["root"]["name"],None)
                    pos = i["root"]["transform"]['X'] / 100.0, -i["root"]["transform"]['Y'] / 100.0, i["root"]["transform"]['Z'] / 100.0
                    ob_parent.location = pos
                    ob_parent.scale = ob_parent.scale
                elif i["root"]["name"]:
                    ob_parent = bpy.data.objects.get(file_path.stem+"_"+i["root"]["name"])
                    if not ob_parent:
                        ob_parent = None
                else:
                    ob_parent = None
                
                
                ob_instance_mesh = bpy.data.objects.get(i["mesh"])
            
                point_positions = []
                rotation_attr = []
                scale_attr = []
                has_attr = False
                #override_materials_attr = []
                if type(i["transform"]) == list:
                    for t in i["transform"]:
                        point_positions.append((
                            t["location"]["X"] / 100.0,
                            t["location"]["Y"] / -100.0,
                            t["location"]["Z"] / 100.0
                            ))
                        r = t["rotation"]
                        quat = Quaternion((-r['W'], r['X'], -r['Y'], r['Z']))
                        euler = quat.to_euler("XYZ")
                        #rot = euler.x, euler.y, euler.z
                        rotation_attr.extend([
                            euler.x,
                            euler.y,
                            euler.z
                        ])
                        scale_attr.extend([
                            t["scale"]["X"] / 100,
                            t["scale"]["Y"] / 100,
                            t["scale"]["Z"] / 100
                        ])
                        has_attr = True
                else:
                    if i["transform"]["location"]:
                        point_positions.append((
                            i["transform"]["location"]["X"] / 100.0,
                            i["transform"]["location"]["Y"] / -100.0,
                            i["transform"]["location"]["Z"] / 100.0
                            ))
                    else:
                        point_positions.append((
                            0.0,
                            0.0,
                            0.0
                            ))
                    if i["transform"]["rotation"]:
                        r = i["transform"]["rotation"]
                        if len(r) > 3:
                            quat = Quaternion((-r['W'], r['X'], -r['Y'], r['Z']))
                            euler = quat.to_euler("XYZ")
                            rotation_attr.extend([
                                euler.x,
                                euler.y,
                                euler.z
                            ])
                        else:
                            #rot = (math.radians(r['Roll']), math.radians(-r['Pitch']), math.radians(-r['Yaw'])) # X=Z Y=X Z=X
                            rotation_attr.extend([
                                math.radians(r['Roll']), 
                                math.radians(-r['Pitch']), 
                                math.radians(-r['Yaw'])
                            ])
                    if i["transform"]["scale"]:
                        scale_attr.extend([
                            i["transform"]["scale"]["X"] / 100,
                            i["transform"]["scale"]["Y"] / 100,
                            i["transform"]["scale"]["Z"] / 100
                        ])
                    has_attr = True
                if not point_positions:
                    continue
                mesh = bpy.data.meshes.new(f"{file_path.stem+"_"+i["mesh"]}_Points")
                mesh.from_pydata(point_positions, [], [])
                # object from the mesh
                point_obj = bpy.data.objects.new(f"{file_path.stem+"_"+i["mesh"]}_Points", mesh)
                if ob_parent:
                    point_obj.parent = ob_parent
            
                if has_attr:
                    if type(i["transform"]) == list:#i["transform"]["scale"]:
                        mesh.attributes.new("scale", "FLOAT_VECTOR", "POINT")
                        mesh.attributes["scale"].data.foreach_set("vector", scale_attr)
                    mesh.attributes.new("rotation", "FLOAT_VECTOR", "POINT")
                    mesh.attributes["rotation"].data.foreach_set("vector", rotation_attr)
            
                if bpy.data.node_groups.get("instance env"):
                    node_group = bpy.data.node_groups["instance env"]
                    mod = point_obj.modifiers.new(name="InstanceEnv", type="NODES")
                    mod.node_group = node_group
                    
                    if ob_instance_mesh:
                        #set_geonode_input(mod, "Use Culling", True)
                        set_geonode_input(mod, "Object", ob_instance_mesh)
                        if i["OverrideMaterials"]:
                            om_attr = [True] * len(point_positions)
                            mesh.attributes.new("OverrideMaterial", "BOOLEAN", "POINT")
                            mesh.attributes["OverrideMaterial"].data.foreach_set("value", om_attr)
                            mat_name = i["OverrideMaterials"]
                            o_mat = bpy.data.materials.get(i["OverrideMaterials"])
                            if not o_mat:
                                o_mat = bpy.data.materials.new(i["OverrideMaterials"])
                            
                                mat_results = get_materials(obj_material=mat_name,sf_asset_export_path=fmodel_export_path)
                                if mat_results == None:
                                    print(f"got {mat_name} material")
                            set_geonode_input(mod, "Override Material", o_mat)
                        
                        if i["instance_count"] > 1:
                            set_geonode_input(mod, "Instance Count", i["instance_count"])
                            if i["instance_bounds"]:
                                in_max = Vector((
                                    i["instance_bounds"]["Max"]['X'] / 100.0,
                                    i["instance_bounds"]["Max"]['Y'] / 100.0,
                                    i["instance_bounds"]["Max"]['Z'] / 100.0
                                    ))
                                in_min = Vector((
                                    i["instance_bounds"]["Min"]['X'] / 100.0,
                                    i["instance_bounds"]["Min"]['Y'] / 100.0,
                                    i["instance_bounds"]["Min"]['Z'] / 100.0
                                    ))
                                set_geonode_input(mod, "Instance Pos Min", in_min)
                                set_geonode_input(mod, "Instance Pos Max", in_max)
                    else:
                        set_geonode_input(mod, "Use Default Object", True)
            
                
                    
                
                
                #continue
                col = bpy.data.collections.get(file_path.stem)
                
                if not col:
                    col = bpy.data.collections.new(file_path.stem)
                    type_col.children.link(col)
            
                if ob_parent:
                    if sc_col in ob_parent.users_collection:
                        sc_col.objects.unlink(ob_parent) 
            
                    if col not in ob_parent.users_collection:
                        col.objects.link(ob_parent)
            
                if sc_col in point_obj.users_collection:
                    sc_col.collection.objects.unlink(point_obj) 
            
                if col not in point_obj.users_collection:
                    col.objects.link(point_obj)
        print(f"imported {un}")
        
#fmodel_export_path = r"FMODEL-EXPORT-PATH"
fmodel_export_path = r"F:\blenber\SF to blend\fmodel export"
search_path = fmodel_export_path + r"\FactoryGame\Content\FactoryGame\Map\GameLevel01\Persistent_Level\_Generated_"
FOLDER_PATH = Path(fmodel_export_path + r"\Exports\FactoryGame\Content\FactoryGame\Map\GameLevel01\Persistent_Level\_Generated_")

# import coordinates. Multiply by 100 for conversion from unreal units to blender units (1 unit = 100 blender units).
TARGET_X = -300 * 100
TARGET_Y = 1200 * -100 # Y needs to be negative because the Y axis is inverted in blender compared to unreal engine.
TOLERANCE = 500.0 * 100

if __name__ == "__main__":
    main()
