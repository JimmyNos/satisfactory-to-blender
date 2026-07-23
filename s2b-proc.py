import json

import bpy
from mathutils import Quaternion, Matrix, Vector
from pathlib import Path
import math
import satisfactory_save as s
import time
# start common types
Vec3 = tuple[float, float, float]
Vec4 = tuple[float, float, float, float]
# end common types

# start DMZ
# im having a hard time inspecting cpp wrapped objects so this helps...
def debug_obj(obj):
   
    if isinstance(obj, (int, float, str, bool, type(None))):
      print(obj)
      return
    
    import pydoc
    print(pydoc.render_doc(obj))
    
def debug_inspect(obj):
    import inspect

    print('---\ntype:', type(obj))
    print('repr:', repr(obj))
    print('attributes:')
    for name in dir(obj):
        if name.startswith("__"):
            continue
        try:
            value = getattr(obj, name)
            if inspect.ismethod(value) or inspect.isbuiltin(value) or inspect.isfunction(value):
                try:
                    print(f"  {name}{inspect.signature(value)}")
                except Exception:
                    print(f"  {name}(...)")
            else:
                print(f"  {name} = {value!r}")
        except Exception as e:
            print(f"  {name} = <error: {e}>")
    print('\n---\n')
# end DMZ


# start blender api

# geonode sockets have a surrogate id thats not the label, but we're not going to
# use the same label twice since that would be silly
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

def get_import_collection() -> bpy.types.Collection:
    return get_or_create_collection('Import')

def create_asset_collection() -> bpy.types.Collection:
    return get_or_create_collection('Assets')

def create_sign_text_collection(sign_name,parent_name = 'Import') -> bpy.types.Collection:
    return get_or_create_collection(sign_name,parent_name)

def create_weight_collection(buildable_name,parent_name = 'Import') -> bpy.types.Collection:
    return get_or_create_collection(buildable_name,parent_name)

def add_text_splines_to_curve(text: list, sign_name: str, text_n: int):
    """
    Generates spline geometry from a text string and appends 
    those splines directly into an existing curve object.
    """
    # TODO: use name of sign for text obj and collection name
    # a set of text to not create duplicate text obj
    # if a sign uses a text from the set, use idx as id
    text_dict = dict()
    text_set = set()
    text_id = []
    
    for t in text:
        text_set.add(t)
        
    for i, t in enumerate(text_set):
        text_dict[t] = i
    
    #print(text_set)
    #print(text_dict)
    #print(text)
    for t in text:
        #print(repr(l[0]))
        #print(test[l[0]])
        text_id.append(text_dict[t])
                
    #col_name = f"{sign_name}"
    text_set = set()
    text_length = len(text)
    for i,text_string in enumerate(text_dict):
        # Create a text curve object
        
        text_name = f"{sign_name}_TextBlock_{text_n}_{i}"
        text_data = bpy.data.curves.new(name=text_name, type='FONT')
        text_data.body = text_string
        text_obj = bpy.data.objects.new(text_name, text_data)

        
        col = create_sign_text_collection(f"{sign_name}_TextBlock_{text_n}",sign_name)
        col.objects.link(text_obj)
        col.hide_viewport
        col.hide_render
        
        
        # Link to the current collection to perform the conversion
        #current_collection = bpy.context.collection
        #current_collection.objects.link(text_obj)
    return text_id,col  
# end blender api


# start satisfactory api

# get the lightweight buildable system from the save
# mostly a type guard for my sanity
def get_lbs(save: s.SaveGame) -> s.AFGLightweightBuildableSubsystem:
    return save.getObjectsByPath(
        "Persistent_Level:PersistentLevel.LightweightBuildableSubsystem"
    )[0].Object


# read the buildale transform and convert to blender coords
def read_transform(transform: s.FTransform3f):

    t = transform.Translation
    # unreal is in CM with the Y inverted
    pos = t.X / 100.0, -t.Y / 100.0, t.Z / 100.0

    q = transform.Rotation
    # y is inverted, and the rotation is left handed, so invert W and Y
    quat = Quaternion((-q.W, q.X, -q.Y, q.Z))
    euler = quat.to_euler("XYZ")
    rot = euler.x, euler.y, euler.z

    # this isnt used since vanilla doesnt allow scaling, but include it for completeness
    s = transform.Scale3D
    scale = s.X, s.Y, s.Z

    return pos, rot, scale


def read_colors_custom(i: s.FRuntimeBuildableInstanceData| str) -> [Vec4, Vec4,int]:
    try:
        p = i.CustomizationData.OverrideColorData.PrimaryColor
        s = i.CustomizationData.OverrideColorData.SecondaryColor
        f_path = i.CustomizationData.OverrideColorData.PaintFinish.PathName
        
        if "Matte" in f_path:
            f = 6
        elif "Shiny" in f_path:
            f = 7
        else:
            f = 0
    except AttributeError:
        return ((1, 1, 1, 1), (1, 1, 1, 1),0)

    return ((p.R, p.G, p.B, p.A), (s.R, s.G, s.B, s.A), f)


def read_colors_swatch(i: s.FRuntimeBuildableInstanceData| str,color_map: dict) -> [Vec4, Vec4,int]:
    # todo swatch?
    if type(i) != str:
        swatch = color_map.get(str(i.CustomizationData.SwatchDesc.PathName).split('.')[-1], {})
    else:
        swatch = color_map.get(str(i).split('.')[-1], {})
        
    try:
        #print(swatch)
        p = swatch["PrimaryColor"]
        s = swatch["SecondaryColor"]
        
        # paint finish indexing for blender materials, easier to work with an index than a string in the geonode
        if "CarbonSteel" in swatch["PaintFinish"]:
            f = 1
        elif "Caterium" in swatch["PaintFinish"]:
            f = 2
        elif "Chrome" in swatch["PaintFinish"]:
            f = 3
        elif "Copper" in swatch["PaintFinish"]:
            f = 4
        elif "Unpainted" in swatch["PaintFinish"]:
            f = 5
        elif "Matte" in swatch["PaintFinish"]:
            f = 6
        elif "Shiny" in swatch["PaintFinish"]:
            f = 7
        else:
            f = 0
        #f = swatch["PaintFinish"] 
    except AttributeError:
        return ((1, 1, 1, 1), (1, 1, 1, 1),0)
    except Exception as e:
        print(f"err setting color: {e}")
        return ((1, 1, 1, 1), (1, 1, 1, 1),0)
    return ((p["R"], p["G"], p["B"], p["A"]), (s["R"], s["G"], s["B"], s["A"]),f)


def read_colors(i: s.FRuntimeBuildableInstanceData| str,color_map: dict) -> [Vec4, Vec4,int]:
    # custom colors use the swatch "...SwatchDesc_Custom_C"
    #print(type(i))
    if type(i) == s.FRuntimeBuildableInstanceData:
        if "SwatchDesc_Custom_C" in i.CustomizationData.SwatchDesc.PathName:
            return read_colors_custom(i)
    else:
        if "SwatchDesc_Custom_C" in i:
            return read_colors_custom(i)

    # todo swatch
    if type(i) == str:
        return read_colors_swatch(i,color_map)
    return read_colors_swatch(i,color_map)
    

def read_sign_colors(color_attr:dict) -> [Vec4, Vec4, Vec4]:
    try:
        f = color_attr['mForegroundColor']
        b = color_attr['mBackgroundColor']
        
        if 'mAuxilaryColor' in color_attr:
            a = color_attr['mAuxilaryColor'] 
        else: 
            a = None
    except AttributeError:
        return ((1, 1, 1, 1), (1, 1, 1, 1),(1, 1, 1, 1))
    
    if a:
        return ((f["R"], f["G"], f["B"], f["A"]), 
                (b["R"], b["G"], b["B"], b["A"]),
                (a["R"], a["G"], a["B"], a["A"]))
    else:
        return ((f["R"], f["G"], f["B"], f["A"]), 
                (b["R"], b["G"], b["B"], b["A"]),
                None)

def read_length(i: s.FRuntimeBuildableInstanceData) -> float:
    for property in i.TypeSpecificData.StructInstance:
        if property.Name.Name == "BeamLength":
            return property.Value / 100  # convert to m

    return 0


# end satisfactory api

# start geonode

# map make buildable classes to corrisponding asset
def buildable_class_to_object(cls: str) -> [bpy.types.Object,Vec3,Vec3]:# | None:
    json_file_path = mapping_path
    with open(json_file_path, 'r', encoding='utf-8') as f:
        map = json.load(f)

    name = map.get(cls)
    
    if "Build_PipelinePumpMk2" in cls:
        name = map.get("Build_PipelinePumpMK2_C")
    if name is None:
        print(f"Missing object mapping: {cls}")
        return None
    
    mesh = name.get("ObjectName")
    
    print(f"found object mapping: {cls}")
    print(f"object mapping name: {mesh}")
    
    #quat = Quaternion((-name["rotation"]["W"], name["rotation"]["X"],-name["rotation"]["Y"], name["rotation"]["Z"]))
    #euler = quat.to_euler("XYZ")
    rot = (0, 0, 0)# euler.x, euler.y, euler.z
    
    pos = (0, 0, 0)# name["translation"]["X"] / 100.0, -name["translation"]["Y"] / 100.0, name["translation"]["Z"] / 100.0

    return (bpy.data.collections.get(mesh),pos,rot)


# pos offset is in m, rot offset is in deg
def buildable_to_mesh_offset(cls: str) -> [Vec3, Vec3]:

    if "Foundation" in cls or "Pillar" in cls:
        return ((0, 0, -2), (0, 0, 0))

    if "Beam" in cls:
        return ((0, 0, 0), (-90, 0, -90))

    return ((0, 0, 0), (0, 0, 0))


# create the mesh/object which feeds the geonode to realize the instances in the scene
def create_buildable_object(
    cls: str,
    positions: list[Vec3],
    rotations: list[Vec4],
    scales: list[Vec3],
    primary_colors: list[Vec4] = [],
    secondary_colors: list[Vec4] = [],
    paint_type: list[int] = [],
    lengths: list[float] = [],
    prop_attr: list[dict] = [],
    is_heavy:bool = False
):
    
    
                    
    POLE_BUILDS = [
        "Build_ConveyorPole_C",
        "Build_PipelineSupport_C",
        "Build_SignPole_",
        "Build_PipeHyperSupport_C"
    ]
    
    # new mesh for all the 'name' buildables
    mesh = bpy.data.meshes.new(f"{cls}_Points")
    mesh.from_pydata(positions, [], [])
    # object from the mesh
    obj = bpy.data.objects.new(f"{cls}_Points", mesh)
    
    get_or_create_collection("Heavyweights","Import")
    get_or_create_collection("Lightweights","Import")
    
    if not 'WidgetSign' in cls:
        if is_heavy:
            create_weight_collection("Heavyweights").objects.link(obj)
        else:
            create_weight_collection("Lightweights").objects.link(obj)
    else:
        get_or_create_collection("Signs","Heavyweights")
        create_sign_text_collection(cls,"Signs").objects.link(obj)
   
    # set the various named attributes
    mesh.attributes.new("rotation", "FLOAT_VECTOR", "POINT")
    flat = [c for vec in rotations for c in vec]
    mesh.attributes["rotation"].data.foreach_set("vector", flat)

    # apply the beam length addjustment to scale
    if not lengths == []:
        adj_scales = [
            (s[0] * l, s[1], s[2]) if l != 0 else s for s, l in zip(scales, lengths)
        ]
    else:
        adj_scales = [
            (s[0], s[1], s[2]) for s in scales
        ]
    
    sign_text_col_list = []
    if prop_attr:
        for i,prop in enumerate(prop_attr):
            for attr in prop_attr[i]:
                if 'type' == attr:
                    continue
                if 'color' in attr:
                    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    flat = [c for att in prop[attr] for c in att]
                    mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                if 'ems' in attr or 'glos' in attr:# or 'length' in attr:
                    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    mesh.attributes[attr].data.foreach_set(prop['type'][1], prop[attr])
                if 'icons' in attr:
                    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    flat = [c for att in prop[attr] for c in att]
                    mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                if 'text' in attr:
                    text1 = []
                    text2 = []
                    text3 = []
                    text_id = 0
                    for att in prop[attr]:
                        if len(att) == 3:
                            text1.append(att[0])
                            text_id += 1
                            text2.append(att[1])
                            text3.append(att[2])
                        else:
                            text1.append(att[0])
                            text_id += 1
                            text2.append(att[1])
                    sign_name = f"{cls}"#_{text_id}"
                    text_1_id,text_col = add_text_splines_to_curve( text1,sign_name,0)
                    sign_text_col_list.append(text_col)
                    text_2_id,text_col = add_text_splines_to_curve( text2,sign_name,1)
                    sign_text_col_list.append(text_col)
                    text_3_id,text_col = add_text_splines_to_curve( text3,sign_name,2)
                    sign_text_col_list.append(text_col)
                    text_ids = []
                    for i in range(text_id):
                        if text_3_id:
                            text_ids.append(
                                (text_1_id[i],
                                text_2_id[i],
                                text_3_id[i])
                            )
                        else:
                            text_ids.append(
                                (text_1_id[i],
                                text_2_id[i],
                                0)
                            )
                    flat = [c for vec in text_ids for c in vec]
                    mesh.attributes.new("text_id", "FLOAT_VECTOR", "POINT")
                    mesh.attributes["text_id"].data.foreach_set('vector', flat)
                    #flat = [c for att in prop[attr] for c in att]
                    ##print(flat)
                    #mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                if not 'WidgetSign' in cls:
                    
                    if prop['type'][0] == "FLOAT2" or prop['type'][0] == "FLOAT" or prop['type'][0] == "INT" or prop['type'][0] == "BOOLEAN":
                        try:
                            mesh.attributes.new(attr, prop['type'][0], "POINT")
                            mesh.attributes[attr].data.foreach_set(prop['type'][1], prop[attr])
                            
                        except Exception as e:
                            print(f"failed to create {attr} {prop['type'][0]} attribute for {cls}: {e}")
                            afs
                           
    try:
        mesh.attributes.new("scale", "FLOAT_VECTOR", "POINT")
        flat = [c for vec in adj_scales for c in vec]
        mesh.attributes["scale"].data.foreach_set("vector", flat)
    except Exception as e:
        print("failed to create scale attribute",e)
    try:
        mesh.attributes.new("primary_color", "FLOAT_COLOR", "POINT")
        flat = [c for rgba in primary_colors for c in rgba]
        mesh.attributes["primary_color"].data.foreach_set("color", flat)
    except Exception as e:
        print("failed to create primary_color attribute",e)
    try:
        mesh.attributes.new("secondary_color", "FLOAT_COLOR", "POINT")
        flat = [c for rgba in secondary_colors for c in rgba]
        mesh.attributes["secondary_color"].data.foreach_set("color", flat)
    except Exception as e:
        print("failed to create secondary_color attribute",e)
    try:    
        mesh.attributes.new("paint_index", "INT", "POINT")
        flat = [idx for idx in paint_type]
        mesh.attributes["paint_index"].data.foreach_set("value", flat)
    except Exception as e:
        print("failed to create paint_index attribute",e)
    

    #node_group = bpy.data.node_groups["Buildables from Points"]
    #mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    #mod.node_group = node_group
    if 'WidgetSign' in cls:
        node_group = bpy.data.node_groups["Buildables from Points(signs)"]
        mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
        mod.node_group = node_group
        set_geonode_input(mod, "Use Default Object", True)
        set_geonode_input(mod, "Text", False)
        set_geonode_input(mod, "TextBlock_0", sign_text_col_list[0])
        set_geonode_input(mod, "TextBlock_1", sign_text_col_list[1])
        if len(sign_text_col_list) == 3:
            set_geonode_input(mod, "TextBlock_2", sign_text_col_list[2])
        sign_mat = bpy.data.materials.get("MI_SignBackground")
        
        if sign_mat:
            set_geonode_input(mod, "Material", sign_mat)
    else:
        node_group = bpy.data.node_groups["Buildables from Points"]
        mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
        mod.node_group = node_group

    # map a buildable to an asset object, set the default object flag if None to let the geonode supply its fallback
    #asset_obj = buildable_class_to_object(cls)
    
    result = buildable_class_to_object(cls)
    print(f"maping name: {result}")
    if result is not None:
        asset_obj, pos_offset, rot_offset = result
    else:
        asset_obj = None
        pos_offset = (0, 0, 0)
        rot_offset = (0, 0, 0)
    set_geonode_input(mod, "Collection", asset_obj)
    # apparently you cant test if Object is a None in the geonode so...
    set_geonode_input(mod, "Use Default Object", asset_obj is None)

    if any(pole in cls for pole in POLE_BUILDS):
        set_geonode_input(mod, "Is Pole", True)

    #pos_offset, rot_offset = buildable_to_mesh_offset(cls)
    set_geonode_input(mod, "Mesh Pos", pos_offset)
    # remember to convert to rad for the socket input
    set_geonode_input(mod, "Mesh Rot", tuple(x for x in rot_offset))
    
# end geonode

def import_lightweights(save: s.SaveGame, color_map: dict):
    cls = save.allSaveObjects()
    
    # get the lightweight buildable subsystem
    lbs = get_lbs(save)
    instances_by_class_ref = lbs.mBuildableClassToInstanceArray

    for class_ref in list(instances_by_class_ref.Keys):
        class_path = class_ref.PathName

        if not class_path:
            raise Exception("Missing class path, how can this happen?")

        instances = instances_by_class_ref[class_ref]

        name = class_path.split(".")[-1]

        # if 'Beam' not in name:
        #    continue;

        if not instances:
            continue       
        verts, rotations, scales = map(
            list, zip(*(read_transform(i.Transform) for i in instances))
        )

        colors = [read_colors(i,color_map) for i in instances]
        primary_colors, secondary_colors, paint_type = zip(*colors)   

        if 'Build_Beam_Painted_C' in name or 'Build_Beam_C' == name:
            lengths = [read_length(i) for i in instances]
            lengths = [l / 4.0 for l in lengths]
        else:
            lengths = [read_length(i) for i in instances]
            
        prop_attr = []
        if "Build_Beam_Shelf_" in name:
            beam_type = [1] * len(instances)
            prop_attr.append({
                "beam_type" : beam_type,
                    "type":["INT","value"]
            })
            
        

        create_buildable_object(
            name, verts, rotations, scales, primary_colors, secondary_colors, paint_type, lengths, prop_attr
        )
        
def import_signs(name: str, instances: list[list]):
    
    prop_attr = []
    color_attr = []
    text_attr= []
    icons_attr = []
    ems_attr = []
    glos_attr = []
    color_idx_f = []
    color_idx_b = []
    color_idx_a = []
    for actor in instances[1]:
        ems_check = False
        glos_check = False
        aux_check = False
        for prop in actor.Properties:
            #if 'mSoftActivePrefabLayout' in prop.Name.Name:
            #    #print(f"{prop.Name.Name}: {prop.Value.AssetPath.AssetName.Name}")
            #    # TODO use a layout map
            #    ...
            if 'mPrefabTextElementSaveData' in prop.Name.Name:
                text_attr.append(tuple([idx.Data[1].Value for idx in prop.Value.Values]))
            if 'mPrefabIconElementSaveData' in prop.Name.Name:
                icons_attr.append(tuple([idx.Data[1].Value for idx in prop.Value.Values])) 
            if 'mForegroundColor' in prop.Name.Name:
                color_idx_f.append(
                    {
                        "R":prop.Value.Data.R,
                        "G":prop.Value.Data.G,
                        "B":prop.Value.Data.B,
                        "A":prop.Value.Data.A
                    }
                )
            if 'mBackgroundColor' in prop.Name.Name:
                color_idx_b.append(
                    {
                        "R":prop.Value.Data.R,
                        "G":prop.Value.Data.G,
                        "B":prop.Value.Data.B,
                        "A":prop.Value.Data.A
                    }
                )  
            if 'mAuxilaryColor' in prop.Name.Name:
                color_idx_a.append(
                    {
                        "R":prop.Value.Data.R,
                        "G":prop.Value.Data.G,
                        "B":prop.Value.Data.B,
                        "A":prop.Value.Data.A
                    }
                ) 
                aux_check = True
            if 'mEmissive' in prop.Name.Name:
                ems_attr.append(prop.Value)
                ems_check = True
            if 'mGlossiness' in prop.Name.Name:
                glos_attr.append(prop.Value)
                glos_check = True
        
        if not ems_check:
            ems_attr.append(1.0)
        
        if not glos_check:
            glos_attr.append(0.0)
            
        if not aux_check:
            color_idx_a.append(
                {
                        "R":0.0,
                        "G":0.0,
                        "B":0.0,
                        "A":1.0
                    }
            )
            
        verts, rotations, scales = map(
                list, zip(*(read_transform(i) for i in instances[0]))
            )
        
    prop_attr.append({
        "foreground_color" : [(c["R"], c["G"], c["B"], c["A"]) for c in color_idx_f],
        "type":["FLOAT_COLOR","color"]
        })
    prop_attr.append({
        "background_color" : [(c["R"], c["G"], c["B"], c["A"]) for c in color_idx_b],
        "type":["FLOAT_COLOR","color"]
        })
    prop_attr.append({
        "auxilary_color" : [(c["R"], c["G"], c["B"], c["A"]) for c in color_idx_a],
        "type":["FLOAT_COLOR","color"]
        })
    
    #text_id = 0 
    ## text attributes
    #prop_attr.append({
    #    "text_id" : [ (text_id + 1) if len(i) == 3 else (text_id + 1) for i in text_attr],
    #    "type":["FLOAT","value"]
    #    })
    prop_attr.append({
        "text" : [ (i[0],i[1],i[2])if len(i) == 3 else (i[0],i[1],"") for i in text_attr],
        "type":["FLOAT_VECTOR","vector"]
        })
    
    # icon attributes
    prop_attr.append({
        "icons" : [ (i[0],i[1],0) if len(i) == 2 else i for i in icons_attr],
        "type":["FLOAT_VECTOR","vector"]
        }) 
    
    # emission attributes
    prop_attr.append({
        "ems" : ems_attr,
        "type":["FLOAT","value"]
        })
    
    # glossiness attributes
    prop_attr.append({
        "glos" : glos_attr,
        "type":["FLOAT","value"]
        })   
    #print(prop_attr) 
    create_buildable_object(
        name, verts, rotations, scales,prop_attr = prop_attr
    )

def import_conveyor_chain(
    actor: s.AFGConveyorChainActor, 
    transform: s.FTransform3f, 
    color_map: dict,
    conveyor_dict,
    passthroughs: list):
    #debug_inspect(obj)
     
    conv = lambda v: Vector((v.X/100, -v.Y/100, v.Z/100))

    #collect the splines in reverse order
    #i dont know why but the starsAtLength property suggest reversing the order and it worked
    points = []
    chain_lift_points = []
    chain_belt_points = []
    chain_points = []
    chain_count = 1
    conveyor_name = ""
    conveyor_ref = ""
    conveyor_mk = 0
    conveyor_attr = [0,0]
    lift_top_rot = []
    lift_rot = []
    belt_top_rot = []
    belt_rot = []
    rot_list = [(0.0,0.0,0.0)]
    top_rot_list = [(0.0,0.0,0.0)]
    colors = []
    primary_colors = [(0.0, 0.0, 0.0, 1.0)]
    secondary_colors = [(0.0, 0.0, 0.0, 1.0)]
    paint_type = [0]
    passthrough = []
    passthrough_lift = [0,0]
    type_mk = [0,0]
    type_mk_lift = []
    type_mk_belt = []
    
    for i, seg in enumerate(reversed(actor.mChainSplineSegments)):
        conveyor_ref = seg.ConveyorBase.PathName
        conveyor_name = seg.ConveyorBase.PathName.split('_')[2]
        conveyor_mk = conveyor_name[-1:]
        is_belt = True if "Belt" in conveyor_name else False
        #conveyor_attr.append(0)
        
        
        conveyor_inst = conveyor_dict.get(conveyor_ref)
        conveyor_colors = conveyor_inst.get("Colors")
        conveyor_top_rot = conveyor_inst.get("TopRotation")
        conveyor_rot = conveyor_inst.get("Rotations")
        conveyor_passthroughs = conveyor_inst.get("Passthroughs")
        
        quat = Quaternion((
            -conveyor_rot['W'], 
            conveyor_rot['X'], 
            -conveyor_rot['Y'], 
            conveyor_rot['Z']
        ))
        euler = quat.to_euler("XYZ")
        rot = euler.x, euler.y, euler.z
        
        if conveyor_top_rot:
            top_quat = Quaternion((
                -conveyor_top_rot['W'], 
                conveyor_top_rot['X'], 
                -conveyor_top_rot['Y'], 
                conveyor_top_rot['Z']
            ))
            top_euler = top_quat.to_euler("XYZ")
            top_rot = top_euler.x, top_euler.y, top_euler.z
            
            
        p_colors, s_colors, p_type = zip(*conveyor_colors)
        
        pts = seg.SplinePointData
        #if i > 0:
        #    pts = pts[1:]  # skip segment join
        
        chain_points = []
        if not is_belt:  
            for p in pts:
                chain_count = 0
                chain_points.append((
                    conv(p.Location),
                    conv(p.ArriveTangent),
                    conv(p.LeaveTangent)
                    ))
            primary_colors.append(p_colors[0])
            secondary_colors.append(s_colors[0])
            paint_type.append(p_type[0])
            lift_rot.append(rot)
            if conveyor_top_rot:
                lift_top_rot.append(top_rot)
            else:
                lift_top_rot.append((0.0,0.0,0.0))
            if conveyor_passthroughs:
                passthrough_lift.append(conveyor_passthroughs[0])
                passthrough_lift.append(conveyor_passthroughs[1])
            else:
                passthrough_lift.append(0)
                passthrough_lift.append(0)
            type_mk_lift.append(int(is_belt))
            type_mk_lift.append(int(conveyor_mk))
            
        
        if is_belt: 
            for p in pts:
                if chain_count > 0:
                    chain_points.append((
                        conv(p.Location),
                        conv(p.ArriveTangent),
                        conv(p.LeaveTangent)
                        ))
                points.append((
                    conv(p.Location),
                    conv(p.ArriveTangent),
                    conv(p.LeaveTangent)
                ))
            primary_colors.append(p_colors[0])
            secondary_colors.append(s_colors[0])
            paint_type.append(p_type[0])
            belt_rot.append(rot)
            belt_top_rot.append((0.0,0.0,0.0))
            passthrough.append(0)
            passthrough.append(0)
            type_mk_belt.append(int(is_belt))
            type_mk_belt.append(int(conveyor_mk))
                 
        chain_count += 1
        
        if chain_points and is_belt:
            chain_belt_points.append((chain_points))
            
        if chain_points and not is_belt:
            chain_lift_points.append((chain_points))
    
    passthrough.extend(passthrough_lift)
    type_mk.extend(type_mk_belt) 
    type_mk.extend(type_mk_lift) 
    
    rot_list.extend(belt_rot)
    rot_list.extend(lift_rot)
    top_rot_list.extend(belt_top_rot)    
    top_rot_list.extend(lift_top_rot)
    curve = bpy.data.curves.new(f"Spline", type='CURVE')
    
    curve.dimensions = '3D'
    
    # todo remove visuals
    curve.bevel_depth = 0
    curve.twist_mode = "Z_UP"
    curve.bevel_resolution = 2
    
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"
    #for i, (L, A, R) in enumerate(points):
    #    print(f"{i:03d}  L={fmt(L)}  A={fmt(A)}  R={fmt(R)}")
    k = 1.0 / 3.0  # hermite -> bezier scaler
    for i, (L, A, R) in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = L
        bp.handle_left = L - (A * k) 
        bp.handle_right = L + (R * k)
        bp.handle_left_type = 'FREE'
        bp.handle_right_type = 'FREE'

    #plot belt points
    for belt in chain_belt_points:
        spline_belt = curve.splines.new('BEZIER')
        spline_belt.bezier_points.add(len(belt) - 1)
        fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"
        #for i, (L, A, R) in enumerate(belt):
        #    print(f"{i:03d}  L={fmt(L)}  A={fmt(A)}  R={fmt(R)}")
        k = 1.0 / 3.0  # hermite -> bezier scaler
        for i, (L, A, R) in enumerate(belt):
            bp = spline_belt.bezier_points[i]
            bp.co = L
            bp.handle_left = L - (A * k) 
            bp.handle_right = L + (R * k)
            bp.handle_left_type = 'FREE'
            bp.handle_right_type = 'FREE'
    
    #plot lift points
    if chain_lift_points:
        for lift in chain_lift_points:
            spline_lift = curve.splines.new('BEZIER')
            spline_lift.bezier_points.add(len(lift) - 1)
            fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"
            #for i, (L, A, R) in enumerate(lift):
            #    print(f"{i:03d}  L={fmt(L)}  A={fmt(A)}  R={fmt(R)}")
            k = 1.0 / 3.0  # hermite -> bezier scaler
            for i, (L, A, R) in enumerate(lift):
                bp = spline_lift.bezier_points[i]
                bp.co = L
                bp.handle_left = L - (A * k) 
                bp.handle_right = L + (R * k)
                bp.handle_left_type = 'FREE'
                bp.handle_right_type = 'FREE'

    obj = bpy.data.objects.new(f"ConveyorChain", curve)
    
    #obj.data.attributes.new(attr, prop['type'][0], "POINT")
    # move the whole actor cause the splines are relative to it
    pos, rot, scale = read_transform(transform)
    obj.location = pos
    obj.rotation_euler = rot
    get_or_create_collection("Heavyweights","Import")
    get_or_create_collection("Splines","Heavyweights")
    get_or_create_collection("ConveyorChain","Splines").objects.link(obj)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='CURVES')
    curve_data = obj.data
    
    new_attribute = curve_data.attributes.new(name="conveyor_type_mk", type="FLOAT2", domain="CURVE")
    new_attribute.data.foreach_set("vector", type_mk)
    
    #for i in top_rot_list:
    #    i = i+rot
    
    if top_rot_list:
        curve_data.attributes.new("lift_top_rot", "FLOAT_VECTOR", "CURVE")
        flat = [c for vec in top_rot_list for c in vec]
        curve_data.attributes["lift_top_rot"].data.foreach_set("vector", flat)
        
    if passthrough:
        new_attribute = curve_data.attributes.new(name="passthrough", type="FLOAT2", domain="CURVE")
        new_attribute.data.foreach_set("vector", passthrough)
        
    curve_data.attributes.new("lift_rot", "FLOAT_VECTOR", "CURVE")
    flat = [c for vec in rot_list for c in vec]
    curve_data.attributes["lift_rot"].data.foreach_set("vector", flat)
    
    curve_data.attributes.new("primary_color", "FLOAT_COLOR", "CURVE")
    flat = [c for rgba in primary_colors for c in rgba]
    
    curve_data.attributes["primary_color"].data.foreach_set("color", flat)

    curve_data.attributes.new("secondary_color", "FLOAT_COLOR", "CURVE")
    flat = [c for rgba in secondary_colors for c in rgba]
    curve_data.attributes["secondary_color"].data.foreach_set("color", flat)
    
    curve_data.attributes.new("paint_index", "INT", "CURVE")
    flat = [idx for idx in paint_type]
    curve_data.attributes["paint_index"].data.foreach_set("value", flat)
    
    node_group = bpy.data.node_groups["Conveyer Cains From Spline"]
    mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    mod.node_group = node_group
    
    set_geonode_input(mod, "Lifts Collection", bpy.data.collections.get("Lifts"))
    set_geonode_input(mod, "Lift Parts Collection", bpy.data.collections.get("LiftParts"))
    set_geonode_input(mod, "Belts Collection", bpy.data.collections.get("ConveyorBelts"))
        
def import_color_slots(cls: s.SaveGame) -> dict:
    with open(color_map_path, 'r', encoding='utf-8') as f:
        color_map = json.load(f)
    for obj in cls:
        try:
            ong_name = obj.Header.ObjectHeader.Reference.PathName
            if 'BuildableSubsystem' in ong_name:
                for prop in obj.Object.Properties:
                    if 'mColorSlots_Data' in prop.Name.Name:
                        for i, idx in enumerate(prop.Value.Values):
                            swatch_name =list(color_map)[i]
                            for data in idx.Data:
                                try:
                                    if 'PrimaryColor' in data.Name.Name:
                                        data_attr = getattr(data.Value, 'Data')
                                        
                                        color_map[swatch_name]["PrimaryColor"] = {
                                            "R": data_attr.R,
                                            "G": data_attr.G,
                                            "B": data_attr.B,
                                            "A": data_attr.A
                                        }
                                    
                                    if 'SecondaryColor' in data.Name.Name:
                                        data_attr = getattr(data.Value, 'Data')
                                        
                                        color_map[swatch_name]["SecondaryColor"] = {
                                            "R": data_attr.R,
                                            "G": data_attr.G,
                                            "B": data_attr.B,
                                            "A": data_attr.A
                                        }
                                    
                                    if 'PaintFinish' in data.Name.Name:
                                        path_attr = getattr(data.Value, 'PathName')
                                        color_map[swatch_name]["PaintFinish"] = str(path_attr).split('.')[-1]
                                        
                                except Exception as e:                    
                                    print(f"  Error inspecting property value (import_color_slots): {e}")
        except Exception as e:
            print(f"  Error inspecting object (import_color_slots): {e}")
    
    return color_map

def import_object_actors(cls):
    pass
    
def import_spline_buildables(name: str,instances: list[list],color_map:dict):
    transform = instances[0]
    actors = instances[1]
    
    
    for i,actor in enumerate(actors):
        transform = instances[0][i]
        passthroughs = []
        flow_indicator = False
        spline_points = []
        conv = lambda v: Vector((v.X/100, -v.Y/100, v.Z/100))
        
        colors = [
                read_colors(prop.Value.Data[0].Value.PathName,color_map) 
                for prop in actor.Properties
                if 'mCustomizationData' in prop.Name.Name
                ]
        primary_colors, secondary_colors, paint_type = zip(*colors)
        
        props = actor.Properties
        for prop in props:
            prop_name = prop.Name.Name
            if 'mSnappedPassthroughs' in prop_name:
                prop_data = prop.Value
                for i in prop_data.Values:
                    if i.PathName:
                        passthroughs.append(1)
                    else:
                        passthroughs.append(0)
            elif 'mFlowIndicator' in prop_name:
                flow_indicator = True
            elif 'mSplineData' in prop_name:
                spline = prop.Value.Values
                for data in spline:
                    
                    points = []
                    for value in data.Data:
                        point = value.Value.Data
                        
                        points.append(
                            conv(point)
                        )
                    spline_points.append(tuple(points))
                     
        curve = bpy.data.curves.new(f"Spline", type='CURVE')
                        
        curve.dimensions = '3D'     
        curve.bevel_depth = 0   
        curve.twist_mode = "Z_UP"   
        curve.bevel_resolution = 2 
        
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(len(spline_points) - 1)
        fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"
        k = 1.0 / 3.0  # hermite -> bezier scaler
        for i, (L, A, R) in enumerate(spline_points):
            bp = spline.bezier_points[i]
            bp.co = L
            bp.handle_left = L - (A * k) 
            bp.handle_right = L + (R * k)
            bp.handle_left_type = 'FREE'
            bp.handle_right_type = 'FREE'
        
        obj = bpy.data.objects.new(name[:-2], curve)
        pos, rot, scale = read_transform(transform)
        obj.location = pos
        get_or_create_collection("Heavyweights","Import")
        get_or_create_collection("Splines","Heavyweights")
        get_or_create_collection(name,"Splines").objects.link(obj)
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.convert(target='CURVES')
        curve_data = obj.data
        if "PipeHyper" not in name:
            curve_data.attributes.new("primary_color", "FLOAT_COLOR", "CURVE")
            flat = [c for rgba in primary_colors for c in rgba]
            curve_data.attributes["primary_color"].data.foreach_set("color", flat)

            curve_data.attributes.new("secondary_color", "FLOAT_COLOR", "CURVE")
            flat = [c for rgba in secondary_colors for c in rgba]
            curve_data.attributes["secondary_color"].data.foreach_set("color", flat)
            
            curve_data.attributes.new("paint_index", "INT", "CURVE")
            flat = [idx for idx in paint_type]
            curve_data.attributes["paint_index"].data.foreach_set("value", flat)
            
        if passthroughs:
            new_attribute = curve_data.attributes.new(name="passthroughs", type="FLOAT2", domain="CURVE")
            new_attribute.data.foreach_set("vector", passthroughs)
        if flow_indicator:
            new_attribute = curve_data.attributes.new(name="flow_indicator", type="BOOLEAN", domain="CURVE")
            new_attribute.data.foreach_set("value", [flow_indicator])
        
        f_indicator_result = None
        if "Build_RailroadTrackIntegrated" in name:
            result = buildable_class_to_object("Build_RailroadTrack_C")
        elif "Pipeline_NoIndicator" in name:
            result = buildable_class_to_object("Build_Pipeline_C")
        elif "PipelineMK2_NoIndicator" in name:
            result = buildable_class_to_object("Build_PipelineMK2_C")  
        else:
            result = buildable_class_to_object(name)
            f_indicator_result = buildable_class_to_object("Build_PipelineFlowIndicator_C")
        
        if f_indicator_result is not None:
            f_indicator_asset_obj, pos_offset, rot_offset = f_indicator_result
        else:
            f_indicator_asset_obj = None
            
        if result is not None:
            asset_obj, pos_offset, rot_offset = result
        else:
            asset_obj = None
            pos_offset = (0, 0, 0)
            rot_offset = (0, 0, 0)
        
        node_group = bpy.data.node_groups["Buildables From Spline"]
        mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
        mod.node_group = node_group
        
        set_geonode_input(mod, "Collection", asset_obj)
        set_geonode_input(mod, "Pipe Indicator", f_indicator_asset_obj)
        set_geonode_input(mod, "Use Default Object", asset_obj is None)

def import_powerlines(name: str,instances: list[list]):
    transform = instances[0]
    actors = instances[1]
    
    for i,actor in enumerate(actors):
        transform = instances[0][i]
        power_line_list = []
        passthroughs = ""
        flow_indicator = False
        #spline_points = []
        all_spline_points = []
        inst_splines = []
        conv = lambda v: Vector((v.X/100, -v.Y/100, v.Z/100))
    
        
        props = actor.Properties
        for prop in props:
            prop_name = prop.Name.Name
            if 'mWireInstances' in prop_name:
                instance = prop.Value.Values
                for line in instance:
                    spline_points = []
                    spline_point = []
                    for loc in line.Data: #point
                        points = []
                        if loc.Name.Name.startswith("Ca"):
                            point = loc.Value.Data
                            points.append(
                                    conv(point)
                                )
                            points.append(
                                    Vector((0,0,0))
                                )
                            points.append(
                                    Vector((0,0,0))
                                )
                            spline_point.append(tuple(points))
                    for i in spline_point:
                        spline_points.append(i)
                    inst_splines.append(spline_points)    
                    
        curve = bpy.data.curves.new(f"Spline", type='CURVE')
                        
        curve.dimensions = '3D'     
        curve.bevel_depth = 0   
        curve.twist_mode = "Z_UP"   
        curve.bevel_resolution = 2 
        
        for i in inst_splines:
            spline = curve.splines.new('BEZIER')
            spline.bezier_points.add(len(i) - 1)
            fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"
            k = 1.0 / 3.0  # hermite -> bezier scaler
            for i, (L, A, R) in enumerate(i):
                bp = spline.bezier_points[i]
                bp.co = L
                bp.handle_left = L - (A * k) 
                bp.handle_right = L + (R * k)
                bp.handle_left_type = 'FREE'
                bp.handle_right_type = 'FREE'
        
        obj = bpy.data.objects.new(name[:-2], curve)
        pos, rot, scale = read_transform(transform)
        obj.location = pos
        obj.rotation_euler = rot
        get_or_create_collection("Heavyweights","Import")
        get_or_create_collection("Splines","Heavyweights")
        get_or_create_collection(name,"Splines").objects.link(obj)
        
        node_group = bpy.data.node_groups["Buildables From Spline"]
        mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
        mod.node_group = node_group
        
        set_geonode_input(mod, "Is Powerline", True)

def import_heavyweights(save: s.SaveGame, color_map: dict):
    save_objects = save.allSaveObjects()
    # color_map = import_color_slots(cls)
    all_classes = set() # all buildable classes in the save
    factory_classes = [] # all factory buildable instances
    exclude_factory = [ # exclude from default importing method 
        "Build_RailroadTrack",
        #"Build_RailroadTrackIntegrated_C_Points",
        #"Build_PowerLine_C",
        "Build_ConveyorBelt",
        "Build_Pipeline_",
        "Build_PipelineMK2",
        "Build_PipeHyper_C",
        "Build_ConveyorLift",
        "Build_PipelineFlowIndicator_C"
    ]   
    spline_buildables = [
        "Build_PipelineMK2_",
        "Build_Pipeline_",
        "Build_RailroadTrack",
        "Build_PipeHyper_C",
    ]
    
    conveyor_dict = {}
    
    attributes = [
        "mHeight",
        "mHeightOfCabin",
        "mLaunchAngle",
        #"mPoleScale",
        "mSnappedBuildingThickness",
        "mSelectedPoleVersion",
        "mHighlightEffectState",
        "mVerticalAngle",
        "mFixtureAngle"
    ]
    
    EX_PROP_BUILDS = [
        "Build_ConveyorPole_C",
        "Build_PipelineSupport_C",
        "Build_SignPole_",
        "Build_PipeHyperSupport_C"
    ]
    
    hub_stage = [0]
    
    for obj in save_objects:
        if not obj.isActor():
            continue    
    
        header = obj.Header
        className =  header.ObjectHeader.ClassName
        classRef =  header.ObjectHeader.Reference.PathName
        actor = obj.Object  
        
        
        if className.startswith('/Game/FactoryGame/Buildable/') and '.Build_' in className and className.endswith('_C') or '.BP_ElevatorCabin_C' in className:
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
        
        if className.startswith('/Game/FactoryGame/Prototype/') and '.Build_' in className and className.endswith('_C'):
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
            
        if className.startswith('/Game/FactoryGame/Buildable/Factory/Conveyor') and "Mk" in className:
            conveyor_dict[classRef] = None
            top_rotations = {}
            passthroughs = []
            rotations = {
                'W':header.Transform.Rotation.W,
                'X':header.Transform.Rotation.X,
                'Y':header.Transform.Rotation.Y,
                'Z':header.Transform.Rotation.Z
            }
            
            colors = []
            for prop in actor.Properties:
                prop_name = prop.Name.Name
                prop_data = None
                if 'mSnappedPassthroughs' in prop_name:
                    prop_data = prop.Value
                    for i in prop_data.Values:
                        if i.PathName:
                            passthroughs.append(1)
                        else:
                            passthroughs.append(0)
                if 'mTopTransform' in prop_name:
                    for i in prop.Value.Data:
                        if "Rotation" == i.Name.Name:
                            prop_data = i.Value
                    if prop_data:
                        top_rotations = {
                            'W':prop_data.Data.W,
                            'X':prop_data.Data.X,
                            'Y':prop_data.Data.Y,
                            'Z':prop_data.Data.Z,
                        }
            colors = [
                read_colors(prop.Value.Data[0].Value.PathName,color_map) 
                for prop in actor.Properties
                if 'mCustomizationData' in prop.Name.Name
                ]
            
            conveyor_dict[classRef] = {
                "Rotations":rotations,
                "Colors":colors,
                "TopRotation":top_rotations,
                "Passthroughs":passthroughs
            }
    
        if "BP_PlayerState_C" in classRef:
            for prop in actor.Properties:  
                prop_name = prop.Name.Name
                if 'mPlayedMessages' in prop_name:
                    for msg in prop.Value.Values:
                        if "Tier" in msg.PathName:
                            hub_stage = [5]
                            break
                        elif "MSG_Onboarding_HUB_Upgrade6" in msg.PathName:
                            hub_stage = [5]
                            break
                        elif "MSG_Onboarding_HUB_Upgrade5" in msg.PathName:
                            hub_stage = [4]
                        elif "MSG_Onboarding_HUB_Upgrade4" in msg.PathName:
                            hub_stage = [4]
                        elif "MSG_Onboarding_HUB_Upgrade3" in msg.PathName:
                            hub_stage = [3]
                        elif "MSG_Onboarding_HUB_Upgrade2" in msg.PathName:
                            hub_stage = [2]
                        elif "MSG_Onboarding_HUB_Upgrade1" in msg.PathName:
                            hub_stage = [1]

    count = 0
    # conveyor belt chains
    for obj in save.mPersistentAndRuntimeData.SaveObjects:  
        
        if not obj.isActor():
            continue
        
        header = obj.Header
        transform = header.Transform
        className =  header.ObjectHeader.ClassName
        actor = obj.Object    
        
        
        
        if className.startswith( '/Script/FactoryGame.FGConveyorChainActor'):
            import_conveyor_chain(actor, transform, color_map,conveyor_dict,passthroughs)
    for factory in all_classes:
        
        count = 0
        instances_transform = []
        instances = [[], []] # transforms, actors
        
        # group buildable instances by buildable class 
        for factory_class in factory_classes:
            header = factory_class.Header
            transform = header.Transform
            actor = factory_class.Object
            cls_name = header.ObjectHeader.Reference.PathName
            
            if factory in cls_name:
                count += 1
                instances[0].append(transform)
                instances[1].append(actor)
                
        if factory.startswith('Build_StandaloneWidgetSign_'):
            import_signs(factory, instances)
        elif any(building in factory for building in spline_buildables):
            import_spline_buildables(factory, instances,color_map)
        elif factory.startswith('Build_PowerLine_'):
            import_powerlines(factory, instances)
        else:
            prop_attr = []
            height_attr = []
            passthorugh_thickness_attr = []
            pole_scale_attr = []
            attr_dict = {}
            needs_attr = []
            attr_used = set()
            pole_scale_used = False
            passthrough_type = []
            
            total_instances = len(instances[0])
            
            for i in attributes:
                attr_dict.update({i:[]})
            
            
            skip = False
            for exc in exclude_factory:
                if exc in factory:
                    print(f"Excluding {exc}")
                    skip = True
            if skip:
                continue
            
            for actor in instances[1]:
                print(factory)
                height_check = False
                pole_scale_check = False
                attr_check = {}
                attr_len = 0
                if "Build_FoundationPassthrough_Hypertube_C" in factory:
                    passthrough_type.append(1)
                    
                else:
                    passthrough_type.append(0)
                
                
                for prop in actor.Properties:
                    prop_name = prop.Name.Name
                    attr_check[prop_name] = 0
                    attr_value= None
                    for i in attributes:
                        if i == prop_name:
                            attr_value = float(prop.Value)
                            
                    if attr_value:
                        if not attr_dict.get(prop_name):
                            attr_dict.update({prop_name:[]})
                        attr_dict[prop_name].append(attr_value)
                        attr_check[prop_name] = 1
                        needs_attr.append(factory)
                        attr_used.add(prop_name)
                        
                    else:
                        if not attr_dict.get(prop_name):
                            attr_dict.update({prop_name:[]})
                        attr_dict[prop_name].append(0) 
                        
                    
                    if 'mHeight' in prop_name:
                        height_attr.append(prop.Value)
                        height_check = True
                    if 'mSnappedBuildingThickness' in prop_name:
                        passthorugh_thickness_attr.append(prop.Value)
                    if 'mPoleScale' in prop_name:
                        pole_scale_attr.extend([
                            prop.Value.Data.X,
                            prop.Value.Data.Y
                        ])
                        pole_scale_used = True
                        pole_scale_check = True
                        
                        
                if not height_check:
                    height_attr.append(100.0)
                if not pole_scale_check:
                    pole_scale_attr.extend([0.0,0.0])
                
                for i in attr_dict:
                    check = attr_check.get(i,3)
                    if check != 1:
                        if "mFixtureAngle" in i:
                            attr_dict[i].append(45.0)
                        else:
                            attr_dict[i].append(0.0)
                        
                verts, rotations, scales = map(
                    list, zip(*(read_transform(i) for i in instances[0]))
                )
            for att_u in attr_used:
                if "mFixtureAngle" in att_u:
                    f_angle = attr_dict[att_u]
                    if len(f_angle) > total_instances:
                        attr_dict[att_u].pop(len(f_angle) - 1)
                prop_attr.append({
                        att_u : attr_dict[att_u],
                        "type":["FLOAT","value"]
                    })
                
                
            if pole_scale_used:
                prop_attr.append({
                        "pole_scale" : pole_scale_attr,
                        "type":["FLOAT2","vector"]
                    })

            
            if "Build_TradingPost" in factory:
                prop_attr.append({
                    "hub_stage" : hub_stage,
                        "type":["INT","value"]
                })
            
            if "Build_FoundationPassthrough_" in factory:
                prop_attr.append({
                    "passthrough_type" : passthrough_type,
                        "type":["INT","value"]
                })
            
            
            colors = [
                read_colors(prop.Value.Data[0].Value.PathName,color_map) 
                for i in instances[1]
                for prop in i.Properties
                if 'mCustomizationData' in prop.Name.Name
                ]
            
            if colors:
                primary_colors, secondary_colors, paint_type = zip(*colors)
            
            create_buildable_object(
                factory, 
                verts, 
                rotations, 
                scales, 
                primary_colors, 
                secondary_colors, 
                paint_type,
                prop_attr = prop_attr,
                is_heavy=True
            )

def import_save(path: str):
    # https://github.com/moritz-h/satisfactory-3d-map/blob/master/docs/SATISFACTORY_SAVE.md
    save = s.SaveGame(Path(path))
    saveHeader = save.mSaveHeader
    start_time = time.perf_counter()
    # print the session info to 'clear' the console    
    print(
        f"\n\n\n\n---\n{saveHeader.SessionName} {saveHeader.SaveDateTime.toString()}\n---\n"
    )
    
    # clear the import collection before adding to it
    for obj in list(get_or_create_collection('Import').objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(get_or_create_collection('Import').children):
        bpy.data.collections.remove(col, do_unlink=True)
    # clear out all the orphans
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    
    cls = save.allSaveObjects()
    
    color_map = import_color_slots(cls)
    
    #import_object_actors(save)
    import_heavyweights(save,color_map)
    import_lightweights(save,color_map)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"SF to Blender time: {execution_time:.6f} seconds")


# IMPORTATNT: YOU HAVE TO SAVE AND RELOAD AND RESAVE THE FILE FOR THE BUILDABLES TO MATCH
# I DONT KNOW WHY - perhaps the LBS is append only then it gets pruned on reload?
path = r"SAVE-PATH.sav"
mapping_path=r"PROJECT-PATH\import models\buildable_to_asset.json"
color_map_path = r"PROJECT-PATH\color_map.json"

import_save(path)
