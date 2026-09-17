import bpy
from pathlib import Path
import json
import os
from mathutils import Vector
print("---------------------------------------------------------")

FILE_EXTENSIONS = [
    "png",
    "tga"
]

PRO_MATERIALS = [
    "MI_Factory_01", # base name
    "Decal_Color",
    "Decal_Normal",
    "DecalColor_Masked",
    #"Glass_Inst", # glass mat name
]

TEXTURE_KEY_WORDS = [
    "Atlas",
    "Mask_Factory_02",
    #"TX2D_",
]

TEXTURE_TYPE_WORDS = [
    "_N",
    "_Nor",
    "_MREO",
    "_Rough",
    "_Refl",
    "_RELF"
]

shader_groups = [
    "SatisfactoryToBlenderShader",
    "TX2D_Shader",
    "SF_display",
    "TX2D_tile_mix_B",
    "TX2D_tile_mix_N",
    "TX2D_tile_mix_R",
    "Rough_Multiplier",
    "MI_ConveyorBelt_PowerStrip_01",
    "Light_shader",
    "FallBack",
    "Beam_Logic"
]

def get_par_materials(sf_asset_export_path):
    missing_shaders = []
    for sg in shader_groups:
        if not bpy.data.node_groups.get(sg):
            missing_shaders.append(sg)
    
    if missing_shaders:
        return f"Shader groups not found in blender: {missing_shaders}"
    
    EXPORT_FILE_DIR = r"FactoryGame\Content"
    TX_EXPORT_FILE_DIR = r"Exports\FactoryGame\Content"
    BASE_FILE_DIR = Path(sf_asset_export_path,EXPORT_FILE_DIR,"FactoryGame","Buildable")
    BASE_TEX_DIR = Path(sf_asset_export_path,TX_EXPORT_FILE_DIR,"FactoryGame","Buildable")
    ATLAS_MAT_DIR = Path(BASE_FILE_DIR,'-Shared') # textures and materials for the atlas materials (decal_color,decal_color_masked, decal_normal)
    ARR_TEX_DIR = Path(BASE_TEX_DIR,'-Shared','Material','Resources') # textures for the factory_inst material

    mat_dir = Path(ATLAS_MAT_DIR,'Material')
    tex_dir = Path(ATLAS_MAT_DIR,'Texture')

    cleared_txd_Shader = False
    for mat in PRO_MATERIALS:
        get_mat = bpy.data.materials.get(mat)
        
        material = get_mat if get_mat else bpy.data.materials.new(name=mat)

        material.use_nodes = True
        
        material.use_fake_user = True
        
        print(f"Material '{material.name}' created successfully with a Fake User!")
        
        try:
            mat_file = Path(mat_dir,f"{mat}.json")
            with open(mat_file, 'r', encoding='utf-8') as f:
                m_data = json.load(f)
                
            print("getting mat tex")    
            mat_tex = m_data["Textures"]
            mat_color_data = m_data["Parameters"]["Colors"]
        except Exception as e:
            print("Error opening material file: ",e)
            return f"Error opening material file: {Path(mat_dir,f"{mat}.json")}: {e}"
        
        
        pos = 0
        if not material.node_tree:
            print(f"Material '{material.name}' does not have a node tree. Skipping material.")
            continue
        material.node_tree.nodes.clear()
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        for tex in mat_tex:
            if "TX2D_" in tex:
                txd_Shader_node = nodes.new('ShaderNodeGroup')
                if txd_Shader_node:
                    txd_Shader_node.node_tree = bpy.data.node_groups['TX2D_Shader']
                txd_Shader_node.location.x = -400
                
                txd_Shader = bpy.data.node_groups['TX2D_Shader']
                if not cleared_txd_Shader:
                    txd_Shader_links = txd_Shader_node.node_tree.links
                    txd_Shader.nodes.clear()
                    cleared_txd_Shader = True
                
                    txd_Shader_out = txd_Shader.nodes.new('NodeGroupInput')
                    txd_Shader_out.location.x = -600
                    txd_Shader_in = txd_Shader.nodes.new('NodeGroupOutput')
                    txd_Shader_in.location.x = 300
                #txd_Shader_mapping_node = txd_Shader.nodes.new('ShaderNodeMapping')
                #txd_Shader_mapping_node.location.x = -600
                #txd_Shader_mapping_node.vector_type = 'TEXTURE'
                break
        
        tex_coord_node = nodes.new('ShaderNodeTexCoord')
        tex_coord_node.location.x = -800
        mapping_node = nodes.new('ShaderNodeMapping')
        mapping_node.location.x = -600
        mapping_node.vector_type = 'POINT'
        sf_shader_node = nodes.new('ShaderNodeGroup')
        if bpy.data.node_groups.get("SatisfactoryToBlenderShader"):
            sf_shader_node.node_tree = bpy.data.node_groups['SatisfactoryToBlenderShader']
            sf_shader_node.inputs["No AO?"].default_value = False
        else:
            sf_shader_node.node_tree = bpy.data.node_groups['FallBack']
        sf_shader_node.location.x = 500
        links.new(tex_coord_node.outputs["UV"], mapping_node.inputs["Vector"])
        links.new(mapping_node.outputs["Vector"], txd_Shader_node.inputs["UV"])
        
        output_node = nodes.new('ShaderNodeOutputMaterial')
        output_node.location.x = 700
        
        if "Decal_Normal" in mat:
            transparent_node = nodes.new('ShaderNodeBsdfTransparent')
            transparent_node.location.x = 200
            transparent_node.location.y = -200
                    
            mix_shader_node = nodes.new('ShaderNodeMixShader')
            mix_shader_node.location.x = 400
            mix_shader_node.location.y = 50
        else:
            links.new(sf_shader_node.outputs["Shader"], output_node.inputs["Surface"])
        
        
        tex_position_node_pos = 0
        tex_position_node_list = []
        tile_nodes_made = False
        tsd_shaders_made = False
        for tex in mat_tex:
            t_match = False
            for t in TEXTURE_KEY_WORDS:
                if t in tex:
                    print(f"{t} found in {tex}")
                        
                    t_match = True
                    break
                
            if "TX2D_" in tex:
                print("===================")
                print(F"{tex} is an array of 9 textures")
                
                sf_shader_node.location.x = -100
                output_node.location.x = 100
                
                #tex_scale = 3 # multiply texture by 3
                #tex_offset_x = 0 # move texture on x axis
                #tex_offset_y = 0 # move texture on y axis
                for i in range(3):
                    mapping_node.inputs[3].default_value[i] = 3
                
                if not tile_nodes_made:
                    tile_nodes_made = True
                    tile_pos_x = 0
                    tile_pos_y = -2
                    step = 0
                    for i in range(9):
                        #txd_Shader = bpy.data.node_groups['TX2D_Shader']
                        tex_position_node = txd_Shader.nodes.new('ShaderNodeVectorMath')
                        tex_position_node.operation = "ADD"
                        tex_position_node.label = "tile X"
                        tex_position_node.location.x = -400
                        txd_Shader_links.new(txd_Shader_out.outputs["UV"], tex_position_node.inputs["Vector"])
                        
                        if tile_pos_x < -2:
                            tile_pos_x = 0
                        tex_position_node.inputs[1].default_value[1] = tile_pos_y
                        tex_position_node.inputs[1].default_value[0] = tile_pos_x
                        
                        tex_position_node.location.y = 0-tex_position_node_pos*50
                        tex_position_node.hide = True
                        tex_position_node_list.append(tex_position_node)
                        tex_position_node_pos += 1
                        tile_pos_x -= 1
                        step += 1
                        if step == 3:
                            
                            step = 0
                            tile_pos_y += 1
                
                tx2D_tile_mix = ""
                if "_N" in tex:
                    tx2D_tile_mix = "TX2D_tile_mix_N"
                elif "_MREO" in tex:
                    tx2D_tile_mix = "TX2D_tile_mix_R"
                else:
                    tx2D_tile_mix = "TX2D_tile_mix_B"
                
                txd_shader_node = txd_Shader.nodes.new('ShaderNodeGroup')
                txd_shader_node.node_tree = bpy.data.node_groups[tx2D_tile_mix]

                #txd_shader_node.location.x = 200
                txd_shader_node.location.x = 100
                txd_shader_node.location.y = 0-(pos*50)
                
                for i in range(9):
                    tex_id = f"{tex}_{i}"
                    tex_file = Path(ARR_TEX_DIR,f"{tex_id}.png")
                    
                    print("---")
                    if not tex_file.exists():
                        print(f"Error: texture does not exist: {tex_file}")
                        continue
                    try:
                    
                        x = -200
                        y = 0-(pos*50)
                        
                        pos += 1
                        img_list = [img.name for img in bpy.data.images]
                        
                        # loading texture
                        b_texture = txd_Shader.nodes.new('ShaderNodeTexImage')
                        b_texture.hide = True
                        b_texture.extension = 'CLIP'
                        b_texture.location = Vector((x,y))
                        img = bpy.data.images.get(f"{tex_id}.png")
                        if img:
                            print("img in blend file")
                            b_texture.image = img
                        else:
                            print("img not in blend file")
                            b_texture.image = bpy.data.images.load(os.fspath(tex_file))
                        
                        for t in TEXTURE_TYPE_WORDS:
                            if t in tex_id:
                                if b_texture.image.colorspace_settings:
                                    b_texture.image.colorspace_settings.name = 'Linear Rec.709'
                        
                        txd_Shader_links.new(tex_position_node_list[i].outputs["Vector"], b_texture.inputs["Vector"])
                        txd_Shader_links.new(b_texture.outputs["Color"], txd_shader_node.inputs[f"tile {i+1}"])
                        sf_tile = ""
                        if "_N" in tex_id:
                            sf_tile = "Normal/Nor/N"
                        elif "_MREO" in tex_id:
                            sf_tile = "Relf/MREA"
                        else:
                            sf_tile = "Color/BC/Albedo"
                            sf_shader_node.inputs["No AO?"].default_value = False
                            sf_shader_node.inputs["No Paint Finish?"].default_value = False
                            txd_Shader_links.new(txd_shader_node.outputs["AO"], txd_Shader_in.inputs["AO"])
                            links.new(txd_Shader_node.outputs["AO"], sf_shader_node.inputs["AO/IDMask"])
                        txd_Shader_links.new(txd_shader_node.outputs["Result"], txd_Shader_in.inputs[sf_tile])
                        links.new(txd_Shader_node.outputs[sf_tile], sf_shader_node.inputs[sf_tile])
                        
                        #links.new(txd_Shader_node.outputs["Result"], txd_Shader_in.inputs[sf_tile])
                        
                        
                        print(f"Finished loading {tex_id}")
                        print("----------------")
                    except Exception as e:
                        print("Error loading texture: ",e)
                print("===================>")
                
                    
            if t_match:
                if "Decal_Normal" in mat:
                    if not tsd_shaders_made:
                        tsd_shaders_made = True
                        txd_mapping_node = nodes.new('ShaderNodeMapping')
                        txd_mapping_node.location.x = -600
                        txd_mapping_node.location.y = 380
                        txd_mapping_node.vector_type = 'POINT'
                        for i in range(3):
                            txd_mapping_node.inputs[3].default_value[i] = 3
                        
                        txd_Shader_node = nodes.new('ShaderNodeGroup')
                        txd_Shader_node.node_tree = bpy.data.node_groups['TX2D_Shader']
                        txd_Shader_node.location.y = 200
                        txd_Shader_node.location.x = -400
                        
                        txd_Shader = bpy.data.node_groups['TX2D_Shader']
                    
                        uv_fact_node = nodes.new('ShaderNodeAttribute')
                        uv_fact_node.location.x = -800
                        uv_fact_node.location.y = 200
                        uv_fact_node.attribute_name = "UVMapFact"
                    
                    sf_shader_node.inputs["No AO?"].default_value = False
                    sf_shader_node.inputs["No Paint Finish?"].default_value = False
                    
                    sf_shader_node.location.x = 200
                    sf_shader_node.location.y = 300
                    
                    links.new(transparent_node.outputs["BSDF"], mix_shader_node.inputs["Shader"])
                    links.new(sf_shader_node.outputs["Shader"], mix_shader_node.inputs[2])
                    links.new(mix_shader_node.outputs["Shader"], output_node.inputs["Surface"])
                    
                    links.new(uv_fact_node.outputs["Vector"], txd_mapping_node.inputs["Vector"])
                    links.new(txd_mapping_node.outputs["Vector"], txd_Shader_node.inputs["UV"])
                    links.new(txd_Shader_node.outputs["Color/BC/Albedo"], sf_shader_node.inputs["Color/BC/Albedo"])
                    links.new(txd_Shader_node.outputs["AO"], sf_shader_node.inputs["AO/IDMask"])
                    links.new(txd_Shader_node.outputs["Relf/MREA"], sf_shader_node.inputs["Relf/MREA"])
                    
                    
                
                print(f"{tex} in TEXTURE_KEY_WORDS")
                
                if "Mask_Factory_02" == tex:
                    tex_file = Path(tex_dir,'Factory',f"{tex}.png")
                else:
                    tex_file = Path(tex_dir,f"{tex}.png")
                
                print("---")
                if not tex_file.exists():
                    print(f"Error: texture does not exist in directory: {tex_file}")
                    continue
                
                try:
                    
                    b_texture = material.node_tree.nodes.new('ShaderNodeTexImage')
                    x = -200
                    y = 0-(pos*50)
                    pos += 1
                    b_texture.location = Vector((x,y))
                    img_list = [img.name for img in bpy.data.images]
                    img = bpy.data.images.get(f"{tex}.png")
                    if img:
                        print("img in blend file")
                        b_texture.image = img
                    else:
                        print("img not in blend file")
                        b_texture.image = bpy.data.images.load(os.fspath(tex_file))
                    b_texture.hide = True
                    for t in TEXTURE_TYPE_WORDS:
                        if t in tex:
                            if b_texture.image.colorspace_settings:
                                b_texture.image.colorspace_settings.name = 'Linear Rec.709'
                    
                    links.new(mapping_node.outputs["Vector"], b_texture.inputs["Vector"])
                    #if not img:
                    #    print(f"Error: texture image not found: {tex_file}")
                    #    continue
                    if "MI_Factory_01" in mat:
                        if "Mask_Factory_02" in tex:
                            b_texture.location.y = 100
                            b_texture.location.x = -400
                    if "Decal_Normal" in mat:
                        sf_shader_node.inputs["No AO?"].default_value = False
                        if "_Mask" in tex:
                            links.new(b_texture.outputs["Color"], mix_shader_node.inputs[0])
                    
                    if "Decal_Color" in mat or "DecalColor_Masked" in mat:
                        if "ColorAtlas_Alb" in tex:
                            sf_shader_node.inputs["No AO?"].default_value = False
                            sf_shader_node.inputs["Alpha?"].default_value = True
                            sf_shader_node.inputs["No Paint Finish?"].default_value = True
                            links.new(b_texture.outputs["Alpha"], sf_shader_node.inputs["Albedo Alpha"])
                    
                    sf_tile = ""
                    if "_N" in tex:
                        sf_tile = "Normal/Nor/N"
                    elif "_MREO" in tex or "_R" in tex:
                        sf_tile = "Relf/MREA"
                    elif "_Mask" in tex or "_A" in tex:
                        sf_tile = "Color/BC/Albedo"
                    links.new(b_texture.outputs["Color"], sf_shader_node.inputs[sf_tile])
                    
                    print(f"Finished loading {tex}")
                    print("----------------")
                except Exception as e:
                    print("Error loading texture: ",e)