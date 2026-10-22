import json
import os
from pathlib import Path
from typing import Any, List, Tuple
import time
import bpy


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
for file_path in sorted(FOLDER_PATH.rglob("0AV6HKSV1RYKUP3THFOHKNUQT.json")):
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
            
            break
    
    models_col = bpy.data.collections.get("models")
    if not models_col:
        models_col = bpy.data.collections.new("models")
        bpy.context.scene.collection.children.link(models_col)
        
    for model in models_used:
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