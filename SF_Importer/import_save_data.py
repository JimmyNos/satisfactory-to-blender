import os
import random
import functools
import bpy # type: ignore
from bpy.types import Operator, AddonPreferences,PropertyGroup,Panel # type: ignore
from bpy.props import StringProperty, IntProperty, BoolProperty # type: ignore
import threading
import time
from datetime import datetime

import json
#from rich.progress import Progress
from mathutils import Quaternion, Matrix, Vector
from pathlib import Path
import math
from numpy import append
import satisfactory_save as s
import time

from .get_lib_assets import get_lib_assets

# start common types
Vec3 = tuple[float, float, float]
Vec4 = tuple[float, float, float, float]
# end common types

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

def get_or_create_collection(name,parent_name = "",col_color: str = "NONE") -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    parent_col = bpy.data.collections.get(parent_name)
    if not col:
        col = bpy.data.collections.new(name)
        if col_color != "NONE":
            col.color_tag = col_color
        if not parent_name:
            bpy.context.scene.collection.children.link(col)
        else:
            parent_col.children.link(col)
            
    return col

def get_import_collection() -> bpy.types.Collection:
    return get_or_create_collection('Import')

def create_asset_collection() -> bpy.types.Collection:
    return get_or_create_collection('Assets')

def create_sign_text_collection(sign_name,parent_name = 'Import',col_color: str = "NONE") -> bpy.types.Collection:
    return get_or_create_collection(sign_name,parent_name,col_color)

def create_weight_collection(buildable_name,parent_name = 'Import',col_color: str = "NONE") -> bpy.types.Collection:
    return get_or_create_collection(buildable_name,parent_name,col_color)

def add_text_splines_to_curve(text: list, sign_name: str, text_n: int,layout:list):
    """
    Generates spline geometry from a text string and appends 
    those splines directly into an existing curve object.
    """
    # TODO: use name of sign for text obj and collection name
    # a set of text to not create duplicate text obj
    # if a sign uses a text from the set, use idx as id
    #text_dict = dict()
    text_set = set()
    text_id = []
    
    sign_layouts = {}
    sign_layout_path = Path(__file__).parent / "sign_layouts.json"
    with open(    sign_layout_path, 'r', encoding='utf-8') as f:
        sign_layouts = json.load(f) # type: dict[str,dict]
    
    layouts = sign_layouts[sign_name] # layouts used by sign
    
    layout_idx = []
    for i in range(len(layout)):
        if i % 2:
            layout_idx.append(layout[i]) # only get layout idx
    print(layout_idx)
    print(layout)
    idx_l = {i: key for i, key in enumerate(layouts)} # to get idx of sign layouts
    l_data = []
    l_name = []
    for l in layout_idx:
        sign_lay = idx_l[l]
        l_name.append(sign_lay)
        l_data.append(layouts[sign_lay]) # store layout data for each sign instance
    
    lay_dict = {} # type: dict[str,set[str]]
    lay_data_dict = {} # type: dict[str,list[str]]
    for i, t in enumerate(text):
        #lay_dict.update({name:set()})
        name = f"name{i}"
        if not lay_dict.get(l_name[i]):
            lay_dict[l_name[i]] = set()
        lay_dict[l_name[i]].add(t)
        if not t in lay_dict[l_name[i]]:
            lay_data_dict[l_name[i]].append(l_data[i])
    
    text_new = []
    layout_new = []
    idx_dict = {}
    text_new_count = 0
    text_new_idx = []
    for n in lay_dict:
        for i,t in enumerate(lay_dict[n]):
            text_new.append(t)
            layout_new.append(n)
            text_new_idx.append(text_new_count)
            if not idx_dict.get(n):
                idx_dict[n] = {}
            idx_dict[n].update({i:text_new_count})
            text_new_count += 1
    
    for i, t in enumerate(text):
        text_dict = dict()
        lay = lay_dict[l_name[i]]
        for idx, tx  in enumerate(lay):
            text_dict[tx] = idx_dict[l_name[i]][idx]
        #lt_idx = text_dict[t]
        #text_id.append(text.index(t))
        text_id.append(text_dict[t])
                
    #col_name = f"{sign_name}"
    text_set = set()
    text_length = len(text)
    
    font_bold_path = os.path.join(os.path.dirname(__file__),"resources","fonts", "NotoSansJP-Bold.ttf")
    font_semibold_path = os.path.join(os.path.dirname(__file__),"resources","fonts", "NotoSansJP-SemiBold.ttf")
    font_path = os.path.join(os.path.dirname(__file__),"resources","fonts", "NotoSansJP-Regular.ttf")
    font_dict = {
        "Regular":font_path,
        "Bold":font_bold_path,
        "SemiBold":font_path,
    }
    for i,text_string in enumerate(text_new):
        print(layout_new[i])
        l_data_new =  layouts[layout_new[i]]
        print(l_data_new)
        l_d = l_data_new.get("Text")
        if l_d:
            t_config = l_d.get(f"Text{text_n+1}")
        else:
            t_config = None
        # Create a text curve object
        
        text_name = f"{sign_name}_TextBlock_{text_n}_{i}"
        text_data = bpy.data.curves.new(name=text_name, type='FONT')
        text_data.body = text_string
        if t_config:
            font = font_dict[t_config["TypefaceFontName"]]
            if not bpy.data.fonts.get(font):
                data_font = bpy.data.fonts.load(font)
            else:
                data_font = bpy.data.fonts.get(font)
            text_data.font = data_font
            text_data.align_x = t_config["Justification"].upper()
            text_data.align_y = t_config.get("Align_y","TOP_BASELINE").upper()
            text_data.space_line = t_config["LineHeightPercentage"]
            text_data.space_character = 0.985
            text_data.offset_x = t_config["Offset"]['X']
            text_data.offset_y = t_config["Offset"]['Y']
            text_data.size = t_config["Size"]
            text_data.text_boxes[0].width = t_config.get("WrapTextAt",0.0)
            text_data.text_boxes[0].height = 0
        text_obj = bpy.data.objects.new(text_name, text_data)
        
        col = create_sign_text_collection(f"{sign_name}_TextBlock_{text_n}",sign_name)
        col.objects.link(text_obj)
        col.hide_viewport
        col.hide_render
        col.color_tag = "COLOR_01"
        
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

def read_prop(i: s.FRuntimeBuildableInstanceData,prop_name:str) -> float | str:
    for property in i.TypeSpecificData.StructInstance:
        if property.Name.Name == prop_name:
            #if type(property.Value) == str:
            #    return property.Value
            return property.Value / 100  # convert to m
        
    try:
        if "PatternRotation" == prop_name:
            return i.CustomizationData.PatternRotation
        if "PatternDesc" == prop_name:
            return i.CustomizationData.PatternDesc.PathName
    except Exception as e:
        print(e)
    return 0

# end satisfactory api

# start geonode

# map make buildable classes to corrisponding asset
def buildable_class_to_object(cls: str,buildable_to_asset_path: str,is_factory:bool = False) -> [bpy.types.Object,Vec3,Vec3]:# | None:
    json_file_path = buildable_to_asset_path
    print(json_file_path)
    with open(json_file_path, 'r', encoding='utf-8') as f:
        map_file = json.load(f)

    name = map_file.get(cls)
    
    if "Build_PipelinePumpMk2" in cls:
        name = map_file.get("Build_PipelinePumpMK2_C")
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
    primary_colors: tuple = (),
    secondary_colors: tuple = (),
    paint_type: tuple[int] = (0,),
    lengths: list[float] = [],
    prop_attr: list[dict] = [],
    is_heavy:bool = False,
    buildable_to_asset_path: str = ""
    ):
    #global progress_in
    
    use_proxy = bpy.context.scene.sf_importer_props.use_proxy
    hide_buildable = bpy.context.scene.sf_importer_props.hide_buildable
                    
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
    
    get_or_create_collection("Heavyweights","Import",col_color = "COLOR_05")
    #get_or_create_collection("Lightweights","Import",col_color = "COLOR_05")
    
    if not 'WidgetSign' in cls:
        if is_heavy:
            get_or_create_collection("Heavyweight Buildings","Heavyweights",col_color = "COLOR_07").objects.link(obj)
        else:
            get_or_create_collection("Lightweights","Import",col_color = "COLOR_05").objects.link(obj)
    else:
        get_or_create_collection("Signs","Heavyweights",col_color = "COLOR_07")
        create_sign_text_collection(cls,"Signs",col_color = "COLOR_08").objects.link(obj)
    
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
    sign_layout_attr = {}
    if prop_attr:
        for i,prop in enumerate(prop_attr):
            for attr in prop_attr[i]:
                if 'type' == attr:
                    continue
                
                #try:
                if 'WidgetSign' in cls:
                    
                    if 'layout' == attr:
                        sign_layout_attr = prop[attr]
                    if 'color' in attr:
                        mesh.attributes.new(attr, prop['type'][0], "POINT")
                        flat = [c for att in prop[attr] for c in att]
                        mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                    #elif 'ems' in attr or 'glos' in attr:# or 'length' in attr:
                    #    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    #    mesh.attributes[attr].data.foreach_set(prop['type'][1], prop[attr])
                    #elif 'icons' in attr:
                    #    mesh.attributes.new(attr, prop['type'][0], "POINT")
                    #    flat = [c for att in prop[attr] for c in att]
                    #    mesh.attributes[attr].data.foreach_set(prop['type'][1], flat)
                    elif 'text' in attr:
                        layout = sign_layout_attr
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
                        text_1_id,text_col = add_text_splines_to_curve( text1,sign_name,0,layout)
                        sign_text_col_list.append(text_col)
                        text_2_id,text_col = add_text_splines_to_curve( text2,sign_name,1,layout)
                        sign_text_col_list.append(text_col)
                        text_3_id,text_col = add_text_splines_to_curve( text3,sign_name,2,layout)
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
                    else:
                        mesh.attributes.new(attr, prop['type'][0], "POINT")
                        mesh.attributes[attr].data.foreach_set(prop['type'][1], prop[attr])
                        
                #except Exception as e:
                #    print(f"failed to create {{attr}} attribute for {cls}: {e}")

                if not 'WidgetSign' in cls:
                    
                    if prop['type'][0] == "FLOAT2" or prop['type'][0] == "FLOAT" or prop['type'][0] == "INT" or prop['type'][0] == "BOOLEAN":
                        try:
                            mesh.attributes.new(attr, prop['type'][0], "POINT")
                            mesh.attributes[attr].data.foreach_set(prop['type'][1], prop[attr])
                        except Exception as e:
                            print(f"failed to create {attr} {prop['type'][0]} attribute for {cls}: {e}")
                    
    try:
        mesh.attributes.new("scale", "FLOAT_VECTOR", "POINT")
        flat = [c for vec in adj_scales for c in vec]
        mesh.attributes["scale"].data.foreach_set("vector", flat)
    except Exception as e:
        print(f"failed to create scale attribute for {cls}",e)
    
    if not 'WidgetSign' in cls:
        try:
            mesh.attributes.new("primary_color", "FLOAT_COLOR", "POINT")
            flat = [c for rgba in primary_colors for c in rgba]
            mesh.attributes["primary_color"].data.foreach_set("color", flat)
        except Exception as e:
            print(f"failed to create primary_color attribute for {cls}",e)
        try:
            mesh.attributes.new("secondary_color", "FLOAT_COLOR", "POINT")
            flat = [c for rgba in secondary_colors for c in rgba]
            mesh.attributes["secondary_color"].data.foreach_set("color", flat)
        except Exception as e:
            print(f"failed to create secondary_color attribute for {cls}",e)
        try:    
            mesh.attributes.new("paint_index", "INT", "POINT")
            flat = [idx for idx in paint_type]
            mesh.attributes["paint_index"].data.foreach_set("value", flat)
        except Exception as e:
            print(f"failed to create paint_index attribute for {cls}",e)
    
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
        
        try:
            if sign_text_col_list:
                view_layer = bpy.context.view_layer
                sc_col = view_layer.layer_collection.children["Import"].children["Heavyweights"].children["Signs"]
                sign_col = sc_col.children[cls]
                for sc in sign_text_col_list:
                    sign_col.children[sc.name].exclude = True
        except Exception as e:
            print(f"failed to exclude {cls} text collections from viewport",e)
        
        sign_mat = bpy.data.materials.get("MI_SignBackground")
        if sign_mat:
            set_geonode_input(mod, "Material", sign_mat)
    else:
        node_group = bpy.data.node_groups["Buildables from Points"]
        mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
        mod.node_group = node_group
    # map a buildable to an asset object, set the default object flag if None to let the geonode supply its fallback
    #asset_obj = buildable_class_to_object(cls)
    is_factory = False
    if is_heavy or 'WidgetSign' in cls:
        is_factory = True
    result = buildable_class_to_object(cls,buildable_to_asset_path,is_factory)
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

    if use_proxy:
        set_geonode_input(mod, "Use Proxy Mesh", True)
    else:
        set_geonode_input(mod, "Use Proxy Mesh", False)
    
    if any(pole in cls for pole in POLE_BUILDS):
        set_geonode_input(mod, "Is Pole", True)

    #pos_offset, rot_offset = buildable_to_mesh_offset(cls)
    set_geonode_input(mod, "Mesh Pos", pos_offset)
    # remember to convert to rad for the socket input
    set_geonode_input(mod, "Mesh Rot", tuple(x for x in rot_offset))
    
    if hide_buildable:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        obj.hide_viewport = True
    
    #progress_in = 100
    print(f"Imported {cls} from save file")
    
    #bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    
# end geonode

def import_color_slots(cls: s.SaveGame) -> dict:
    color_map_path = Path(__file__).parent / "color_map.json"
    with open(color_map_path, 'r', encoding='utf-8') as f:
        color_map = json.load(f)
    
    print("Getting color swatch data")
    
    for obj in cls:
        try:
            try:
                ong_name = obj.Header.ObjectHeader.Reference.PathName
            except Exception as e:
                continue
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
                                    print(f"Error inspecting property value (import_color_slots): {e}")
        except Exception as e:
            print(f"Error inspecting object (import_color_slots): {e}")
    
    return color_map

def import_spline_buildables(name: str,
                            colors: list,
                            spline_points:list,
                            transform:list,
                            passthroughs:list,
                            flow_indicator:bool,
                            buildable_to_asset_path: str
                            ):
    #global progress_in
    
    use_proxy = bpy.context.scene.sf_importer_props.use_proxy
    hide_buildable = bpy.context.scene.sf_importer_props.hide_buildable
    
    primary_colors, secondary_colors, paint_type = zip(*colors)
    curve = bpy.data.curves.new(f"{name}Spline", type='CURVE')
    
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
    get_or_create_collection("Heavyweights","Import",col_color = "COLOR_05")
    get_or_create_collection("Splines","Heavyweights",col_color = "COLOR_07")
    col = get_or_create_collection(name,"Splines",col_color = "COLOR_07").objects.link(obj)
    
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
        result = buildable_class_to_object("Build_RailroadTrack_C",buildable_to_asset_path,True)
    elif "Pipeline_NoIndicator" in name:
        result = buildable_class_to_object("Build_Pipeline_C",buildable_to_asset_path,True)
    elif "PipelineMK2_NoIndicator" in name:
        result = buildable_class_to_object("Build_PipelineMK2_C",buildable_to_asset_path,True)
    else:
        result = buildable_class_to_object(name,buildable_to_asset_path,True)
        f_indicator_result = buildable_class_to_object("Build_PipelineFlowIndicator_C",buildable_to_asset_path,True)

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
    if use_proxy:
        set_geonode_input(mod, "Use Proxy Mesh", True)
    else:
        set_geonode_input(mod, "Use Proxy Mesh", False)
        
    if hide_buildable:
        obj.hide_viewport = True
    #progress_in = 100
    print(f"Imported {name} from save file")

def import_powerlines(name: str,inst_splines: list,transform: list):       
    #global progress_in
    
    hide_buildable = bpy.context.scene.sf_importer_props.hide_buildable
    
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
    get_or_create_collection("Heavyweights","Import",col_color = "COLOR_05")
    get_or_create_collection("Splines","Heavyweights",col_color = "COLOR_07")
    get_or_create_collection(name,"Splines",col_color = "COLOR_07").objects.link(obj)
    
    node_group = bpy.data.node_groups["Buildables From Spline"]
    mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    mod.node_group = node_group

    set_geonode_input(mod, "Is Powerline", True)
    
    if hide_buildable:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        obj.hide_viewport = True
    
    #progress_in = 100
    print(f"Imported {name} from save file")

def import_conveyor_chain( 
    transform: s.FTransform3f, 
    points:list,
    chain_belt_points:list,
    chain_lift_points:list,
    type_mk:list,
    top_rot_list:list,
    passthrough:list,
    rot_list:list,
    primary_colors:list,
    secondary_colors:list,
    paint_type:list
    ):
    #global progress_in
    
    use_proxy = bpy.context.scene.sf_importer_props.use_proxy
    hide_buildable = bpy.context.scene.sf_importer_props.hide_buildable
    
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
    get_or_create_collection("Heavyweights","Import",col_color = "COLOR_05")
    get_or_create_collection("Splines","Heavyweights",col_color = "COLOR_07")
    get_or_create_collection("ConveyorChain","Splines",col_color = "COLOR_07").objects.link(obj)
    
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
    
    try:
        curve_data.attributes.new("lift_rot", "FLOAT_VECTOR", "CURVE")
        flat = [c for vec in rot_list for c in vec]
        curve_data.attributes["lift_rot"].data.foreach_set("vector", flat)
    except Exception as e:
            print("failed to create scale attribute",e)
    
    try:   
        curve_data.attributes.new("primary_color", "FLOAT_COLOR", "CURVE")
        flat = [c for rgba in primary_colors for c in rgba]
        curve_data.attributes["primary_color"].data.foreach_set("color", flat)
    except Exception as e:
        print("failed to create scale attribute",e)
    
    try:   
        curve_data.attributes.new("secondary_color", "FLOAT_COLOR", "CURVE")
        flat = [c for rgba in secondary_colors for c in rgba]
        curve_data.attributes["secondary_color"].data.foreach_set("color", flat)
    except Exception as e:
        print("failed to create scale attribute",e)
    
    try:
        curve_data.attributes.new("paint_index", "INT", "CURVE")
        flat = [idx for idx in paint_type]
        curve_data.attributes["paint_index"].data.foreach_set("value", flat)
    except Exception as e:
        print("failed to create scale attribute",e)
    
    node_group = bpy.data.node_groups["Conveyer Cains From Spline"]
    mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    mod.node_group = node_group
    
    set_geonode_input(mod, "Lifts Collection", bpy.data.collections.get("Lifts"))
    set_geonode_input(mod, "Lift Parts Collection", bpy.data.collections.get("LiftParts"))
    set_geonode_input(mod, "Belts Collection", bpy.data.collections.get("ConveyorBelts"))
    if use_proxy:
        set_geonode_input(mod, "Use Proxy Mesh", True)
    else:
        set_geonode_input(mod, "Use Proxy Mesh", False)
        
    if hide_buildable:
        obj.hide_viewport = True
    
    #progress_in = 100
    print(f"Imported Conveyor chain from save file")
