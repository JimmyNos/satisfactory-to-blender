import json
import os
from pathlib import Path
import random
from typing import Any, List, Tuple
import bpy
import time
from mathutils import Quaternion
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
                        o_mat = bpy.data.materials.get(i["OverrideMaterials"])
                        if not o_mat:
                            o_mat = bpy.data.materials.new(i["OverrideMaterials"])
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
