import bpy
from pathlib import Path
import json
import os
from mathutils import Quaternion, Matrix, Vector


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
        "ubkmehzya",
        "MI_TitanTreeLeaves_01"
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


sf_asset_export_path = r"F:\blenber\SF to blend\fmodel export"
collection_name = "prototypes" # replace with the actual collection name
get_singal_coll = False

mat_trim = "MI_GrassTuftDry_01"
mat_trim = "MI_CraterGrass_01"
mat_trim = "MI_Grass_01"
mat_trim = "MI_Grass_03"
mat_trim = "MI_DryGrassStraws_01"
mat_trim = "MI_Grass_Pink_01"
mat_trim = "MI_TallGrass_01_Dry"
#mat_trim = "MI_Grass_BigTuft_01"

b_material = bpy.data.materials.get(mat_trim)
if not b_material:
    bpy.data.materials.new(mat_trim)
    
mat_results = get_materials(obj_material=mat_trim,sf_asset_export_path=sf_asset_export_path)
if mat_results == None:
    print(f"got {mat_trim} material")

#file_name = "HLODInstancedStaticMeshComponent_2307"
#ob = bpy.data.objects.get(file_name)
#if ob != None:
#    obj_materials = [slot.material.name for slot in ob.material_slots if slot.material]
#    print(f"Materials on {ob.name}: {obj_materials}")
#    
#    for i,mat in enumerate(obj_materials):
#        mat_trim = mat#.split('_G')[0]
#        mat_results = get_materials(ob,mat_trim,i,sf_asset_export_path)
#        if mat_results == None:
#            print(f"got {mat_trim} material for {ob}")
#            

# If you want to process all objects in a specific collection:
#collection_name = "prototypes" # replace with the actual collection name
#collection = bpy.data.collections.get(collection_name)
#
#processed_materials = []
#for col in bpy.data.collections:
#    #if col.name.startswith("Persistent Level"):
#    if collection and get_singal_coll:
#        for obj in collection.all_objects:
#            if obj.type == 'MESH':
#                obj_materials = [slot.material.name for slot in obj.material_slots if slot.material]
#                print(f"Materials on {obj.name}: {obj_materials}")
#                
#                for i,mat in enumerate(obj_materials):
#                    mat_results = get_materials(obj,mat,i,sf_asset_export_path)
#                    if mat_results == None:
#                        print(f"got {mat} material for {obj}")
#        break
#    
#    # Models instanced are in the prototypes collection.
#    elif col.name.startswith("prototypes"):
#        for obj in col.all_objects:
#            if obj.type == 'MESH':
#                obj_materials = [slot.material.name for slot in obj.material_slots if slot.material]
#                print(f"Materials on {obj.name}: {len(obj_materials)}")
#        
#                for i,mat in enumerate(obj_materials):
#                    if mat not in processed_materials:
#                        mat_results = get_materials(obj,mat,i,sf_asset_export_path)
#                        if mat_results == None:
#                            processed_materials.append(mat)
#                            print(f"got {mat} material for {obj}")
#                    else:
#                        print(f"{mat} already processed")
#    #break
#else:
#    print(f"Collection '{collection_name}' not found.")

#print(f"Processed {len(processed_materials)} materials")