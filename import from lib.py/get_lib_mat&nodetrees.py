import os
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

# Set the absolute path to the source .blend file
blend_file_path = r"F:\blenber\SF to blend\SF-2-Blender addon\satisfactory-to-blender\SF Assets blend\SF Assets1.blend"

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
    
    {"Collection": "test_col"},
]
as_col = get_or_create_collection("Assets")
if os.path.exists(blend_file_path):
    for asset in assets:
        for data_block_type, object_name in asset.items():
            inner_path = data_block_type
            
            if object_name in bpy.data.materials or object_name in bpy.data.node_groups or object_name in bpy.data.collections:
                #remove the existing material or node group if it already exists
                if object_name in bpy.data.materials:
                    for mat in bpy.data.materials:
                        if mat.name.startswith("MI_SignBackground"):
                            bpy.data.materials.remove(mat, do_unlink=True)
                    bpy.data.materials.remove(bpy.data.materials[object_name], do_unlink=True)
                elif object_name in bpy.data.node_groups:
                    bpy.data.node_groups.remove(bpy.data.node_groups[object_name], do_unlink=True)
                elif object_name in bpy.data.collections:
                    bpy.data.collections.remove(bpy.data.collections[object_name], do_unlink=True)
                # purge the orphan data blocks to free up memory
                bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
                print(f"{object_name} already exists in the current Blender session.")
            
            
            #append all materials that start with "MI_SignBackground" from the source .blend file
            if object_name == "MI_SignBackground":
                with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
                    for mat_name in data_from.materials:
                        if mat_name.startswith("MI_SignBackground_") and not "." in mat_name:
                            data_to.materials.append(mat_name)
                            print(f"Appended material: {mat_name}")
                continue
                
            # Execute the append operation
            bpy.ops.wm.append(
                filepath=os.path.join(blend_file_path, inner_path, object_name),
                directory=os.path.join(blend_file_path, inner_path),
                filename=object_name,
                clear_asset_data =True
            )
            
            if object_name in bpy.data.collections:
                as_col.children.link(bpy.data.collections[object_name])
                bpy.context.scene.collection.children.unlink(bpy.data.collections[object_name])
                view_layer = bpy.context.view_layer
                sc_col = view_layer.layer_collection
                sc_col.children[as_col.name].children[object_name].exclude = True



