import json
import os
from pathlib import Path
import random
from typing import Any, List, Tuple
import bpy
import time
from mathutils import Quaternion,Vector

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
        "MI_FicsmasTree_Branches_01"
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
        "Forest":"Top Vector",
        "Moss":"Top Vector",
        "Puddles":"Top Vector",
        "Soil":"Top Vector",
        "Gravel":"Top Vector",
        "Cliff_Sediment_Alb":"Vector",
        "TX_DesertRock_Cracked_01":"Vector",
        "DesertRock_Rough_01":"Vector",
        "FlatRock":"Vector",
        "Arc_Rock":"Vector",
        "Arc_Inside":"Vector",
        "CaveFloor_Inst":"Vector",
        "OriginStaligtite":"Vector",
        "Cliff_Detail_Alb":"Vector",
        "Plateau1and3":"Vector",
        "MI_Bigshell_01":"Vector",
        "TX_TitanTree_TilingBark_N":"Vector",
        "MI_TitanTree_01":"Vector",
    }
    
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
    
    mat_path = None
    
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
    
    textures = [] # type: list[dict[str,str]] 
    switch_parameters = [] # type: list[dict[str,str]] 
    vec_parameters = [] # type: list[dict[str,dict]] 
    is_wrong_format = False
    is_cliff_mat = False
    for item in m_data:
        if is_wrong_format:
            break
        #print(item)
        if type(item) == str:
            if item == "Parameters":
                par_data = m_data[item]
                color_data = par_data.get("Colors")
                scalar_data = par_data.get("Scalars")
                switch_data = par_data.get("Switches")
            
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
            if item == "Textures":
                tex_data = m_data[item]
                for tex_name in tex_data:
                    if is_wrong_format:
                        break
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
                    
                    #if tex_data[tex_name]["ObjectPath"].split("/")[-1] not in detail_normal_tex:
                    #    if "desert" in tex_name.lower() and "desert" not in obj_material:
                    #        continue
                    #
                    #t_name_parts = tex_data[tex_name]["ObjectPath"].split("/")[-1].split("_")
                    #obj_material_parts = tex_name.split("_")
                    #if tex_name not in detail_normal_tex:
                    #    for p in t_name_parts:
                    #        if "cliff" in p.lower() and p not in obj_material.lower():
                    #            if "Foliage" not in tex_data[tex_name]["ObjectPath"]:
                    #                skip_tex = True
                    #                break
                    #
                    #
                    #
                    #if "Foliage" in tex_data[tex_name]["ObjectPath"]:
                    #    for p in t_name_parts:
                    #        if p == "TX" or p == "T" or p.lower() == "mask":
                    #            continue
                    #        if p.lower() in obj_material.lower():
                    #            break
                    #        if "tree" in p.lower() and p.lower() not in obj_material.lower():
                    #            skip_tex = True
                    #            break
                    #        if mapping_tex.get(p,p).lower() in obj_material.lower():
                    #            break
                    #        if p not in obj_material:
                    #            skip_tex = True
                    #            break
                            
                    
                    
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
                    
                    if "Moss" in tex_path and "_Moss" not in obj_material:
                        if parameters["Moss "][0] == False:
                            print("skipping moss tex",tex_name)
                            continue
                    
                    is_exclude = False
                    for exc in exclude_tex:
                        if exc in tex_path:
                            is_exclude = True
                            print("skipping ",tex_name)
                            break
                    if is_exclude:
                        continue
                    if "_Grass" not in obj_material and "_Sand" not in obj_material and "_RedJungle" not in obj_material and "Desert" not in obj_material: 
                        if "Sand" in tex_path or "RedJungle" in tex_path or "Grass_01" in tex_path:
                            print("skipping ",tex_name)
                            continue
                    if "_Grass" in obj_material:
                        if "Sand" in tex_name or "RedJungle" in tex_name:
                            print("skipping ",tex_name)
                            continue
                    
                    if "_Sand" in obj_material:
                        if "Grass_01" in tex_name or "RedJungle" in tex_name:
                            print("skipping ",tex_name)
                            continue
                    
                    if "_RedJungle" in obj_material:
                        if "Sand" in tex_name or "Grass_01" in tex_name:
                            print("skipping ",tex_name)
                            continue
                    
                    is_dup = False
                    for t in textures:
                        for dt in t:
                            if tex_path[6:].split('.')[0] in t[dt]:
                                is_dup = True
                    if not is_dup:
                        textures.append(
                            {tex_name:tex_path[6:].split('.')[0]}
                        )
            print(textures)
            
        continue
        is_tpv = False
        if item.get("Properties"):
            props = item.get("Properties")
            if props.get("Parent"):
                # default to Factory_01 material if TX2D_ textures found
                if "MI_Factory_Base" in props["Parent"]["ObjectName"]: 
                    #ob.material_slots[index].material = fact_mat
                    print("MI_Factory_Base in mat name")
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
            sf_env_shader_node.node_tree = bpy.data.node_groups['FallBack']
        sf_env_shader_node.location.x = 200
        links.new(sf_env_shader_node.outputs["Shader"], output_node.inputs["Surface"])
        
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
        if "Cliff" in obj_material or "DesertRock" in obj_material or any(ut in obj_material for ut in use_tiling):
            if is_cliff_mat:
                sf_env_shader_node.inputs["Cliff Relf?"].default_value = True
            tiling_shader_node = nodes.new('ShaderNodeGroup')
            if bpy.data.node_groups.get("Tiling"):
                tiling_shader_node.node_tree = bpy.data.node_groups['Tiling']
                tiling_shader_node.location.x = -400
            if "_Grass" in obj_material or "_Sand" in obj_material or "_RedJungle" in obj_material:
                sf_env_shader_node.inputs["Use Top?"].default_value = True
                
        pos = 0
        
        for tex in textures:
            tex_type = ""
            tex_path = ""
            for tt,tp in tex.items(): #should only have one item {texture type: texture path}
                tex_type = tt # type: str
                tex_path = tp # type: str
            
            exports_path = Path(sf_asset_export_path,"FactoryGame","Content")
            tex_file = Path(exports_path,f"{tex_path}.png")    
            if not tex_file.exists():
                print(f"Error: texture does not exist in search folder: {tex_file}")
                continue
            
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
                for mt in mirrored_tex:
                    if mt in obj_material:#tex_file.name:
                        if "TX_Stencils" not in tex_file.name:
                            b_texture.extension = 'MIRROR'
                for t in rn_type_tex:
                    if t in tex_type or t in tex_file.name:
                    #if '_N' in tex_file.name or 'Refl' in tex_file.name:
                        b_texture.image.colorspace_settings.name = 'Linear Rec.709'
                
                is_detail_normal = False
                if tiling_shader_node:
                    for tile in use_tiling:
                        if tile in tex_file.name:
                            links.new(tiling_shader_node.outputs[use_tiling[tile]], b_texture.inputs["Vector"])
                    
                    #links.new(tiling_shader_node.outputs["Vector"], b_texture.inputs["Vector"])
                    for detail in detail_normal_tex:
                        if detail in tex_file.name:
                            if "Desert" in detail and "Cliff_Sediment_Alb" in textures:
                                continue
                            is_detail_normal = True
                            links.new(tiling_shader_node.outputs["Vector"], b_texture.inputs["Vector"])
                            links.new(b_texture.outputs["Color"], sf_env_shader_node.inputs["Normal/Nor/N top"])
                    if is_detail_normal:    
                        continue
                if "FlatRock" in tex_file.name:#"Desert" in tex_file.name or "Flat" in tex_file.name:
                    continue
                if "Sand" in tex_file.name or "RedJungle" in tex_file.name or "Grass_01" in tex_file.name or "Forest" in tex_file.name:
                    if "Desert" in obj_material:
                        sf_env_shader_node.inputs["Use AO Mask?"].default_value = True
                    if "_ORMA" in tex_file.name:
                        sf_env_shader_node.inputs["Top ORMA?"].default_value = True
                
                    if "_HRA" in tex_file.name:
                        sf_env_shader_node.inputs["Top HRA?"].default_value = True
                
                    for ua in uses_alpha:
                        if ua in b_material.name:
                            continue
                
                    tx_type = ""
                    tx_type_a = ""
                
                    if "_N" in tex_file.name or "N" in tex_type:
                        if "wet" not in tex_file.name.lower():
                            tx_type = "Top Normal/Nor/N"
                    if "_AO" in tex_file.name or "AO" in tex_type:
                        tx_type = "Top AO/IDMask"
                    for rt in rough_type_tex:
                        if rt in tex_file.name or rt in tex_type:
                            tx_type = "Top Relf/MREA"
                            tx_type_a = tx_type+" Alpha"
                            b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                        if "_MREA" in tex_file.name:
                            sf_env_shader_node.inputs["Top Relf or MREA??"].default_value = True
                    for bc in color_type_tex:
                        if bc in tex_file.name or bc in tex_type:
                            tx_type = "Top Color/BC/Albedo"
                            tx_type_a = "Top Albedo Alpha"
                            b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                
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
                    
                    for ua in uses_alpha:
                        if ua in b_material.name:
                            continue
                            
                    tx_type = ""
                    tx_type_a = ""
                    
                    if "_N" in tex_file.name or "N" in tex_type:
                        tx_type = "Normal/Nor/N"
                    if "_AO" in tex_file.name or "AO" in tex_type:
                        tx_type = "AO/IDMask"
                    for rt in rough_type_tex:
                        if rt in tex_file.name or rt in tex_type:
                            for nt in nor_type_tex:
                                if nt not in tex_file.name and nt not in tex_type:
                                    
                                    tx_type = "Relf/MREA"
                                    tx_type_a = tx_type+" Alpha"
                                    b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                        if "_MREA" in tex_file.name:
                            sf_env_shader_node.inputs["Relf or MREA?"].default_value = True
                    for bc in color_type_tex:
                        if bc in tex_file.name or bc in tex_type:
                            tx_type = "Color/BC/Albedo"
                            tx_type_a = "Albedo Alpha"
                            b_texture.image.alpha_mode = 'CHANNEL_PACKED'
                    
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
                
            if "Translation" in data :
                translation = data["Translation"]
                
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
    print(f"Found {matched_files} file(s) with close Translation/X or Translation/Y values.")
    
    print(f"Importing {len(import_files)} files into Blender...")
    
    
    
    for un in umap_names:
        file_path = Path(FOLDER_PATH,un+".json")

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        umap_dict.update({
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
            if u_type == 2:
                break
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
                    else:
                        actor_props = actor_data["Properties"]
                        actor_type = actor_data["Type"]
                        if any(ex in actor_type for ex in exclude_actors):
                            ex_dump.append(actor_type)
                            continue
                        if actor_type.startswith("BP_"):
                            asd
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
                    if not mesh:
                        continue
                    
                    models_used.update({
                        mesh["ObjectName"].split("'")[1]:mesh["ObjectPath"].split('.')[0]
                    })
                    if instance_props.get("TranslatedInstanceSpaceOrigin"):
                        translations = instance_props["TranslatedInstanceSpaceOrigin"]
                    elif instance_props.get("RelativeLocation"):
                        translations = instance_props["RelativeLocation"]
                    else:
                        translations = None # replace if more translations found
                    rotation = None # replace if more translations found
                    scale = None # replace if more translations found
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
                                        "OverrideMaterials" : override_materials
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
        
        
        
        if umap_type[file_path.stem] == 2:
            usd_file_path = import_files[file_path.stem]
            #break
            umap_name = usd_file_path.parent.name
        
        
            umap_col = bpy.data.collections.get(umap_name)
            #if map_col.children.get(umap_name):
            #    print(f"Removing existing collection: {umap_name}")
            #    bpy.data.collections.remove(umap_col)
            #    umap_col = bpy.data.collections.new(umap_name)
            #    map_col.children.link(umap_col)
            if not umap_col:
                umap_col = bpy.data.collections.new(umap_name)
                #bpy.context.scene.collection.children.link(umap_col)
                type_col.children.link(umap_col)
        
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[map_col.name].children[type_col.name].children[umap_col.name]
        
            bpy.ops.wm.usd_import(
                filepath=str(usd_file_path),
                import_materials=True,
                import_meshes=True,
                import_volumes=True,
                scale=1.0,
                read_mesh_uvs=True,
                read_mesh_colors=True,
                read_mesh_attributes = True,
                import_textures_mode  = 'IMPORT_NONE',
                mtl_name_collision_mode = 'REFERENCE_EXISTING',
                support_scene_instancing = True,
                mtl_purpose = 'MTL_FULL',
                import_skeletons=True,
                import_blendshapes=True,
                import_shapes =True,
                #create_collection=True,
                set_frame_range = False,
            )
        
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
            if not point_positions:
                continue
            mesh = bpy.data.meshes.new(f"{file_path.stem+"_"+i["mesh"]}_Points")
            mesh.from_pydata(point_positions, [], [])
            # object from the mesh
            point_obj = bpy.data.objects.new(f"{file_path.stem+"_"+i["mesh"]}_Points", mesh)
            if ob_parent:
                point_obj.parent = ob_parent
        
            if has_attr:
                mesh.attributes.new("scale", "FLOAT_VECTOR", "POINT")
                mesh.attributes["scale"].data.foreach_set("vector", scale_attr)
                mesh.attributes.new("rotation", "FLOAT_VECTOR", "POINT")
                mesh.attributes["rotation"].data.foreach_set("vector", rotation_attr)
        
            if bpy.data.node_groups.get("instance env"):
                node_group = bpy.data.node_groups["instance env"]
                mod = point_obj.modifiers.new(name="InstanceEnv", type="NODES")
                mod.node_group = node_group
                
                if ob_instance_mesh:
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
TARGET_X = 1000 * 100
TARGET_Y = 1000 * -100 # Y needs to be negative because the Y axis is inverted in blender compared to unreal engine.
TOLERANCE = 500.0 * 100

if __name__ == "__main__":
    main()
