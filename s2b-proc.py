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

def get_or_create_collection(name) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def get_import_collection() -> bpy.types.Collection:
    return get_or_create_collection('Import')

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


def read_colors_custom(i: s.FRuntimeBuildableInstanceData) -> [Vec4, Vec4]:
    try:
        p = i.CustomizationData.OverrideColorData.PrimaryColor
        s = i.CustomizationData.OverrideColorData.SecondaryColor
        
        paint_index = 1
    except AttributeError:
        return ((1, 1, 1, 1), (1, 1, 1, 1),2)

    return ((p.R, p.G, p.B, p.A), (s.R, s.G, s.B, s.A),paint_index)

def read_colors_paint_finish(i: s.FRuntimeBuildableInstanceData) -> [Vec4, Vec4]:
    try:
        p = i.CustomizationData.OverrideColorData.PrimaryColor
        s = i.CustomizationData.OverrideColorData.SecondaryColor
        f = i.CustomizationData.OverrideColorData.PaintFinish
        
        paint_index = 3
    except AttributeError:
        return ((0, 0, 0, 1), (0, 0, 0, 1),4)

    return ((p.R, p.G, p.B, p.A), (s.R, s.G, s.B, s.A),paint_index)


def read_colors_swatch(i: s.FRuntimeBuildableInstanceData) -> [Vec4, Vec4]:
    # todo swatch?
    return ((1, 1, 1, 1), (1, 1, 1, 1),0)


def read_colors(i: s.FRuntimeBuildableInstanceData) -> [Vec4, Vec4]:

    # custom colors use the swatch "...SwatchDesc_Custom_C"
    if "SwatchDesc_Custom_C" in i.CustomizationData.SwatchDesc.PathName:
        return read_colors_custom(i)
    
    if "PaintFinishes" in i.CustomizationData.SwatchDesc.PathName:
        return read_colors_paint_finish(i)

    # todo swatch
    return read_colors_swatch(i)


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
    #map = {
    #    "Build_Foundation_Concrete_8x4_C": "SM_Foundation_Concrete_8x4",
    #    "Build_Foundation_Concrete_8x2_C": "SM_Foundation_Concrete_8x2",
    #    "Build_Foundation_8x1_01_C": "SM_Foundation_Concrete_8x1",
    #    "Build_PillarMiddle_C": "SM_Pillar_MiddleMetal_01",
    #    "Build_PillarBase_C": "SM_Pillar_01",
    #    
    #    #pillars
    #    "Build_Beam_C": "SM_Beam_02",
    #    
    #    # Beams
    #    "Build_Barrier_Corner_C":"SM_CornerBlock_01",
    #    "Build_Beam_Support_C":"SM_SmallestPillarBase_01",
    #    "Build_Beam_Connector_Double_C":"SM_ConnectionCube_Wide_01",
    #    "Build_Beam_Connector_C":"SM_ConnectionCube_01",
    #    "Build_Beam_Cable_Cluster_C":"SM_BeamCable_02",
    #    "Build_Beam_Cable_C":"SM_BeamCable_01",
    #    "Build_Beam_Concrete_C":"SM_Beam_07",
    #    "Build_Beam_Cross_C":"SM_Beam_01",
    #    "Build_Beam_Shelf_C":"SM_Beam_05",
    #    "Build_Beam_H_C":"SM_Beam_04",
    #    "Build_Beam_C": "SM_Beam_02",
    #    "Build_Beam_Painted_C": "SM_BeamPainted_01",
    #}

    name = map.get(cls)
    if name is None:
        print(f"Missing object mapping: {cls}")
        return None
    
    #rot_q = {
    #    "X":name["rotation"].X,
    #    "Y":name["rotation"].Y,
    #    "Z":name["rotation"].Z,
    #    "W":name["rotation"].W
    #}
    
    quat = Quaternion((-name["rotation"]["W"], name["rotation"]["X"],-name["rotation"]["Y"], name["rotation"]["Z"]))
    euler = quat.to_euler("XYZ")
    rot = euler.x, euler.y, euler.z
    
    pos = name["translation"]["X"] / 100.0, -name["translation"]["Y"] / 100.0, name["translation"]["Z"] / 100.0

    #return bpy.data.objects.get(name["object_name"])
    return (bpy.data.objects.get(name["object_name"]),pos,rot)


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
    primary_colors: list[Vec3],
    secondary_colors: list[Vec3],
    paint_type: list[int],
    lengths: list[float],
):
    # new mesh for all the 'name' buildables
    mesh = bpy.data.meshes.new(f"{cls}_Points")
    mesh.from_pydata(positions, [], [])
    # object from the mesh
    obj = bpy.data.objects.new(f"{cls}_Points", mesh)
    
    get_import_collection().objects.link(obj)
   
    # set the various named attributes
    mesh.attributes.new("rotation", "FLOAT_VECTOR", "POINT")
    flat = [c for vec in rotations for c in vec]
    mesh.attributes["rotation"].data.foreach_set("vector", flat)

    # apply the beam length addjustment to scale
    adj_scales = [
        (s[0] * (l / 4.0), s[1], s[2]) if l != 0 else s for s, l in zip(scales, lengths)
    ]

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
    flat = [rgba for rgba in paint_type]
    mesh.attributes["paint_index"].data.foreach_set("value", flat)

    node_group = bpy.data.node_groups["Buildables from Points"]
    mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    mod.node_group = node_group

    # map a buildable to an asset object, set the default object flag if None to let the geonode supply its fallback
    #asset_obj = buildable_class_to_object(cls)
    result = buildable_class_to_object(cls)
    if result is not None:
        asset_obj, pos_offset, rot_offset = result
    else:
        asset_obj = None
        pos_offset = (0, 0, 0)
        rot_offset = (0, 0, 0)
    set_geonode_input(mod, "Object", asset_obj)
    # apparently you cant test if Object is a None in the geonode so...
    set_geonode_input(mod, "Use Default Object", asset_obj is None)
    

    #pos_offset, rot_offset = buildable_to_mesh_offset(cls)
    set_geonode_input(mod, "Mesh Pos", pos_offset)
    # remember to convert to rad for the socket input
    set_geonode_input(mod, "Mesh Rot", tuple(x for x in rot_offset))

# end geonode

def import_lightweights(save: s.SaveGame):
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

        colors = [read_colors(i) for i in instances]
        primary_colors, secondary_colors, paint_type = zip(*colors)   

        lengths = [read_length(i) for i in instances]

        create_buildable_object(
            name, verts, rotations, scales, primary_colors, secondary_colors, paint_type, lengths
        )

        print(f"{name}: {len(instances)}")

def import_conveyor_chain(obj: s.AFGConveyorChainActor, transform: s.FTransform3f):
    debug_inspect(obj)
     
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
    spline.bezier_points.add(len(points) - 1)


    fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"

    for i, (L, A, R) in enumerate(points):
        print(f"{i:03d}  L={fmt(L)}  A={fmt(A)}  R={fmt(R)}")
    
    k = 1.0 / 3.0  # hermite -> bezier scaler
    for i, (L, A, R) in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = L
        bp.handle_left = L - (A * k) 
        bp.handle_right = L + (R * k)
        bp.handle_left_type = 'FREE'
        bp.handle_right_type = 'FREE'
        
    obj = bpy.data.objects.new("SplineObj", curve)
    
    #plot belt points
    for belt in chain_belt_points:
        spline_belt = curve.splines.new('BEZIER')
        spline_belt.bezier_points.add(len(belt) - 1)


        fmt = lambda v: f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"

        for i, (L, A, R) in enumerate(belt):
            print(f"{i:03d}  L={fmt(L)}  A={fmt(A)}  R={fmt(R)}")
        
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

            for i, (L, A, R) in enumerate(lift):
                print(f"{i:03d}  L={fmt(L)}  A={fmt(A)}  R={fmt(R)}")
            
            k = 1.0 / 3.0  # hermite -> bezier scaler
            for i, (L, A, R) in enumerate(lift):
                bp = spline_lift.bezier_points[i]
                bp.co = L
                bp.handle_left = L - (A * k) 
                bp.handle_right = L + (R * k)
                bp.handle_left_type = 'FREE'
                bp.handle_right_type = 'FREE'
    
    
    # move the whole actor cause the splines are relative to it
    pos, rot, scale = read_transform(transform)
    obj.location = pos
    get_import_collection().objects.link(obj)
        

def import_heavyweights(save: s.SaveGame):
    for obj in save.mPersistentAndRuntimeData.SaveObjects:  
        
        if not obj.isActor():
            continue
        
        header = obj.Header
        transform = header.Transform
        cls =  header.ObjectHeader.ClassName
        actor = obj.Object       
        
        if cls.startswith( '/Script/FactoryGame.FGConveyorChainActor'):
            import_conveyor_chain(actor, transform)

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
    # clear out all the orphans
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    
    import_heavyweights(save)
    import_lightweights(save)


# IMPORTATNT: YOU HAVE TO SAVE AND RELOAD AND RESAVE THE FILE FOR THE BUILDABLES TO MATCH
# I DONT KNOW WHY - perhaps the LBS is append only then it gets pruned on reload?
path = "sav_path"
mapping_path=r"mapping_path"
import_save(path)
