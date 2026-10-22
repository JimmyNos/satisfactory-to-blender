import bpy
from pathlib import Path
import json
import os
from mathutils import Quaternion, Matrix, Vector


def get_materials(ob,obj_material: str,index:int,sf_asset_export_path:str):
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
        "Moss":"Top Vector",
        "Puddles":"Top Vector",
        "Soil":"Top Vector",
        "Gravel":"Top Vector",
        "Cliff_Sediment_Alb":"Vector",
        "TX_DesertRock_Cracked_01":"Vector",
        "DesertRock_Rough_01":"Vector",
        "FlatRock":"Vector",
    }
    
    detail_normal_tex = [
        "TX_DesertRock_Cracked_01_normal",
        "TX_DesertRock_Rough_01_normal",
        "TX_CliffRock_A_2x2_1K_normal",
        "Cliff_Sediment_Nor",
        "CliffSediment_Nor",
        "TX_Arc_Rock_N",
        "TX_Arc_Inside_N",
    ]
    
    bark_mats = [
        "_Bark"
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
                    if "_Grass" not in obj_material and "_Sand" not in obj_material and "_RedJungle" not in obj_material: 
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
        if "Cliff" in obj_material or "DesertRock" in obj_material:
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
                            if "Desert" in detail and not "Desert" in obj_material:
                                continue
                            is_detail_normal = True
                            links.new(tiling_shader_node.outputs["Vector"], b_texture.inputs["Vector"])
                            links.new(b_texture.outputs["Color"], sf_env_shader_node.inputs["Normal/Nor/N top"])
                    if is_detail_normal:    
                        continue
                if "Flat" in tex_file.name:#"Desert" in tex_file.name or "Flat" in tex_file.name:
                    continue
                if "Sand" in tex_file.name or "RedJungle" in tex_file.name or "Grass_01" in tex_file.name:
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
                        if "Bark" in tex_file.name or "FieldFlower" in tex_file.name or "SnailBottom" in tex_file.name:
                            sf_env_shader_node.inputs["Bark ORMA?"].default_value = True
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


sf_asset_export_path = r"F:\blenber\SF to blend\fmodel export"
collection_name = "prototypes" # replace with the actual collection name
get_singal_coll = False

file_name = "HLODInstancedStaticMeshComponent_2307"
ob = bpy.data.objects.get(file_name)
if ob != None:
    obj_materials = [slot.material.name for slot in ob.material_slots if slot.material]
    print(f"Materials on {ob.name}: {obj_materials}")
    
    for i,mat in enumerate(obj_materials):
        mat_trim = mat#.split('_G')[0]
        mat_results = get_materials(ob,mat_trim,i,sf_asset_export_path)
        if mat_results == None:
            print(f"got {mat_trim} material for {ob}")
            

# If you want to process all objects in a specific collection:
collection_name = "prototypes" # replace with the actual collection name
collection = bpy.data.collections.get(collection_name)

processed_materials = []
for col in bpy.data.collections:
    #if col.name.startswith("Persistent Level"):
    if collection and get_singal_coll:
        for obj in collection.all_objects:
            if obj.type == 'MESH':
                obj_materials = [slot.material.name for slot in obj.material_slots if slot.material]
                print(f"Materials on {obj.name}: {obj_materials}")
                
                for i,mat in enumerate(obj_materials):
                    mat_results = get_materials(obj,mat,i,sf_asset_export_path)
                    if mat_results == None:
                        print(f"got {mat} material for {obj}")
        break
    
    # Models instanced are in the prototypes collection.
    elif col.name.startswith("prototypes"):
        for obj in col.all_objects:
            if obj.type == 'MESH':
                obj_materials = [slot.material.name for slot in obj.material_slots if slot.material]
                print(f"Materials on {obj.name}: {len(obj_materials)}")
        
                for i,mat in enumerate(obj_materials):
                    if mat not in processed_materials:
                        mat_results = get_materials(obj,mat,i,sf_asset_export_path)
                        if mat_results == None:
                            processed_materials.append(mat)
                            print(f"got {mat} material for {obj}")
                    else:
                        print(f"{mat} already processed")
    #break
else:
    print(f"Collection '{collection_name}' not found.")

print(f"Processed {len(processed_materials)} materials")