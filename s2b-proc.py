import json

import bpy
from mathutils import Quaternion, Matrix, Vector
from pathlib import Path
import math
import satisfactory_save as s

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
            modifier[item.identifier] = value
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
    return text_id    
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


def read_colors_custom(i: s.FRuntimeBuildableInstanceData| str) -> [Vec4, Vec4]:
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


def read_colors_swatch(i: s.FRuntimeBuildableInstanceData| str,color_map: dict) -> [Vec4, Vec4]:
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


def read_colors(i: s.FRuntimeBuildableInstanceData| str,color_map: dict) -> [Vec4, Vec4]:
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
    prop_attr: list[dict] = []
):
    # new mesh for all the 'name' buildables
    mesh = bpy.data.meshes.new(f"{cls}_Points")
    mesh.from_pydata(positions, [], [])
    # object from the mesh
    obj = bpy.data.objects.new(f"{cls}_Points", mesh)
    
    if not 'WidgetSign' in cls:
        get_import_collection().objects.link(obj)
    else:
        create_sign_text_collection(cls).objects.link(obj)
   
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
        
    
    if prop_attr:
        for i,prop in enumerate(prop_attr):
            for attr in prop_attr[i]:
                if 'type' in attr:
                    continue
                #print(type(prop[attr]))
                #print(attr)
                #print(prop[attr])
                if 'color' in attr:
                    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    #print(prop[attr])
                    flat = [c for att in prop[attr] for c in att]
                    #print(flat)
                    mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                if 'ems' in attr or 'glos' in attr:# or 'length' in attr:
                    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    #flat = [c for att in prop[attr] for c in att]
                    #print(flat)
                    mesh.attributes[attr].data.foreach_set(prop['type'][1], prop[attr])
                if 'icons' in attr:
                    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    flat = [c for att in prop[attr] for c in att]
                    #print(flat)
                    mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                    #set_geonode_input(mod, "Use Default Object", asset_obj is None)
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
                    text_1_id = add_text_splines_to_curve( text1,sign_name,0)
                    text_2_id = add_text_splines_to_curve( text2,sign_name,1)
                    text_3_id = add_text_splines_to_curve( text3,sign_name,2)
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
                    
                #if 'text' in attr:
                #    onj = mesh.attributes.new(attr, prop['type'][0], "POINT")
                #    #flat = [att.encode() for att in prop[attr]]
                #    #print(flat)
                #    for i,  vertex_attr in enumerate(onj.data):
                #        flat = [att.encode() for att in prop[attr]]
                #        vertex_attr.value = flat[i]
                #    #mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                

    mesh.attributes.new("scale", "FLOAT_VECTOR", "POINT")
    flat = [c for vec in adj_scales for c in vec]
    mesh.attributes["scale"].data.foreach_set("vector", flat)

    mesh.attributes.new("primary_color", "FLOAT_COLOR", "POINT")
    flat = [c for rgba in primary_colors for c in rgba]
    mesh.attributes["primary_color"].data.foreach_set("color", flat)

    mesh.attributes.new("secondary_color", "FLOAT_COLOR", "POINT")
    flat = [c for rgba in secondary_colors for c in rgba]
    mesh.attributes["secondary_color"].data.foreach_set("color", flat)
    
    mesh.attributes.new("paint_index", "INT", "POINT")
    flat = [idx for idx in paint_type]
    mesh.attributes["paint_index"].data.foreach_set("value", flat)

    #node_group = bpy.data.node_groups["Buildables from Points"]
    #mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    #mod.node_group = node_group
    if prop_attr:
        node_group = bpy.data.node_groups["Buildables from Points(signs)"]
        mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
        mod.node_group = node_group
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
        print(f"{name}: before")        
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

        create_buildable_object(
            name, verts, rotations, scales, primary_colors, secondary_colors, paint_type, lengths
        )

        print(f"{name}: {len(instances)}")
        
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
                #debug_inspect(prop.Value)
                ems_attr.append(prop.Value)
                ems_check = True
            if 'mGlossiness' in prop.Name.Name:
                #debug_inspect(prop.Value)
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
        
        #colors = [read_sign_colors(color_attr)]
        #foreground_color, background_colors, auxilary_type = zip(*colors)
        
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

def import_conveyor_chain(obj: s.AFGConveyorChainActor, transform: s.FTransform3f, color_map: dict):
    #debug_inspect(obj)
     
    conv = lambda v: Vector((v.X/100, -v.Y/100, v.Z/100))

    #collect the splines in reverse order
    #i dont know why but the starsAtLength property suggest reversing the order and it worked
    points = []
    chain_lift_points = []
    chain_belt_points = []
    chain_points = []
    chain_count = 1
    for i, seg in enumerate(reversed(obj.mChainSplineSegments)):

        is_belt = True if "Belt" in seg.ConveyorBase.PathName else False
        
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
                
        chain_count += 1
        
        if chain_points and is_belt:
            chain_belt_points.append((chain_points))
        if chain_points and not is_belt:
            chain_lift_points.append((chain_points))
          
    curve = bpy.data.curves.new("Spline", type='CURVE')
    curve.dimensions = '3D'
    
    # todo remove visuals
    curve.bevel_depth = 0
    curve.twist_mode = "Z_UP"
    curve.bevel_resolution = 2
    
    spline = curve.splines.new('BEZIER')
    #spline = "test"
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
    
    
    obj = bpy.data.objects.new("ConveyorChain", curve)
    
    # move the whole actor cause the splines are relative to it
    pos, rot, scale = read_transform(transform)
    obj.location = pos
    get_import_collection().objects.link(obj)
        
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
    ... 
    
    

def import_heavyweights(save: s.SaveGame, color_map: dict):
    save_objects = save.allSaveObjects()
    # color_map = import_color_slots(cls)
    all_classes = set() # all buildable classes in the save
    factory_classes = [] # all factory buildable instances
    exclude_factory = [ # exclude from default importing method 
        "Build_RailroadTrack",
        #"Build_RailroadTrackIntegrated_C_Points",
        "Build_PowerLine_C",
        "Build_ConveyorBeltMk",
        "Build_Pipeline_",
        "Build_PipelineMK2",
        "Build_PipeHyper_C",
        "Build_ConveyorLift",
    ]   
    
    # conveyor belt chains
    for obj in save.mPersistentAndRuntimeData.SaveObjects:  
        
        if not obj.isActor():
            continue
        
        header = obj.Header
        transform = header.Transform
        className =  header.ObjectHeader.ClassName
        actor = obj.Object       
        
        if className.startswith( '/Script/FactoryGame.FGConveyorChainActor'):
            import_conveyor_chain(actor, transform, color_map)
            
    for obj in save_objects:
        if not obj.isActor():
            continue    
    
        header = obj.Header
        className =  header.ObjectHeader.ClassName
        
        if className.startswith('/Game/FactoryGame/Buildable/Factory/')and '.Build_' in className and className.endswith('_C'):
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
            cls_name = obj.Header.ObjectHeader.Reference.PathName
    
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
                
        #todo: properties data
        if factory.startswith('Build_StandaloneWidgetSign_'):
            import_signs(factory, instances)
        else:
            skip = False
            for exc in exclude_factory:
                if exc in factory:
                    print(f"excluding {exc}")
                    skip = True
            if skip:
                continue
            for actor in instances[1]:
                print(factory)
                # just color swatch data needed
                for prop in actor.Properties:
                    if 'mCustomizationData' in prop.Name.Name:
                        #print(f"Name: {prop.Value.Data[0].Value.PathName}")
                        ...
                        #colors = [read_colors(i,color_map) for i in instances[1]]
                #print(f"just color swatch data needed: {factory}")
                ...
                verts, rotations, scales = map(
                    list, zip(*(read_transform(i) for i in instances[0]))
                )
            
            colors = [
                read_colors(prop.Value.Data[0].Value.PathName,color_map) 
                for i in instances[1]
                for prop in i.Properties
                if 'mCustomizationData' in prop.Name.Name
                ]
            primary_colors, secondary_colors, paint_type = zip(*colors)
            
            create_buildable_object(
                factory, verts, rotations, scales, primary_colors, secondary_colors, paint_type
            )
    

def import_save(path: str):
    # https://github.com/moritz-h/satisfactory-3d-map/blob/master/docs/SATISFACTORY_SAVE.md
    save = s.SaveGame(Path(path))
    saveHeader = save.mSaveHeader
    
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


# IMPORTATNT: YOU HAVE TO SAVE AND RELOAD AND RESAVE THE FILE FOR THE BUILDABLES TO MATCH
# I DONT KNOW WHY - perhaps the LBS is append only then it gets pruned on reload?
#path = "sav_path"
#mapping_path=r"mapping_path"
#color_map_path = r"color_map.json"
path = r"SAVE-PATH.sav"
mapping_path=r"PROJECT-PATH\impot models\buildable_to_asset.json"
color_map_path = r"PROJECT-PATH\color_map.json"
import_save(path)
