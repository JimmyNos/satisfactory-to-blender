import os
from pathlib import Path
import bpy

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

#data block types ('Object', 'Collection', 'Material', etc.)
assets = [
    {"Material": "MI_Glass"},
    {"Material": "MI_Factory_01"},
    {"Material": "DecalColor_Masked"},
    {"Material": "Decal_Normal"},
    {"Material": "MI_SignBackground"},
    
    {"NodeTree": "Buildables from Points"},
    {"NodeTree": "Buildables from Points(signs)"},
    {"NodeTree": "Buildables From Spline"},
    {"NodeTree": "Conveyer Cains From Spline"},
    
    #{"Collection": "Assets"},
]

def get_lib_assets(data_type:str,asset_name:str = "",asset_lib_name:str = "SF Asset Lib",asset_lib_blend:str = "SF_Asset_Lib.blend") -> str:
    library_path = bpy.context.preferences.filepaths.asset_libraries.get(asset_lib_name).path
    as_col = get_or_create_collection("Assets")
    
    asset_lib_blend_path = os.path.join(library_path, asset_lib_blend)
    # get collections
    if os.path.exists(asset_lib_blend_path):
        if asset_name and data_type == "Collection":
            if asset_name in bpy.data.collections:
                bpy.data.collections.remove(bpy.data.collections[asset_name], do_unlink=True)
                # purge the orphan data blocks to free up memory
                bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
                print(f"{asset_name} already exists in the current Blender session.")    
            
            inner_path = data_type
            bpy.ops.wm.append(
                filepath=os.path.join(asset_lib_blend_path, inner_path, asset_name),
                directory=os.path.join(asset_lib_blend_path, inner_path),
                filename=asset_name,
                clear_asset_data =True
            )
            
            if asset_name in bpy.data.collections:
                as_col.children.link(bpy.data.collections[asset_name])
                bpy.context.scene.collection.children.unlink(bpy.data.collections[asset_name])
                view_layer = bpy.context.view_layer
                sc_col = view_layer.layer_collection
                sc_col.children[as_col.name].children[asset_name].exclude = True
            else:
                return f"Collection {asset_name} not found in the library: {asset_lib_blend_path}"
            
            return f"Appended {asset_name} from {asset_lib_blend_path}"

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        for asset in assets:
            for data_block_type, object_name in asset.items():
                if data_block_type != data_type:
                    continue
                
                if asset_name and object_name != asset_name:
                    continue
                
                inner_path = data_block_type
                
                if object_name in bpy.data.materials or object_name in bpy.data.node_groups or object_name in bpy.data.collections:
                    #remove the existing material or node group if it already exists
                    if object_name in bpy.data.materials:
                        for mat in bpy.data.materials:
                            if mat.name.startswith("MI_SignBackground"):
                                bpy.data.materials.remove(mat, do_unlink=True)
                        bpy.data.materials.remove(bpy.data.materials[object_name], do_unlink=True)
                        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
                    elif object_name in bpy.data.node_groups:
                        #bpy.data.node_groups[object_name].name = object_name + "_old"
                        #bpy.data.node_groups[object_name + "_old"].use_fake_user = False
                        #bpy.data.node_groups.remove(bpy.data.node_groups[object_name], do_unlink=True)
                        return f"{object_name} already exists in the current Blender session."
                    elif object_name in bpy.data.collections:
                        bpy.data.collections.remove(bpy.data.collections[object_name], do_unlink=True)
                        
                    print(f"{object_name} already exists in the current Blender session.")
                
                
                #append all materials that start with "MI_SignBackground" from the source .blend file
                if object_name == "MI_SignBackground":
                    with bpy.data.libraries.load(library_path, link=False) as (data_from, data_to):
                        for mat_name in data_from.materials:
                            if mat_name.startswith("MI_SignBackground_") and not "." in mat_name:
                                data_to.materials.append(mat_name)
                                print(f"Appended material: {mat_name}")
                    continue
                    
                # Execute the append operation
                bpy.ops.wm.append(
                    filepath=os.path.join(asset_lib_blend_path, inner_path, object_name),
                    directory=os.path.join(asset_lib_blend_path, inner_path),
                    filename=object_name,
                    clear_asset_data =True
                )
                
                if object_name in bpy.data.collections:
                    as_col.children.link(bpy.data.collections[object_name])
                    bpy.context.scene.collection.children.unlink(bpy.data.collections[object_name])
                    view_layer = bpy.context.view_layer
                    sc_col = view_layer.layer_collection
                    sc_col.children[as_col.name].children[object_name].exclude = True
        return f"Appended {data_type} assets from {asset_lib_blend_path}"
    else:
        return f"Blend file not found: {asset_lib_blend_path}"



