import json
import os
from pathlib import Path
from typing import Any, List, Tuple
import time
import bpy
import sys

from PIL import Image

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

height_maps = {}



#for file_path in sorted(FOLDER_PATH.rglob("0C0EB0SNHH89X7G16DXI46BC3.json")):
#for file_path in sorted(FOLDER_PATH.rglob("1IRGQ236BGL3067IY2HJARLHO.json")):
count = 0
is_skip = False
for file_path in sorted(FOLDER_PATH.rglob("*.json")):
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    
    for item in data:
        i_type = item.get("Name")
        i_prop = item.get("Properties")
        if i_prop:
            for prop in i_prop:
                if "Mesh" in prop:
                    if type(i_prop[prop]) == dict and i_prop[prop].get("ObjectName"):
                        if "ResourceNode" in i_prop[prop]["ObjectName"]:
                            print(item)
    
    #continue
    umap_dict.update({
        file_path.stem:[]
    })
    
    land_umap_dict.update({
        file_path.stem:[]
    })
    
    
    #print(data[232])
    actor_indexes = []
    instance_indexes = []
    root_indexes = []
    
    umap_meshes = {}
    
    if "Audio" in data[0]["Name"]:
        continue
    
    for item in data:
        if is_skip:
            break
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
                    if "ResourceNode" in actor_data["Properties"]["StaticMeshComponent"]["ObjectName"]:
                        print(actor_data)
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

                #continue
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
                                    "OverrideMaterials" : override_materials,
                                    "instance_count" : instance_count,
                                    "instance_bounds":instance_bounds
                                }
                                )
                
                #print()
            
            break
    
    if land_umap_dict:
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
            
            sc_col = bpy.context.scene.collection
            col = bpy.data.collections.get(file_path.stem)
            col = bpy.data.collections.get("test_land")
            if not col:
                col = bpy.data.collections.new("test_land")
                bpy.context.scene.collection.children.link(col)
            
            if ob_parent:
                if sc_col in ob_parent.users_collection:
                    bpy.context.scene.collection.objects.unlink(ob_parent) 
            
                if col not in ob_parent.users_collection:
                    col.objects.link(ob_parent)
            
            if sc_col in point_obj.users_collection:
                bpy.context.scene.collection.objects.unlink(point_obj) 
            
            if col not in point_obj.users_collection:
                col.objects.link(point_obj)
    
    #continue
    models_col = bpy.data.collections.get("models")
    if not models_col:
        models_col = bpy.data.collections.new("models")
        bpy.context.scene.collection.children.link(models_col)
        
    for model in models_used:
        if "resource" in model.lower():
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
        
        if not ob:
            print(f"⚠️Error: {models_used[model]} did not import into blend file.")
            continue
        
        if models_col not in ob.users_collection:
            models_col.objects.link(ob)
        
    count = 0
    maxx = 10
    for i in umap_dict[file_path.stem]:
        count+=1
        if count == maxx:
            break
        
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
                rotation_attr.extend([
                    t["rotation"]["X"],
                    t["rotation"]["Y"],
                    t["rotation"]["Z"],
                    t["rotation"]["W"]
                ])
                scale_attr.extend([
                    t["scale"]["X"] / 100,
                    t["scale"]["Y"] / -100,
                    t["scale"]["Z"] / 100
                ])
                has_attr = True
        else:
            if i["transform"]["location"]:
                point_positions.append((
                    i["transform"]["location"]["X"] / 100.0,
                    i["transform"]["location"]["Y"] / 100.0,
                    i["transform"]["location"]["Z"] / 100.0
                    ))
            else:
                point_positions.append((
                    0.0,
                    0.0,
                    0.0
                    ))
        
        mesh = bpy.data.meshes.new(f"{file_path.stem+"_"+i["mesh"]}_Points")
        mesh.from_pydata(point_positions, [], [])
        # object from the mesh
        point_obj = bpy.data.objects.new(f"{file_path.stem+"_"+i["mesh"]}_Points", mesh)
        if ob_parent:
            point_obj.parent = ob_parent
        
        if has_attr:
            mesh.attributes.new("scale", "FLOAT_VECTOR", "POINT")
            mesh.attributes["scale"].data.foreach_set("vector", scale_attr)
            mesh.attributes.new("rotation", "QUATERNION", "POINT")
            mesh.attributes["rotation"].data.foreach_set("value", rotation_attr)
        
        
        if bpy.data.node_groups.get("instance env"):
            node_group = bpy.data.node_groups["instance env"]
            mod = point_obj.modifiers.new(name="InstanceEnv", type="NODES")
            mod.node_group = node_group
        
            if ob_instance_mesh:
                set_geonode_input(mod, "Use Culling", True)
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
        
        
        #node_group = bpy.data.node_groups["instance env"]
        #mod = point_obj.modifiers.new(name="InstanceEnv", type="NODES")
        #mod.node_group = node_group
        
        sc_col = bpy.context.scene.collection
        col = bpy.data.collections.get(file_path.stem)
        if not col:
            col = bpy.data.collections.new(file_path.stem)
            bpy.context.scene.collection.children.link(col)
            
        if ob_parent:
            if sc_col in ob_parent.users_collection:
                bpy.context.scene.collection.objects.unlink(ob_parent) 
        
            if col not in ob_parent.users_collection:
                col.objects.link(ob_parent)
        
        if sc_col in point_obj.users_collection:
            bpy.context.scene.collection.objects.unlink(point_obj) 
    
        if col not in point_obj.users_collection:
            col.objects.link(point_obj)
    #print()