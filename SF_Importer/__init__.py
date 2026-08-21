import bpy 
from bpy.types import Operator, AddonPreferences,PropertyGroup,Panel # type: ignore
from bpy.props import StringProperty, IntProperty, BoolProperty # type: ignore

import threading
import time
import functools
from datetime import datetime
import json
from mathutils import Quaternion, Matrix, Vector
from pathlib import Path
import math
import satisfactory_save as s
import time


from .get_models import *
from .import_save_data import *
from .populate_buildable_to_asset import populate_buildable_to_asset
from .get_lib_assets import get_lib_assets
from .get_par_materials import get_par_materials

# Global variables to save progress
total_entries = 0
current_buildable = ""
progress = 0.0
progress_in = 0.0
start_process = 0.0
execution_time = 0.0
per_time = []
total_buildables = 0
total = 0
total_instances = 0
total_all_instances = 0
total_imported = 0
is_scanning = False
is_get_scanning = False
is_asset_building = False
stop_requested = False
stop_get_requested = False
stop_building_requested = False
buildable_to_asset_path = ""
x_corr = -500.0
y_corr = 2800.0
distance = 1000.0
obj_name=""
prop_parent = None
prop_parent_name = ""
build_total = 0
total_buildings_imported = 0
build_execution_time = 0.0
marking_asset = False
is_appended = 0
mapped_build = set()

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

def remap(value, from_min, from_max, to_min, to_max):
    from_span = from_max - from_min
    to_span = to_max - to_min
    value_scaled = float(value - from_min) / float(from_span)
    return to_min + (value_scaled * to_span)

def update_ui():
    # Force UI update
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    
    if is_scanning:
        return 0.1  # Call every 0.1 seconds
    elif is_get_scanning:
        return 0.1  # Call every 0.1 seconds
    elif is_asset_building:
        return 0.1  # Call every 0.1 seconds
    else:
        return None  # Stop the timer

class SF_Importer_Properties(PropertyGroup):
    save_path: bpy.props.StringProperty( #type: ignore
        name="Save Path",
        description="The save file you want to import factory data from",
        subtype = "FILE_PATH",
        options = {"LIBRARY_EDITABLE"},
        default = "C:/tmp/",
        maxlen = 1024
    )
    
    get_lightweight: bpy.props.BoolProperty(
        name="Lightweight Buildables",
        description="Get lightweight buildables used in save file. e.g. foundations, walls, pillers, etc ",
        default=False
    ) # type: ignore
    
    get_heavyweight: bpy.props.BoolProperty(
        name="Heavyweight Buildables",
        description="Get heavyweigh buildables used in save file. e.g. construtor, smelter, pipeHyperSupport, etc ",
        default=False
    ) # type: ignore
    
    get_signs: bpy.props.BoolProperty(
        name="Sign Buildables",
        description="Get sign buildables used in save file. e.g. medium signs, large signs, etc ",
        default=False
    ) # type: ignore
    
    get_splines: bpy.props.BoolProperty(
        name="Spline Buildables",
        description="Get spline buildables used in save file. e.g. conveyor belts, pipes, powerlines, etc ",
        default=False
    ) # type: ignore
    
    hide_buildable: bpy.props.BoolProperty(
        name="Hide Buildables",
        description="Hide buildable on import for buildables with a lot of instances for viewport proformace",
        default=False
    ) # type: ignore
    
    use_proxy: bpy.props.BoolProperty(
        name="Use Proxy Mesh",
        description="Use proxy mesh for viewport proformance. Use main mesh for render",
        default=False
    ) # type: ignore
    
    mark_as_asset: bpy.props.BoolProperty(
        name="Mark as Asset",
        description="Mark the imported models as asset and add to SF asset Library",
        default=False
    ) # type: ignore
    
    build_materials: bpy.props.BoolProperty(
        name="Build Materials",
        description="Build materials for the imported models",
        default=False
    ) # type: ignore
    
    get_models_from_library: bpy.props.BoolProperty(
        name="Use Library Models",
        description="Append models from SF_Asset_Lib file before importing save data instead of using models in current blend file. NOTE: The more buildable types in the save, the longer it will take and blender UI will be while it appends. Uses default_mesh if no models in blend file or SF_Asset_Lib.",
        default=False
    ) # type: ignore

class SFImportPreferences(AddonPreferences):
    bl_idname = __package__
    
    sf_asset_lib_path: StringProperty( #type: ignore
        name="SF Asset Library Path",
        description="Path to the Satisfactory asset library folder. this is where the addon will copy the asset library files to. e.g. C:/Users/username/Documents/Blender/SF Asset Lib. Note: if there is already an 'SF Asset Lib' and 'blender_assets.cats.txt' file in the dir, it will be overwritten.",
        subtype = "DIR_PATH",
        options = {"LIBRARY_EDITABLE"},
        default = "",
        maxlen = 1024
    )
    
    sf_asset_export_path: StringProperty( #type: ignore
        name="SF Asset Export Path",
        description="Path to the folder where Fmodel exported Satisfactory assets.",
        subtype = "DIR_PATH",
        options = {"LIBRARY_EDITABLE"},
        default = "",
        maxlen = 1024
    )
    
    custom_buildable_to_asset_path: StringProperty( #type: ignore
        name="Buildable To Asset Path",
        description="Path to the folder the custom buildable_to_asset.json file stored.",
        subtype = "DIR_PATH",
        options = {"LIBRARY_EDITABLE"},
        default = "",
        maxlen = 1024
    )
    
    def draw(self, context):
        global total_entries
        layout = self.layout
        layout.label(text="Setup SF Importer")
        
        # path to the Fmodel export Satisfactory assets
        layout.prop(self, "sf_asset_export_path", text="SF Asset Exported Path")
        
        # buildable to asset path
        bta_box = layout.box()
        bta_split = bta_box.split(factor=0.5)
        bta_split.column().label(text="Generate buildable_to_asset file")
        bta_col = bta_split.column(align=True)
        if total_entries:
            bta_col.alignment = 'RIGHT'
            bta_col.label(text=f"Total Entries: {total_entries}")
        bta_box.prop(self, "custom_buildable_to_asset_path", text="Custom buildable to Asset Path")
        
        bta_btt_text = "Generate buildable_to_asset.json"
        if self.custom_buildable_to_asset_path:
            bta_btt_text = "Generate custom buildable_to_asset.json"
            if Path(self.custom_buildable_to_asset_path, "buildable_to_asset.json").exists():
                bta_btt_text = "Overwrite custom buildable_to_asset.json"
        elif Path(Path(__file__).parent, "buildable_to_asset.json").exists():
            bta_btt_text = "Overwrite buildable_to_asset.json"
        bta_box.operator("sf_importer.generate_buildable_to_asset", text=bta_btt_text)
        
        # path to the Satisfactory asset library folder
        lb_btt_text = "Copy asset library files to asset library path"
        if not self.sf_asset_lib_path:
            lb_btt_text = "Copy asset library files to asset library path (set path first)"
        elif Path(self.sf_asset_lib_path,"SF_Asset_Lib.blend").exists():
            if not Path(self.sf_asset_lib_path,"blender_assets.cats.txt").exists():
                lb_btt_text = "Overwrite asset library files in asset library path (blender_assets.cats.txt missing)"
            else:
                lb_btt_text = "Overwrite asset library files in asset library path"
        
        # button to copy, files from addon file to the asset library path
        lib_box = layout.box()
        lib_box.label(text="Copy asset library files to asset library path")
        lib_box.prop(self, "sf_asset_lib_path", text="Asset Library Path")
        lib_box.operator("sf_importer.copy_blend_to_asset_lib", text=lb_btt_text)

# sf_importer.generate_buildable_to_asset
class GenerateBuildableToAsset(Operator):
    bl_idname = "sf_importer.generate_buildable_to_asset"
    bl_label = "Generate buildable_to_asset.json"

    def execute(self, context):
        global total_entries,buildable_to_asset_path
        prefs = context.preferences.addons[__package__].preferences
        sf_asset_export_path = Path(prefs.sf_asset_export_path)
        
        buildable_to_asset_path = ""
        
        if not prefs.sf_asset_export_path:
            self.report({'ERROR'}, "SF asset export path is not set.")
            return {'CANCELLED'}
        if not sf_asset_export_path.exists():
            self.report({'ERROR'}, f"SF asset export path does not exist: {sf_asset_export_path}")
            return {'CANCELLED'}
        
        if not prefs.custom_buildable_to_asset_path:
            total_entries = populate_buildable_to_asset(sf_asset_export_path)
        elif prefs.custom_buildable_to_asset_path:
            custom_buildable_to_asset_path = Path(prefs.custom_buildable_to_asset_path)
            if not custom_buildable_to_asset_path.exists():
                self.report({'ERROR'}, f"Custom buildable_to_asset.json path does not exist: {custom_buildable_to_asset_path}")
                return {'CANCELLED'}
            total_entries = populate_buildable_to_asset(sf_asset_export_path, custom_buildable_to_asset_path)
            buildable_to_asset_path = os.path.join(prefs.custom_buildable_to_asset_path, "buildable_to_asset.json")

        self.report({'INFO'}, f"buildable_to_asset.json file generated at: {buildable_to_asset_path}")
        return {'FINISHED'}
    
def copy_blend_to_asset_lib(asset_lib_path: Path):
    # Copy the SF_Asset_Lib.blend and blender_assets.cats.txt files to the asset library path
    source_blend = Path(__file__).parent / "SF Asset Lib" / "SF_Asset_Lib.blend"
    source_cats = Path(__file__).parent / "SF Asset Lib" / "blender_assets.cats.txt"
    
    dest_blend = asset_lib_path / "SF_Asset_Lib.blend"
    dest_cats = asset_lib_path / "blender_assets.cats.txt"
    
    if not source_blend.exists() or not source_cats.exists():
        raise FileNotFoundError("Source asset library files not found.")
    
    # Copy the files
    import shutil
    shutil.copy(source_blend, dest_blend)
    shutil.copy(source_cats, dest_cats)

# sf_importer.copy_blend_to_asset_lib
class CopyBlendToAssetLib(Operator):
    bl_idname = "sf_importer.copy_blend_to_asset_lib"
    bl_label = "Copy asset library files to asset library path"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        if not prefs.sf_asset_lib_path:
            self.report({'ERROR'}, "Asset library path is not set in the addon preferences.")
            return {'CANCELLED'}
        lib_path = Path(prefs.sf_asset_lib_path)
        if not lib_path.exists():
            self.report({'ERROR'}, f"Asset library path does not exist: {lib_path}")
            return {'CANCELLED'}
        copy_blend_to_asset_lib(lib_path)
        self.report({'INFO'}, f"Asset library files copied to: {lib_path}")
        return {'FINISHED'}


def append_assets(cls: str,map_file,is_light:bool = False,is_sign:bool = False):
    global is_appended,mapped_build
    
    name = map_file.get(cls)
    mesh = None
    if "Build_PipelinePumpMk2" in cls:
        name = map_file.get("Build_PipelinePumpMK2_C")
    
    if "Build_PipelineMK2_NoIndicator" in cls:
        name = map_file.get("Build_PipelineMK2_C")
    if "Build_Pipeline_NoIndicator" in cls:
        name = map_file.get("Build_Pipeline_C")
    if not name:
        print("skipping: ",cls)
        is_appended = 3
    else:
        mesh = name.get("ObjectName")
        
    if mesh:
        if mesh in mapped_build:
            print(f"{mesh} already appended by {cls}")
            is_appended = 4
        else:
            
            print(f"Appending {cls} models",mesh)
            if is_light:
                get_lib_result = get_lib_assets(data_type="Collection",asset_name=mesh,asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            else:
                get_lib_result = get_lib_assets(data_type="Collection",asset_name=mesh,asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend",col_type=True)
                
            if get_lib_result:
                print(get_lib_result)
                is_appended = 1
        
            mapped_build.add(mesh)

def import_lightweights_task(save: s.SaveGame, color_map: dict,get_models_from_library,map_file):
    global progress,progress_in, is_scanning, stop_requested,run_once,is_appended
    global total,total_imported,total_instances,current_buildable,buildable_to_asset_path
    progress = 0.0
    progress_in = 0.0
    cls = save.allSaveObjects()
    # get the lightweight buildable subsystem
    lbs = get_lbs(save)
    instances_by_class_ref = lbs.mBuildableClassToInstanceArray
    
    total = 0
    for buildable in list(instances_by_class_ref.Keys):
        class_path = buildable.PathName
        if not class_path:
            raise Exception("Missing class path, how can this happen?")
        instances = instances_by_class_ref[buildable]
        if not instances:
            continue    
        total += 1
    
    count = 0
    for i,class_ref in enumerate(list(instances_by_class_ref.Keys),1):
        if stop_requested:
            progress = 0.0
            break
        progress_in = 0.0
        class_path = class_ref.PathName
    
        if not class_path:
            raise Exception("Missing class path, how can this happen?")
    
        instances = instances_by_class_ref[class_ref]
        total_instances = len(instances)
        name = class_path.split(".")[-1]
    
        # if 'Beam' not in name:
        #    continue;
    
        if not instances:
            continue  
        
        #tmp_instances = []
        #for ints in instances:
        #    if x_corr <= ints.X <= x_corr + distance:
        #        tmp_instances.append(ints)
        
        current_buildable = f"{name}: {total_instances} instances"  
        verts, rotations, scales = map(
            list, zip(*(read_transform(i.Transform) for i in instances))
        )
    
        colors = [read_colors(i,color_map) for i in instances]
        primary_colors, secondary_colors, paint_type = zip(*colors)   
    
        lengths = [read_prop(i,"BeamLength") for i in instances]
        if 'Build_Beam_Painted_C' in name or 'Build_Beam_C' == name:
            lengths = [read_prop(i,"BeamLength") for i in instances]
            lengths = [l / 4.0 for l in lengths]
            
        prop_attr = []
        if "Build_Beam_Shelf_" in name:
            beam_type = [1] * len(instances)
            prop_attr.append({
                "beam_type" : beam_type,
                    "type":["INT","value"]
            })
        stencil_dir = Path(__file__).parent / "stencil_map.json"
        with open(stencil_dir, 'r', encoding='utf-8') as f:
            stencil_map = json.load(f)
        pattern_rot = [int(read_prop(i,"PatternRotation")) for i in instances]
        pattern_desc = []
        for i in instances:
            prop_result = read_prop(i,"PatternDesc")
            if type(prop_result) == str:
                stencil_id = stencil_map.get(prop_result.split('.')[-1],20)
                if stencil_id:
                    pattern_desc.append(stencil_id)
            else:
                pattern_desc.append(24)
        
        if pattern_desc:
            prop_attr.append({
                "pattern_desc" : pattern_desc,
                    "type":["INT","value"]
            })
        
        if pattern_rot:
            prop_attr.append({
                "pattern_rot" : pattern_rot,
                    "type":["INT","value"]
            })
        
        if get_models_from_library:
            progress_in = 50.0
            is_appended = 0
            bpy.app.timers.register(functools.partial(
                append_assets, 
                name,
                map_file,
                True
                ), first_interval=0)
            time.sleep(0.1)
        
            while is_appended == 0:
                if stop_requested:
                    break
                print("waiting for model to finish appending..")
                time.sleep(0.2)
        else:
            progress_in = 50.0
        
        bpy.app.timers.register(functools.partial(
            create_buildable_object, 
            name,
            verts,
            rotations,
            scales,
            primary_colors,
            secondary_colors,
            paint_type,
            lengths,
            prop_attr,
            buildable_to_asset_path=buildable_to_asset_path
            ), first_interval=0)
        progress_in = 100.0
        #print(class_path.split('.')[1],len(instances))
        time.sleep(0.1)
        
        #while not bpy.data.objects.get(name+"_Points"):
        #    if stop_building_requested:
        #        break 
        #    print("waiting for model to finish importing")
        #    time.sleep(0.5)   
        
        count += 1
        total_imported += 1#count
        progress = (total_imported / total) * 100
        
    #if not stop_requested:
    #    progress = 100.0
    #is_scanning = False
    #stop_requested = False
    bpy.app.timers.register(update_ui)

def import_heavyweights_task(save: s.SaveGame, color_map: dict,get_models_from_library,map_file):
    global progress, is_scanning, stop_requested,run_once,total,total_imported,current_buildable,is_appended
    global total_instances,current_buildable,progress_in,buildable_to_asset_path
    save_objects = save.allSaveObjects()
    progress = 0.0
    progress_in = 0.0
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
    float_attributes = [
        "mHeight",
        "mHeightOfCabin",
        "mLaunchAngle",
        "mSnappedBuildingThickness",
        "mSelectedPoleVersion",
        "mHighlightEffectState",
        "mVerticalAngle",
        "mFixtureAngle"
    ]
    vec_attributes = [
            "mPoleScale",
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
                        else:
                            hub_stage = [5]

    total_fact_instances = 0
    for factory in all_classes:
        ex = False
        for exc in exclude_factory:
            if exc in factory:
                ex = True
        if not ex and not factory.startswith('Build_StandaloneWidgetSign_') and not factory.startswith('Build_PowerLine_') and not any(building in factory for building in spline_buildables):
            total_fact_instances += 1
    total = total_fact_instances
    
    count = 0
    for factory in all_classes:
        if stop_requested:
            progress = 0.0
            break
        instances = [[], []] # --> [transforms], [actors]
        
        # group buildable instances by buildable class 
        for factory_class in factory_classes:
            header = factory_class.Header
            transform = header.Transform
            actor = factory_class.Object
            cls_name = header.ObjectHeader.Reference.PathName
            
            if factory in cls_name:
                instances[0].append(transform)
                instances[1].append(actor)
        
        total_instances = len(instances[0])
        
        if not factory.startswith('Build_StandaloneWidgetSign_') and not factory.startswith('Build_PowerLine_') and not any(building in factory for building in spline_buildables):
            prop_attr = []
            height_attr = []
            passthorugh_thickness_attr = []
            pole_scale_attr = [[0.0,0.0]] * total_instances
            attr_dict = {}
            needs_attr = []
            attr_used = set()
            pole_scale_used = False
            passthrough_type = [0] * total_instances
            progress_in = 0.0
            
            current_buildable = f"{factory}: {total_instances} instances" 
                            
            for i in float_attributes:
                attr_dict.update({i:[None] * total_instances})
            
            skip = False
            for exc in exclude_factory:
                if exc in factory:
                    print(f"Excluding {exc}")
                    skip = True
            if skip:
                continue
            
            print(factory,f" has {len(instances[1])} instances")
            count_p = 0
            total_instances = len(instances[0])
            found_prop = False
            for idx,actor in enumerate(instances[1]):
                if stop_requested:
                    progress = 0.0
                    break
                height_check = False
                pole_scale_check = False
                attr_check = {}
                if "Build_FoundationPassthrough_Hypertube_C" in factory:
                    passthrough_type[idx] = 1
                else:
                    passthrough_type[idx] = 0
                
                for prop in actor.Properties:
                    prop_name = prop.Name.Name
                    attr_check[prop_name] = 0
                    attr_value= None
                    for i in float_attributes:
                        if i == prop_name:
                            attr_value = float(prop.Value)
                    
                    if attr_value != None:
                        attr_dict[prop_name][idx] = attr_value
                        attr_used.add(prop_name)  
                        if not found_prop:
                            found_prop = True
                            
                    #if attr_value:
                    #    if not attr_dict.get(prop_name):
                    #        attr_dict.update({prop_name:[]})
                    #    attr_dict[prop_name].append(attr_value)
                    #    attr_check[prop_name] = 1
                    #    needs_attr.append(factory)
                    #    attr_used.add(prop_name)  
                    #else:
                    #    if not attr_dict.get(prop_name):
                    #        attr_dict.update({prop_name:[]})
                    #    attr_dict[prop_name].append(0) 
                        
                    if 'mPoleScale' in prop_name:
                        pole_scale_attr[idx] = [
                            prop.Value.Data.X,
                            prop.Value.Data.Y
                        ]
                        pole_scale_used = True
                        #pole_scale_check = True
                        
                #if not pole_scale_check:
                #    pole_scale_attr.extend([0.0,0.0])
                
                for i in attr_dict:
                    if attr_dict[i][idx] == None:
                        attr_dict[i][idx] = 0.0
                        if "mFixtureAngle" in i:
                            attr_dict[i][idx] = 24.0
                
                #for i in attr_dict:
                #    check = attr_check.get(i,2)
                #    if check != 1:
                #        if "mFixtureAngle" in i:
                #            attr_dict[i].append(45.0)
                #        else:
                #            attr_dict[i].append(0.0)
                        
                verts, rotations, scales = map(
                    list, zip(*(read_transform(i) for i in instances[0]))
                )
                count_p += 1
                progress_in = (count_p / total_instances) * 98
            
            for att_u in attr_used:
                if len(attr_dict[att_u]) > total_instances:
                    print("⚠️higher than total",len(attr_dict[att_u]),total_instances)
                    #attr_dict[att_u] = attr_dict[att_u][:total_instances]
                elif len(attr_dict[att_u]) < total_instances:
                    print("⚠️lower than total",len(attr_dict[att_u]),total_instances)
                    #diff = total_instances - len(attr_dict[att_u])
                    #attr_dict[att_u].extend(attr_dict[att_u][:1]*diff)
                
                prop_attr.append({
                        att_u : attr_dict[att_u],
                        "type":["FLOAT","value"]
                    })
                
            if pole_scale_used:
                prop_attr.append({
                        "pole_scale" : [v for vec in pole_scale_attr for v in vec],
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
            

            if get_models_from_library:
                is_appended = 0
                bpy.app.timers.register(functools.partial(
                    append_assets, 
                    factory,
                    map_file
                    ), first_interval=0)
                time.sleep(0.1)

                while is_appended == 0:
                    if stop_requested:
                        break
                    print("waiting for model to finish appending..")
                    time.sleep(0.2)
            
            progress_in = 99
            bpy.app.timers.register(functools.partial(
                create_buildable_object, 
                factory,
                verts,
                rotations,
                scales,
                primary_colors,
                secondary_colors,
                paint_type,
                prop_attr=prop_attr,
                is_heavy = True,
                buildable_to_asset_path=buildable_to_asset_path
                ), first_interval=0)
            progress_in = 100.0
            time.sleep(0.1)
            count += 1
            total_imported += 1
            
            progress = (total_imported / total) * 100
            
    #if not stop_requested:
    #    progress = 100.0
    #is_scanning = False
    #stop_requested = False
    bpy.app.timers.register(update_ui)

def import_signs_task(save: s.SaveGame,get_models_from_library,map_file):
    global progress, is_scanning, stop_requested,run_once,total,total_imported,is_appended
    global current_buildable,total_instances,current_buildable,progress_in,buildable_to_asset_path
    save_objects = save.allSaveObjects()
    progress = 0.0
    progress_in = 0.0
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
    
    EX_PROP_BUILDS = [
        "Build_ConveyorPole_C",
        "Build_PipelineSupport_C",
        "Build_SignPole_",
        "Build_PipeHyperSupport_C"
    ]
    
    sign_layouts = {}
    sign_layout_path = Path(__file__).parent / "sign_layouts.json"
    with open(    sign_layout_path, 'r', encoding='utf-8') as f:
        sign_layouts = json.load(f)
        
    for obj in save_objects:
        if not obj.isActor():
            continue    
    
        header = obj.Header
        className =  header.ObjectHeader.ClassName
        classRef =  header.ObjectHeader.Reference.PathName
        actor = obj.Object  
        
        if className.startswith('/Game/FactoryGame/Buildable/') and '.Build_StandaloneWidgetSign_' in className and className.endswith('_C'):
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)

    total_sign_instances = 0
    for factory in all_classes:
        ex = False
        for exc in exclude_factory:
            if exc in factory:
                ex = True
        if not ex:
            total_sign_instances += 1
    total = total_sign_instances
    
    for factory in all_classes:
        if stop_requested:
            progress = 0.0
            break
        progress_in = 0.0
        
        current_buildable = f"{factory}: {total_instances} instances" 
        instances = [[], []] # --> [transforms], [actors]
        
        # group buildable instances by buildable class 
        for factory_class in factory_classes:
            header = factory_class.Header
            transform = header.Transform
            actor = factory_class.Object
            cls_name = header.ObjectHeader.Reference.PathName
            
            if factory in cls_name:
                instances[0].append(transform)
                instances[1].append(actor)
        
        total_instances = len(instances[0])
        prop_attr = []
        color_attr = []
        text_attr= []
        icons_attr = []
        ems_attr = []
        glos_attr = []
        idx_map = {key: i for i, key in enumerate(sign_layouts)}
        layout_data = sign_layouts[factory]
        sign_lay_idx = idx_map.get(factory)
        layouts_attr = []
        layouts_text_attr = []
        color_idx_f = []
        color_idx_b = []
        color_idx_a = []
        verts, rotations, scales = [],[],[]
    
        count_p = 0
        for actor in instances[1]:
            if stop_requested:
                progress = 0.0
                break
            ems_check = False
            glos_check = False
            aux_check = False
            for prop in actor.Properties:
                if 'mSoftActivePrefabLayout' in prop.Name.Name:
                    layout_name = prop.Value.AssetPath.AssetName.Name
                    layout_idx = layout_data[layout_name]["layout"]
                    layout_text = layout_data[layout_name]["Text"]
                    if layout_text:
                        lt1 = 1 if layout_text.get('Text1') else 0
                        lt2 = 1 if layout_text.get('Text2') else 0
                        lt3 = 1 if layout_text.get('Text3') else 0
                        layouts_text_attr.extend([lt1,lt2,lt3])
                    else:
                        layouts_text_attr.extend([0,0,0])
                    layouts_attr.append(sign_lay_idx)
                    layouts_attr.append(layout_idx)
                    #print(f"{prop.Name.Name}: {prop.Value.AssetPath.AssetName.Name}")
                    # TODO use a layout map
                
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
            
            count_p += 1
            progress_in = (count_p / total_instances) * 98
            
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
        prop_attr.append({
            "layout" : layouts_attr,
            "type":["FLOAT2","vector"]
        })
        prop_attr.append({
            "layout_t" : layouts_text_attr,
            "type":["FLOAT_VECTOR","vector"]
        })
        
        #text_id = 0 
        ## text attributes
        #prop_attr.append({
        #    "text_id" : [ (text_id + 1) if len(i) == 3 else (text_id + 1) for i in text_attr],
        #    "type":["FLOAT","value"]
        #    })
        prop_attr.append({
            "text" : [ (i[0],i[1],i[2]) if len(i) == 3 else (i[0],i[1],"") for i in text_attr],
            "type":["FLOAT_VECTOR","vector"]
            })
        
        icons_attr_final = []
        for icons in icons_attr:
            if len(icons) == 2:
                icons_attr_final.extend([icons[0],icons[1],0])
            else:
                icons_attr_final.extend(icons)
        # icon attributes
        prop_attr.append({
            "icons" : icons_attr_final,
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
        
        if get_models_from_library:
            is_appended = 0
            bpy.app.timers.register(functools.partial(
                append_assets, 
                factory,
                map_file,
                is_sign=True
                ), first_interval=0)
            time.sleep(0.1)
        
            while is_appended == 0:
                if stop_requested:
                    break
                print("waiting for model to finish appending..")
                time.sleep(0.2)
                
        progress_in = 99
        bpy.app.timers.register(functools.partial(
            create_buildable_object, 
            factory,
            verts,
            rotations,
            scales,
            prop_attr=prop_attr,
            buildable_to_asset_path=buildable_to_asset_path
            ), first_interval=0)
        progress_in = 100.0
        time.sleep(0.1)
        total_imported += 1
        progress = (total_imported / total) * 100
        
    bpy.app.timers.register(update_ui)

def import_splines_task(save: s.SaveGame, color_map: dict,get_models_from_library,map_file):
    global progress, is_scanning, stop_requested,run_once,total,total_imported,is_appended
    global progress_in,total_instances,current_buildable,buildable_to_asset_path
    save_objects = save.allSaveObjects()
    progress = 0.0
    progress_in = 0.0
    all_classes = set() # all buildable classes in the save
    factory_classes = [] # all factory buildable instances
    exclude_factory = [ # exclude from default importing method 
        #"Build_RailroadTrack",
        #"Build_RailroadTrackIntegrated_C_Points",
        #"Build_PowerLine_C",
        #"Build_ConveyorBelt",
        #"Build_Pipeline_",
        #"Build_PipelineMK2",
        #"Build_PipeHyper_C",
        #"Build_ConveyorLift",
        "Build_PipelineFlowIndicator_C"
    ]
    spline_buildables = [
        "Build_PipelineMK2_",
        "Build_Pipeline_",
        "Build_RailroadTrack",
        "Build_PipeHyper_C",
    ]
    conveyor_dict = {}
    
    for obj in save_objects:
        if not obj.isActor():
            continue    
    
        header = obj.Header
        className =  header.ObjectHeader.ClassName
        classRef =  header.ObjectHeader.Reference.PathName
        actor = obj.Object  
        
        if className.startswith('/Game/FactoryGame/Buildable/') and '.Build_' in className and className.endswith('_C'):
            all_classes.add(className.split('.')[-1]) # instances
            factory_classes.append(obj) # buildables
        
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

    tot_chains = 0
    for obj in save.mPersistentAndRuntimeData.SaveObjects:
        if not obj.isActor():
            continue
        header = obj.Header
        className =  header.ObjectHeader.ClassName
        
        if className.startswith( '/Script/FactoryGame.FGConveyorChainActor'):
            tot_chains += 1
    
    total_spline_instances = 0
    total_spline_buildables = 0
    for factory in all_classes:
        for factory_class in factory_classes:
            header = factory_class.Header
            cls_name = header.ObjectHeader.Reference.PathName
            ex = False
            for exc in exclude_factory:
                if exc in factory:
                    ex = True
            if factory in cls_name and not ex:
                if any(building in factory for building in spline_buildables) or factory.startswith('Build_PowerLine_'):
                    total_spline_instances += 1
        ex = any(exc in factory for exc in exclude_factory)
        if not ex:
            if any(building in factory for building in spline_buildables) or factory.startswith('Build_PowerLine_'):
                total_spline_buildables += 1
    total = total_spline_buildables + tot_chains
    total_types = 0
    total_types_imported = 0
    if tot_chains > 0:
        total_types = 1
    total_types += total_spline_buildables
    total_percent = 100 / total_types
    print("    total_percent: ",total_percent)
    spline_set = set()
    # conveyor belt chains   
    has_con = False   
    for obj in save.mPersistentAndRuntimeData.SaveObjects:
        if stop_requested:
            progress = 0.0
            break     
        if not obj.isActor():
            continue
        
        header = obj.Header
        transform = header.Transform
        className =  header.ObjectHeader.ClassName
        actor = obj.Object 
        
        
        if className.startswith( '/Script/FactoryGame.FGConveyorChainActor'):
            has_con = True
            spline_set.add("c_chain")
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
            
            total_cons = len(actor.mChainSplineSegments)
            current_buildable = f"Conveyor chain: {total_cons} segments" 
            count_p = 0
            for i, seg in enumerate(reversed(actor.mChainSplineSegments)):
                if stop_requested:
                    progress = 0.0
                    break
                conveyor_ref = seg.ConveyorBase.PathName
                conveyor_name = seg.ConveyorBase.PathName.split('_')[2]
                conveyor_mk = conveyor_name[-1:]
                is_belt = True if "Belt" in conveyor_name else False
                #conveyor_attr.append(0)
                top_rot = None
                
                conveyor_inst = conveyor_dict.get(conveyor_ref,[])
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

                count_p += 1
                progress_in = (count_p / total_cons) * 98

            passthrough.extend(passthrough_lift)
            type_mk.extend(type_mk_belt) 
            type_mk.extend(type_mk_lift) 
            
            rot_list.extend(belt_rot)
            rot_list.extend(lift_rot)
            top_rot_list.extend(belt_top_rot)    
            top_rot_list.extend(lift_top_rot)
            
            progress_in = 99
            bpy.app.timers.register(
                functools.partial(
                    import_conveyor_chain,
                    transform,
                    points,
                    chain_belt_points,
                    chain_lift_points,
                    type_mk,
                    top_rot_list,
                    passthrough,
                    rot_list,
                    primary_colors,
                    secondary_colors,
                    paint_type
                    ), first_interval=0)
            progress_in = 100.0
            time.sleep(0.1)
            total_imported += 1#count
            progress = (total_imported / total) * total_percent
    
    #total_types_imported = len(spline_set)
            
    count = 0
    
    for factory in all_classes:
        total_types_imported = len(spline_set)
        print(total_types_imported)
        if stop_requested:
            progress = 0.0
            break
        instances = [[], []] # --> [transforms], [actors]
        
        # group buildable instances by buildable class 
        for factory_class in factory_classes:
            header = factory_class.Header
            transform = header.Transform
            actor = factory_class.Object
            cls_name = header.ObjectHeader.Reference.PathName
            
            if factory in cls_name:
                instances[0].append(transform)
                instances[1].append(actor)
        
        total_instances = len(instances[0])
        
        if factory.startswith('Build_PowerLine_'):
            spline_set.add(factory)
            transform = instances[0]
            actors = instances[1]
            
            current_buildable = f"{factory}: {total_instances} splines" 
            progress_in = 0.0
            for i,actor in enumerate(actors):
                if stop_requested:
                    progress = 0.0
                    break
                transform = instances[0][i]
                passthroughs = ""
                flow_indicator = False
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
            
                progress_in = 50
                bpy.app.timers.register(
                    functools.partial(
                        import_powerlines,
                        factory,
                        inst_splines,
                        transform
                        ), first_interval=0)
                progress_in = 100.0
                time.sleep(0.1)
            count += 1
            total_imported += 1#count
            progress = (total_percent * total_types_imported)+(total_imported / total) * total_percent
                #import_powerlines(factory, instances)
                    
        if any(building in factory for building in spline_buildables):
            spline_set.add(factory)
            transform = instances[0]
            actors = instances[1]
            current_buildable = f"{factory}: {total_instances} splines" 
            progress_in = 0.0
            count_p = 0
            
            if get_models_from_library:
                is_appended = 0
                bpy.app.timers.register(functools.partial(
                    append_assets, 
                    factory,
                    map_file
                    ), first_interval=0)
                time.sleep(0.1)
            
                while is_appended == 0:
                    if stop_requested:
                        break
                    print("waiting for model to finish appending..")
                    time.sleep(0.2)
            
            for i,actor in enumerate(actors): # per spline/instance
                if stop_requested:
                    progress = 0.0
                    break
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
                #primary_colors, secondary_colors, paint_type = zip(*colors)
                
                props = actor.Properties
                for prop in props:
                    if stop_requested:
                        progress = 0.0
                        break
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

                
                bpy.app.timers.register(
                    functools.partial(
                        import_spline_buildables,
                        factory,
                        colors,
                        spline_points,
                        transform,
                        passthroughs,
                        flow_indicator,
                        buildable_to_asset_path
                        ), first_interval=0)
                #progress_in = 100.0
                time.sleep(0.1)
                
                count_p += 1
                progress_in = (count_p / total_instances) * 100
                
            count += 1
            total_imported += 1#count
            progress = (total_percent * total_types_imported)+(total_imported / total) * total_percent
    bpy.app.timers.register(update_ui)

def import_save_task(save: s.SaveGame, color_map: dict,get_models_from_library):
    global progress,total,total_imported,is_scanning,stop_requested,execution_time,per_time
    start_time = datetime.now()
    execution_time = 0.0
    progress = 0.0
    final_total = 0
    total = 0
    current_imported = 0
    total_imported = 0
    
    light_end_time = None
    heavy_end_time = None
    sign_end_time = None
    spline_end_time = None
    partial_time = [""]*4
    
    get_lightweight = bpy.context.scene.sf_importer_props.get_lightweight
    get_heavyweight = bpy.context.scene.sf_importer_props.get_heavyweight
    get_signs = bpy.context.scene.sf_importer_props.get_signs
    get_splines = bpy.context.scene.sf_importer_props.get_splines
    
    with open(buildable_to_asset_path, 'r', encoding='utf-8') as f:
        map_file = json.load(f)
    
    if get_lightweight:
        import_lightweights_task(save, color_map,get_models_from_library,map_file)
        final_total = total
        current_imported = total_imported
        #progress = 0.0
        total_imported = 0
        #total = 0
        light_end_time = datetime.now() - start_time
        partial_time[0] = f"Lightweight {str(light_end_time)[:-4]}"
    if get_heavyweight:
        import_heavyweights_task(save, color_map,get_models_from_library,map_file)
        if final_total == 0:
            final_total = total
        else:
            final_total += total
        #total = final_total
        current_imported += total_imported
        total_imported = 0
        #progress = 0.0
        heavy_end_time = datetime.now() - start_time
        if light_end_time:
            partial_time[1] = f"Heavyweight {str(heavy_end_time-light_end_time)[:-4]}"
        else:
            partial_time[1] = f"Heavyweight {str(heavy_end_time)[:-4]}"
    
    if get_signs:
        import_signs_task(save,get_models_from_library,map_file)
        if final_total == 0:
            final_total = total
        else:
            final_total += total
        #total = final_total
        current_imported += total_imported
        total_imported = 0
        #progress = 0.0
        sign_end_time = datetime.now() - start_time
        if heavy_end_time and light_end_time:
            partial_time[2] = f"Signs {str(sign_end_time - heavy_end_time)[:-4]}"
        elif heavy_end_time:
            partial_time[2] = f"Signs {str(sign_end_time - heavy_end_time)[:-4]}"
        elif light_end_time:
            partial_time[2] = f"Signs {str(sign_end_time - light_end_time)[:-4]}"
        else:
            partial_time[2] = f"Signs {str(sign_end_time)[:-4]}"
            
    if get_splines:    
        import_splines_task(save, color_map,get_models_from_library,map_file)
        if final_total == 0:
            final_total = total
        else:
            final_total += total
        #total = final_total
        current_imported += total_imported
        total_imported = 0
        #progress = 0.0
        spline_end_time = datetime.now() - start_time
        if heavy_end_time and light_end_time and sign_end_time:
            partial_time[3] = f"Spline {str(spline_end_time - sign_end_time)[:-4]}"
        if heavy_end_time and light_end_time:
            partial_time[3] = f"Spline {str(spline_end_time - heavy_end_time)[:-4]}"
        if heavy_end_time:
            partial_time[3] = f"Spline {str(spline_end_time - heavy_end_time)[:-4]}"
        if light_end_time:
            partial_time[3] = f"Spline {str(spline_end_time - light_end_time)[:-4]}"
        if sign_end_time:
            partial_time[3] = f"Spline {str(spline_end_time - sign_end_time)[:-4]}"
        else:
            partial_time[3] = f"Spline {str(spline_end_time)[:-4]}"


    total = final_total
    if not stop_requested:
        total_imported = final_total
    else:
        total_imported = current_imported
    
    is_scanning = False
    stop_requested = False
    end_time = datetime.now()
    execution_time = end_time - start_time   
    per_time = partial_time
    print(f"SF to Blender time: {execution_time} seconds")
    bpy.app.timers.register(update_ui)

def import_models_reg(
        b_type:int,
        asset: dict,
        buildable_name:str,
        file: Path,
        parent_name:str,
        parent_attach:str,
        support_name:str = "",
        pole_height:float = 0.0):
    global obj_name
    
    if b_type == 0:
        obj_name = import_model(
            asset=asset,
            buildable_name=buildable_name,
            file=file,
            parent_name=parent_name,
            parent_attach=parent_attach,
            support_name=support_name,
            pole_height = pole_height
        )
    else:
        obj_name = import_model(
                asset=asset,
                buildable_name=buildable_name,
                file=file,
                parent_name=parent_name,
                parent_attach=parent_attach
            )
    
def import_empty_reg(
        asset: dict,
        buildable_name:str,
        empty_name:str = ""):
    global prop_parent_name
    
    prop_parent = import_empty(
            asset=asset,
            buildable_name=buildable_name,
            empty_name=empty_name
        )
    prop_parent_name = prop_parent.name if prop_parent else ""
    
def hide_current_col(buildable_name:str):
    current_col = bpy.data.collections.get(buildable_name)
    if current_col:
        current_col.hide_viewport = True

def schedule_remove_object(object_name: str):
    if not object_name:
        return None

    def remove():
        ob = bpy.data.objects.get(object_name)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
        return None

    bpy.app.timers.register(remove, first_interval=0)

def get_buildable_models(sf_asset_export_path):
    global buildable_to_asset_path,build_total,total_buildings_imported
    global is_asset_building,stop_building_requested,obj_name,prop_parent_name
    print("---------------------------------------------------------")
    #sf_asset_export_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_export_path
    
    #mark_as_asset = bpy.context.scene.sf_importer_props.mark_as_asset
    #build_materials = bpy.context.scene.sf_importer_props.build_materials
    
    search_dir = Path(r"FactoryGame\Content\FactoryGame\Buildable")
    base_file_dir = Path(sf_asset_export_path, search_dir)
    event_file_dir = Path(sf_asset_export_path, search_dir.parent,"Events")
    base_tex_dir = base_file_dir
    if Path(sf_asset_export_path,"Exports").exists():
        base_tex_dir = Path(sf_asset_export_path,"Exports", search_dir)
    
    psk_files = list(base_file_dir.rglob("*.psk"))
    pskx_files = list(base_file_dir.rglob("*.pskx"))
    event_psk_files = list(Path(event_file_dir).rglob("*.psk"))
    event_pskx_files = list(Path(event_file_dir).rglob("*.pskx"))
    asset_files = psk_files + pskx_files + event_psk_files + event_pskx_files
    
    is_pskx = "ALL"
    
    
    #bpy.ops.outliner.orphans_purge(do_recursive=True)

    with open(buildable_to_asset_path, 'r', encoding='utf-8') as f:
        build_to_asset = json.load(f)
        
    build_total = len(build_to_asset)
    count = 0
    for build in build_to_asset:
        if stop_building_requested:
            break
        
        buildable = build_to_asset[build]
        buildable_name = buildable['ObjectName']
    
        asset_list = {}
        support_name = ""
        support_mesh = []
        for component in buildable:
            if stop_building_requested:
                break
            
            if component == 'ObjectName':# or asset == 'ProductionIndicator':
                continue
            asset = buildable.get(component)
            if not asset:
                continue
    
            print(component)
            print("===============")
            if type(asset) == list:
                for ast in asset:
                    print("--------------")
                    asset_name = ast.get('Mesh')
                    asset_dir = ""
                    buildable_file = ""
                    if '/' in asset_name:
                        asset_dir =Path(asset_name)
                        asset_name = asset_name.split('/')[-1]
    
                    pole_height = ast.get('Height')
    
                    if asset_dir:
                        for asset_file in asset_files:
                            if os.fspath(asset_dir) in os.fspath(asset_file):
                                if asset_file.name.startswith(asset_name+'.'):
                                    buildable_file = asset_file
                    else:
                        buildable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
    
    
                    if buildable_file:
                        if type(buildable_file) == list:
                            file = buildable_file[0]
                        else:
                            file = buildable_file # type: Path
                    else:
                        print(f"Not Found: {asset_name}")
                        continue
    
                    parent_name = ""
                    parent_attach = ""
                    parent_comp_name = ast.get('Parent')
                    if parent_comp_name:
                        if asset_list.get(parent_comp_name):
                            parent_name = asset_list.get(parent_comp_name,"") 
                        else:
                            parent_name = buildable[parent_comp_name].get('Mesh',"")
                        print(f"parent_name: {parent_name}")
                        parent_attach = ast.get('ParentAttach',"")
                        print(f"parent_attach: {parent_attach}")
                    #ob_name = import_model(asset=ast,
                    #    buildable_name=buildable_name,
                    #    file=file,
                    #    parent_name=parent_name,
                    #    parent_attach=parent_attach,
                    #    support_name=support_name,
                    #    pole_height = pole_height
                    #    )
                    
                    obj_name = None
                    bpy.app.timers.register(functools.partial(
                        import_models_reg,
                        b_type = 0,
                        asset=ast,
                        buildable_name=buildable_name,
                        file=file,
                        parent_name=parent_name,
                        parent_attach=parent_attach,
                        support_name=support_name,
                        pole_height = pole_height
                        ), first_interval=0)
                    time.sleep(0.1)
                    
                    while obj_name is None:
                        if stop_building_requested:
                            break
                        print("waiting for model to finish importing")
                        time.sleep(0.5)
                    
                    asset_list[component] = obj_name
    
                    #if not obj_name:
                    #    asset_list[component] = file.name.split('.')[0]
                    #else:
                    #    asset_list[component] = obj_name #file.name.split('.')[0]
                    #print(asset_list)
    
                if support_name:
                    schedule_remove_object(support_name)
            elif "Props" in component:
                asset_name = asset.get('Mesh')
                empty_name =component.split('_')[0]
                prop_components = asset["Props"]
    
                #prop_parent = import_empty(asset=asset,
                #    buildable_name=buildable_name,
                #    empty_name=empty_name
                #    )
                
                prop_parent_name = None
                bpy.app.timers.register(functools.partial(
                    import_empty_reg,
                    asset=asset,
                    buildable_name=buildable_name,
                    empty_name=empty_name
                    ), first_interval=0)
                time.sleep(0.1)
    
                for prop in prop_components:
                    print("--------------")
                    ast = prop_components[prop]
                    asset_name = ast.get('Mesh')
                    asset_dir = ""
                    buildable_file = ""
                    if '/' in asset_name:
                        asset_dir =Path(asset_name)
                        asset_name = asset_name.split('/')[-1]
    
                    if asset_dir:
                        for asset_file in asset_files:
    
                            if os.fspath(asset_dir) in os.fspath(asset_file):
                                buildable_file = asset_file
                    else:
                        buildable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
    
                    if buildable_file:
                        if type(buildable_file) == list:
                            file = buildable_file[0]
                        else:
                            file = buildable_file
                    else:
                        print(f"Not Found: {asset_name}")
                        continue
    
                    
                    
                    while not prop_parent_name:
                        if stop_building_requested:
                            break
                        print("waiting for model to finish importing")
                        time.sleep(0.5)
    
                    parent_name = prop_parent_name
                    
                    #if not prop_parent:
                    #    parent_name = empty_name
                    #else:
                    #    parent_name = prop_parent.name
                    parent_attach = ""
                    parent_comp_name = ast.get('Parent')
    
                    #ob_name = import_model(asset=ast,
                    #    buildable_name=buildable_name,
                    #    file=file,
                    #    parent_name=parent_name,
                    #    parent_attach=parent_attach
                    #    )
                    
                    obj_name = None
                    bpy.app.timers.register(functools.partial(
                        import_models_reg,
                        b_type = 1,
                        asset=ast,
                        buildable_name=buildable_name,
                        file=file,
                        parent_name=parent_name,
                        parent_attach=parent_attach
                        ), first_interval=0)
                    time.sleep(0.1)
                    
                    while not obj_name:
                        if stop_building_requested:
                            break
                        print("waiting for model to finish importing")
                        time.sleep(0.5)
                    
                    asset_list[prop] = obj_name
    
                    #if not obj_name:
                    #    asset_list[prop] = file.name.split('.')[0]
                    #else:
                    #    asset_list[prop] = obj_name #file.name.split('.')[0]
                    #print(asset_list)
            else:   
                asset_name = asset.get('Mesh')
                asset_dir = ""
                buildable_file = ""
                if '/' in asset_name:
                    asset_dir =Path(asset_name)
    
                    asset_name = asset_name.split('/')[-1] # type: str
    
                if "mSupportMeshInstanceData" in component:
                    support_name = asset_name
                print(f"does {build} have mSupportMeshInstanceData: {support_name}")
    
                if asset_dir:
                    for asset_file in asset_files:
                        if os.fspath(asset_dir) in os.fspath(asset_file):
                            if asset_file.name.startswith(asset_name+'.'):
                                buildable_file = asset_file
                                print(buildable_file)
    
                        if asset_dir.name in asset_file.parent.name:
                            asset_file_l = asset_file.stem.lower()
                            if asset_file_l == asset_name.lower():
                                buildable_file = asset_file
                                print(buildable_file)
                else:
                    buildable_file = [asset_file for asset_file in asset_files if asset_file.name.startswith(asset_name+'.')]
                    print(buildable_file)

                if buildable_file:
                    #if type(buildable_file) == list:
                    #    file = buildable_file[0]
                    #else:
                    #    file = buildable_file
                    if type(buildable_file) == list:
                        if 1 < len(buildable_file):
                            print(f"Multiple files found: {buildable_file}")
                            #multiple_files = builable_filea
                            if "TradingPost" in str(buildable_file[0]):
                                file = buildable_file[1]
                            else:   
                                file = buildable_file[0]
                        else:
                            file = buildable_file[0]
                    else:
                        file = buildable_file # type: Path
                else:
                    print(f"Not Found: {asset_name}")
                    continue

                parent_name = ""
                parent_attach = ""
                parent_comp_name = asset.get('Parent')

                if parent_comp_name:
                    if asset_list.get(parent_comp_name):
                        parent_name = asset_list.get(parent_comp_name,"") 
                    else:
                        print(asset)
                        print(buildable.get(parent_comp_name))
                        #if buildable.get(parent_comp_name):
                        parent_name = buildable[parent_comp_name].get('Mesh',"")
                    print(f"parent_name: {parent_name}")
                    parent_attach = asset.get('ParentAttach',"")
                    print(f"parent_attach: {parent_attach}")

                obj_name = None
                bpy.app.timers.register(functools.partial(
                    import_models_reg,
                    b_type = 2,
                    asset=asset,
                    buildable_name=buildable_name,
                    file=file,
                    parent_name=parent_name,
                    parent_attach=parent_attach
                    ), first_interval=0)
                time.sleep(0.1)
                
                #ob_name = import_model(asset=asset,
                #    buildable_name=buildable_name,
                #    file=file,
                #    parent_name=parent_name,
                #    parent_attach=parent_attach
                #    )
                
                while not obj_name:
                    if stop_building_requested:
                        break
                    print("waiting for model to finish importing")
                    time.sleep(0.5)

                asset_list[component] = obj_name
                #if not obj_name:
                #    asset_list[component] = file.name.split('.')[0]
                #else:
                #    asset_list[component] = obj_name #file.name.split('.')[0]
        total_buildings_imported += 1
        bpy.app.timers.register(functools.partial(
            hide_current_col,
            buildable_name=buildable_name
            ), first_interval=0)
        time.sleep(0.1)
        #current_col = bpy.data.collections.get(buildable_name)
        #if current_col:
        #    current_col.hide_viewport = True
        #print(asset_list)
                
    #a_coll = get_or_create_collection('Assets')
    #u_coll = get_or_create_collection('Utility')
    #if mark_as_asset and not stop_building_requested:
    #    folder = Path(bpy.data.filepath).parent
    #    if not Path(folder,"blender_assets.cats.txt").exists():
    #        print("blender_assets.cats.txt not in perant folder")
    #    target_catalogs = {
    #    "Assets-Factory":"",
    #    "Assets-Building":"",
    #    "Utility":""
    #    }
    #    with (folder / "blender_assets.cats.txt").open() as f:
    #        for line in f.readlines():
    #            if line.startswith(("#", "VERSION", "\n")):
    #                continue
    #            # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
    #            name = line.split(":")[2].split("\n")[0]
    #            for cat in target_catalogs:
    #                if name == cat:
    #                    uuid = line.split(":")[0]
    #                    target_catalogs[name] = uuid
    #    
    #        for col in list(a_coll.children):
    #            catalog_id = target_catalogs.get("Assets-"+col.name)
    #            for b_col in list(col.children):
    #                a_coll.asset_clear()
    #                b_col.asset_mark()
    #                b_col.asset_generate_preview()
    #                asset_data = b_col.asset_data
    #                asset_data.catalog_id = catalog_id
    #    
    #        for col in list(u_coll.children):
    #            catalog_id = target_catalogs.get(u_coll.name)
    #            col.asset_clear()
    #            col.asset_mark()
    #            col.asset_generate_preview()
    #            asset_data = col.asset_data 
    #            asset_data.catalog_id = catalog_id

def run_mark_asset(a_coll,u_coll):
    global marking_asset
    marking_asset = True
    
    folder = Path(bpy.data.filepath).parent
    if Path(folder,"blender_assets.cats.txt").exists():
        target_catalogs = {
        "Assets-Factory":"",
        "Assets-Building":"",
        "Utility":""
        }
        with (folder / "blender_assets.cats.txt").open() as f:
            for line in f.readlines():
                if line.startswith(("#", "VERSION", "\n")):
                    continue
                # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
                name = line.split(":")[2].split("\n")[0]
                for cat in target_catalogs:
                    if name == cat:
                        uuid = line.split(":")[0]
                        target_catalogs[name] = uuid
                        
            for col in list(a_coll.children):
                catalog_id = target_catalogs.get("Assets-"+col.name)
                for b_col in list(col.children):
                    col.hide_viewport = False
                    a_coll.asset_clear()
                    b_col.asset_mark()
                    b_col.asset_generate_preview()
                    col.hide_viewport = True
                    asset_data = b_col.asset_data
                    asset_data.catalog_id = catalog_id
                    
            for col in list(u_coll.children):
                if "Conveyor" in col.name:
                    col.hide_viewport = True
                catalog_id = target_catalogs.get(u_coll.name)
                col.hide_viewport = False
                col.asset_clear()
                col.asset_mark()
                col.asset_generate_preview()
                col.hide_viewport = True
                asset_data = col.asset_data 
                asset_data.catalog_id = catalog_id
    else:
        print("blender_assets.cats.txt not in perant folder")
    marking_asset = False
    
def import_models_task(a_coll,u_coll,sf_asset_export_path,mark_as_asset):
    global build_total,total_buildings_imported,is_asset_building,stop_building_requested,build_execution_time
    start_time = datetime.now()
    build_execution_time = 0.0
    final_total = 0
    build_total = 0
    total_buildings_imported = 0
    
    get_buildable_models(sf_asset_export_path)
    
    if mark_as_asset and not stop_building_requested:
        bpy.app.timers.register(functools.partial(
            run_mark_asset,
            a_coll=a_coll,
            u_coll=u_coll
            ), first_interval=0)
        time.sleep(0.1)
    
    #mark_as_asset = bpy.context.scene.sf_importer_props.mark_as_asset
    #if mark_as_asset and not stop_building_requested:
    #    folder = Path(bpy.data.filepath).parent
    #    if Path(folder,"blender_assets.cats.txt").exists():
    #        target_catalogs = {
    #        "Assets-Factory":"",
    #        "Assets-Building":"",
    #        "Utility":""
    #        }
    #        with (folder / "blender_assets.cats.txt").open() as f:
    #            for line in f.readlines():
    #                if line.startswith(("#", "VERSION", "\n")):
    #                    continue
    #                # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
    #                name = line.split(":")[2].split("\n")[0]
    #                for cat in target_catalogs:
    #                    if name == cat:
    #                        uuid = line.split(":")[0]
    #                        target_catalogs[name] = uuid
    #    
    #            for col in list(a_coll.children):
    #                catalog_id = target_catalogs.get("Assets-"+col.name)
    #                for b_col in list(col.children):
    #                    col.hide_viewport = False
    #                    a_coll.asset_clear()
    #                    b_col.asset_mark()
    #                    b_col.asset_generate_preview()
    #                    col.hide_viewport = True
    #                    asset_data = b_col.asset_data
    #                    asset_data.catalog_id = catalog_id
    #    
    #            for col in list(u_coll.children):
    #                if "Conveyor" in col.name:
    #                    col.hide_viewport = True
    #                catalog_id = target_catalogs.get(u_coll.name)
    #                col.hide_viewport = False
    #                col.asset_clear()
    #                col.asset_mark()
    #                col.asset_generate_preview()
    #                col.hide_viewport = True
    #                asset_data = col.asset_data 
    #                asset_data.catalog_id = catalog_id
    #    else:
    #        print("blender_assets.cats.txt not in perant folder")
    
    is_asset_building = False
    stop_building_requested = False
    end_time = datetime.now()
    build_execution_time = end_time - start_time
    print(f"SF to Blender time: {execution_time} seconds")
    bpy.app.timers.register(update_ui)

def get_total_instances_task(save: s.SaveGame):
    global total_all_instances,is_get_scanning,stop_get_requested
    lbs = get_lbs(save)
    instances_by_class_ref = lbs.mBuildableClassToInstanceArray
    
    l_total = 0
    for buildable in list(instances_by_class_ref.Keys):
        if stop_get_requested:
            break
        class_path = buildable.PathName
        if not class_path:
            raise Exception("Missing class path, how can this happen?")
        instances = instances_by_class_ref[buildable]
        if not instances: 
            continue  
        l_total += 1
        total_all_instances += len(instances)#= l_total
    print(f"l_total: {l_total} (instances: {total_all_instances})")
    
    all_classes = set() # all buildable classes in the save
    factory_classes = [] # all factory buildable instances
    exclude_factory = [ # exclude from default importing method 
        #"Build_RailroadTrack",
        #"Build_RailroadTrackIntegrated_C_Points",
        #"Build_PowerLine_C",
        #"Build_ConveyorBelt",
        #"Build_Pipeline_",
        #"Build_PipelineMK2",
        #"Build_PipeHyper_C",
        #"Build_ConveyorLift",
        "Build_PipelineFlowIndicator_C"
    ]   
    spline_buildables = [
        "Build_PipelineMK2_",
        "Build_Pipeline_",
        "Build_RailroadTrack",
        "Build_PipeHyper_C",
    ]
    
    save_objects = save.allSaveObjects()
    
    for obj in save_objects:
        if stop_get_requested:
            break
        if not obj.isActor():
            continue    
    
        header = obj.Header
        className =  header.ObjectHeader.ClassName  
        
        if className.startswith('/Game/FactoryGame/Buildable/') and '.Build_' in className and className.endswith('_C') or '.BP_ElevatorCabin_C' in className:
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
        
        if className.startswith('/Game/FactoryGame/Prototype/') and '.Build_' in className and className.endswith('_C'):
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
    
    tot_chains = 0
    for obj in save.mPersistentAndRuntimeData.SaveObjects:
        if stop_get_requested:
            break
        if not obj.isActor():
            continue
        header = obj.Header
        className =  header.ObjectHeader.ClassName
        
        if className.startswith( '/Script/FactoryGame.FGConveyorChainActor'):
            tot_chains += 1
    
    h_total = 0
    s_total = 0
    s_total_set = set()
    for factory in all_classes:
        if stop_get_requested:
            break
        
        # group buildable instances by buildable class 
        ex = any(exc in factory for exc in exclude_factory)
        if ex:
            continue
        for factory_class in factory_classes:
            header = factory_class.Header
            cls_name = header.ObjectHeader.Reference.PathName
            if any(spline in cls_name for spline in spline_buildables):
                s_total += 1
                s_total_set.add(cls_name)
                #print(cls_name,s_total,len(factory_classes))
                #print(len(s_total_set))
                #print("spline",cls_name)
                #continue
            
            if factory in cls_name:
                h_total += 1
                total_all_instances += 1
                #print("not spline",cls_name)
    print(f"h_total: {h_total}, s_total: {s_total}, splines: {len(s_total_set)}")
    print(s_total)
    
    #if not stop_get_requested:
    #    total_all_instances = h_total# l_total + h_total
    is_get_scanning = False
    stop_get_requested = False
    bpy.app.timers.register(update_ui)

class GetTotIntButton(bpy.types.Operator):
    bl_idname = "button.total_instances"
    bl_label = "Get Total Instances"

    def execute(self, context):
        global total_all_instances,is_scanning,is_get_scanning,is_asset_building,stop_get_requested
        save_path = bpy.context.scene.sf_importer_props.save_path
        
        if not is_get_scanning and not is_scanning and not is_asset_building:
            save = s.SaveGame(Path(save_path))
        
            is_get_scanning = True
            self.report({'INFO'}, "Calculating total instances...")
            t1_thread = threading.Thread(target=get_total_instances_task,args=(save,))
            t1_thread.start()
            
            bpy.app.timers.register(update_ui)
            GetTotIntButton.bl_label = "Stop Calculations"
        else:
            self.report({'INFO'}, "Stopping Calculations...")
            stop_get_requested = True
            GetTotIntButton.bl_label = "Get Total Instances"
        
        return {'FINISHED'}

def get_lib_assets_task(save: s.SaveGame):
    global buildable_to_asset_path
    with open(buildable_to_asset_path, 'r', encoding='utf-8') as f:
        map = json.load(f)
    
    get_models_from_library = bpy.context.scene.sf_importer_props.get_models_from_library
    get_lightweight = bpy.context.scene.sf_importer_props.get_lightweight
    get_heavyweight = bpy.context.scene.sf_importer_props.get_heavyweight
    get_signs = bpy.context.scene.sf_importer_props.get_signs
    get_splines = bpy.context.scene.sf_importer_props.get_splines
    
    if get_lightweight:
        lbs = get_lbs(save)
        instances_by_class_ref = lbs.mBuildableClassToInstanceArray
        for buildable in list(instances_by_class_ref.Keys):
            if stop_get_requested:
                break
            class_path = buildable.PathName
            if not class_path:
                raise Exception("Missing class path, how can this happen?")
            instances = instances_by_class_ref[buildable]
            if not instances: 
                continue  
            
            cls = class_path.split(".")[-1]
            name = map.get(cls)
            mesh = name.get("ObjectName")
            get_lib_result = get_lib_assets(data_type="Collection",asset_name=mesh,asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            
            if get_lib_result:
                print(get_lib_result)
            
    all_classes = set() # all buildable classes in the save
    factory_classes = [] # all factory buildable instances
    exclude_factory = [ # exclude from default importing method 
        "Build_RailroadTrack",
        "Build_RailroadTrackIntegrated_C_Points",
        "Build_PowerLine_C",
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
        "Build_PipeHyper_",
        "Build_RailroadTrack",
    ]
    
    save_objects = save.allSaveObjects()
    
    for obj in save_objects:
        if stop_get_requested:
            break
        if not obj.isActor():
            continue    
    
        header = obj.Header
        className =  header.ObjectHeader.ClassName  
    
        if className.startswith('/Game/FactoryGame/Buildable/') and '.Build_' in className and className.endswith('_C') or '.BP_ElevatorCabin_C' in className:
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
    
        if className.startswith('/Game/FactoryGame/Prototype/') and '.Build_' in className and className.endswith('_C'):
            all_classes.add(className.split('.')[-1])
            factory_classes.append(obj)
    
    for factory in all_classes:
        if factory in exclude_factory:
            continue
        get_heavy = False
        is_spline = any(spline in factory for spline in spline_buildables)
        if get_heavyweight:
            if "Build_StandaloneWidgetSign_" not in factory or not is_spline:
                get_heavy = True
                
        if get_signs:
            if "Build_StandaloneWidgetSign_" in factory:
                get_heavy = True
                
        if get_splines:
            if is_spline:
                get_heavy = True
        
        if not get_heavy:
            continue
            
        name = map.get(factory)
        print(f"Getting {factory} mapping")
        if "Build_PipelinePumpMk2" in factory:
            name = map.get("Build_PipelinePumpMK2_C")
        if not name:
            print("skipping: ",factory)
            continue
        mesh = name.get("ObjectName")
        get_lib_result = get_lib_assets(data_type="Collection",asset_name=mesh,asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend",col_type=True)
        
        if get_lib_result:
            print(get_lib_result)
        
class ImportSaveButton(bpy.types.Operator):
    bl_idname = "button.import_save"
    bl_label = "Start Save Import"

    def execute(self, context):
        global is_scanning,is_get_scanning,is_asset_building, stop_requested,is_appended,mapped_build
        global execution_time,start_process,buildable_to_asset_path
        
        is_appended = 0
        mapped_build = set()
        
        sf_asset_lib_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_lib_path
        sf_asset_export_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_export_path
        if not bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path:
            buildable_to_asset_path = os.path.join(os.path.dirname(__file__), "buildable_to_asset.json")
        else:
            buildable_to_asset_path = os.path.join(bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path, "buildable_to_asset.json")
        
        if not sf_asset_lib_path:
            self.report({'ERROR'}, "Please set the asset library path in the addon preferences.")
            return {'CANCELLED'}
        if not sf_asset_export_path:
            self.report({'ERROR'}, "Please set the asset export path in the addon preferences.")
            return {'CANCELLED'}
        if not buildable_to_asset_path:
            self.report({'ERROR'}, "Please set the buildable to asset path in the addon preferences.")
            return {'CANCELLED'}
        
        save_path = bpy.context.scene.sf_importer_props.save_path
        
        get_lightweight = bpy.context.scene.sf_importer_props.get_lightweight
        get_heavyweight = bpy.context.scene.sf_importer_props.get_heavyweight
        get_signs = bpy.context.scene.sf_importer_props.get_signs
        get_splines = bpy.context.scene.sf_importer_props.get_splines
        
        get_models_from_library = bpy.context.scene.sf_importer_props.get_models_from_library
        
        if not is_scanning and not is_get_scanning and not is_asset_building:
        #if not stop_requested:
            # https://github.com/moritz-h/satisfactory-3d-map/blob/master/docs/SATISFACTORY_SAVE.md
            start_process = datetime.now()
            save = s.SaveGame(Path(save_path))
            saveHeader = save.mSaveHeader
            #start_time = time.perf_counter()
            # print the session info to 'clear' the console    
            print(
                f"\n\n\n\n---\n{saveHeader.SessionName} {saveHeader.SaveDateTime.toString()}\n---\n"
            )
            
            get_or_create_collection('Import')
            # clear the import collection before adding to it
            if get_lightweight:
                for obj in list(get_or_create_collection('Lightweights','Import').objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for col in list(get_or_create_collection('Lightweights','Import').children):
                    bpy.data.collections.remove(col, do_unlink=True)
            if get_heavyweight:
                for obj in list(get_or_create_collection('Heavyweights','Import').objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for col in list(get_or_create_collection('Heavyweights','Import').children):
                    if col == bpy.data.collections.get("Signs") or col == bpy.data.collections.get("Splines"):
                        continue
                    bpy.data.collections.remove(col, do_unlink=True)
            if get_signs:
                get_or_create_collection('Heavyweights','Import')
                for obj in list(get_or_create_collection('Signs','Heavyweights').objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for col in list(get_or_create_collection('Signs','Heavyweights').children):
                    bpy.data.collections.remove(col, do_unlink=True)
            if get_splines:
                get_or_create_collection('Heavyweights','Import')
                for obj in list(get_or_create_collection('Splines','Heavyweights').objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for col in list(get_or_create_collection('Splines','Heavyweights').children):
                    bpy.data.collections.remove(col, do_unlink=True)
                
            #for obj in list(get_or_create_collection('Import').objects):
            #    bpy.data.objects.remove(obj, do_unlink=True)
            #for col in list(get_or_create_collection('Import').children):
            #    bpy.data.collections.remove(col, do_unlink=True)
            # clear out all the orphans
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            
            cls = save.allSaveObjects()
            
            color_map = import_color_slots(cls)
            print(color_map)
            #if get_lightweight or get_heavyweight:
            #    get_lib_result = get_lib_assets(data_type="NodeTree",asset_name="Buildables from Points",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            #    
            #    if get_lib_result:
            #        self.report({'INFO'}, get_lib_result)
            #if get_signs:
            #    get_lib_result = get_lib_assets(data_type="NodeTree",asset_name="Buildables from Points(signs)",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            #    
            #    if get_lib_result:
            #        self.report({'INFO'}, get_lib_result)
            #if get_splines:
            #    get_lib_result = get_lib_assets(data_type="NodeTree",asset_name="Buildables From Spline",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            #    
            #    if get_lib_result:
            #        self.report({'INFO'}, get_lib_result)
            #    
            #    get_lib_result = get_lib_assets(data_type="NodeTree",asset_name="Conveyer Cains From Spline",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            #
            #    if get_lib_result:
            #        self.report({'INFO'}, get_lib_result)
                
            get_lib_result = get_lib_assets(data_type="NodeTree",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend",set_fake=True)

            if get_lib_result:
                self.report({'INFO'}, get_lib_result)
            
            #if get_signs:
            #    get_lib_result = get_lib_assets(data_type="Material",asset_name="MI_SignBackground",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")
            #    if get_lib_result:
            #        print(get_lib_result)
                    
            if get_models_from_library:
                #if bpy.data.collections.get(mesh):
                    
                get_lib_result = get_lib_assets(data_type="Collection",asset_name="Utility",asset_lib_name="SF Asset Lib",asset_lib_blend = "SF_Asset_Lib.blend")

                if get_lib_result:
                    print(get_lib_result)
            
            #if get_models_from_library:
            #    self.report({'INFO'}, "Getting Models from asset library...")
            #    get_lib_assets_task(save)
            
            is_scanning = True
            self.report({'INFO'}, "Starting scan...")
            t1_thread = threading.Thread(target=import_save_task,args=(save,color_map,get_models_from_library))
            t1_thread.start()
            
            bpy.app.timers.register(update_ui)
            ImportSaveButton.bl_label = "Stop Scan"
        else:
            self.report({'INFO'}, "Stopping scan...")
            stop_requested = True
            ImportSaveButton.bl_label = "Start Scan"
        
        return {'FINISHED'}
class BuildAssetsButton(bpy.types.Operator):
    bl_idname = "button.build_assets"
    bl_label = "Build Asset Library"

    def execute(self, context):
        global is_scanning,is_get_scanning,is_asset_building,stop_building_requested,buildable_to_asset_path
        
        sf_asset_lib_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_lib_path
        sf_asset_export_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_export_path
        if not bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path:
            buildable_to_asset_path = os.path.join(os.path.dirname(__file__), "buildable_to_asset.json")
        else:
            buildable_to_asset_path = os.path.join(bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path, "buildable_to_asset.json")
        
        if not sf_asset_lib_path:
            self.report({'ERROR'}, "Please set the asset library path in the addon preferences.")
            return {'CANCELLED'}
        if not sf_asset_export_path:
            self.report({'ERROR'}, "Please set the asset export path in the addon preferences.")
            return {'CANCELLED'}
        if not buildable_to_asset_path:
            self.report({'ERROR'}, "Please set the buildable to asset path in the addon preferences.")
            return {'CANCELLED'}
        
        mark_as_asset = bpy.context.scene.sf_importer_props.mark_as_asset
        build_materials = bpy.context.scene.sf_importer_props.build_materials
        
        if not is_scanning and not is_get_scanning and not is_asset_building:
            clear_asset_col = True
            
            a_coll = get_or_create_collection('Assets')
            u_coll = get_or_create_collection('Utility')
            if clear_asset_col:
                for obj in list(a_coll.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for col in list(a_coll.children):
                    for b_col in list(col.children):
                        b_col.asset_clear()
                    bpy.data.collections.remove(col, do_unlink=True)
            
                for obj in list(u_coll.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for col in list(u_coll.children):
                    bpy.data.collections.remove(col, do_unlink=True)
            
            else:
                get_asset_collection()
            
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            
            is_asset_building = True
            
            build_materials = bpy.context.scene.sf_importer_props.build_materials
            
            if build_materials:
                get_par_materials(sf_asset_export_path)
            
            self.report({'INFO'}, "Starting asset building...")
            mark_as_asset = bpy.context.scene.sf_importer_props.mark_as_asset
            t1_thread = threading.Thread(
                target=import_models_task,
                args=(a_coll, u_coll, sf_asset_export_path, mark_as_asset)
            )
            t1_thread.start()
            
            bpy.app.timers.register(update_ui)
            BuildAssetsButton.bl_label = "Stop Building"
        else:
            self.report({'INFO'}, "Stopping asset building...")
            stop_building_requested = True
            BuildAssetsButton.bl_label = "Start Building"
        
        return {'FINISHED'}

class VIEW3D_PT_SF_Importer_panel(Panel):
    bl_idname = "SF_PT_IMPORTER"
    bl_label = "Import SF Save"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SF Importer'
    
    def draw(self, context):
        global progress,progress_in,per_time, is_scanning,total,total_imported,execution_time, current_buildable,start_process,total_all_instances,is_get_scanning
        layout = self.layout
        scene = context.scene
        props = scene.sf_importer_props

        save_col = layout.column()
        save_col.prop(props, "save_path", text="Save Path")
        
        save_path = props.save_path
        is_save_valid = save_path and Path(save_path).exists() and save_path.endswith(".sav")
        if not save_path:
            save_col.label(text="Please select a save file to import.", icon='INFO')
        if not Path(save_path).exists():
            save_col.label(text="Save file does not exist.", icon='INFO')
        if not save_path.endswith(".sav"):
            save_col.label(text="Save file must be a .sav file.", icon='INFO')
            
        save_button = layout.column()
        save_button.scale_y = 1.5
        save_button.operator("button.import_save", text="Stop Scan" if is_scanning else "Start Scan")
        if is_get_scanning or is_asset_building or is_save_valid == False:
            save_button.active = False
        else:
            save_button.active = True
    
        get_i_button = layout.column(align=True)
        get_i_button.operator("button.total_instances", text="Stop Calculating" if is_get_scanning else "Get Total Instances")
        if is_scanning or is_asset_building or is_save_valid == False:
            get_i_button.active = False
        else:
            get_i_button.active = True
        if total_all_instances:
            get_i_box = get_i_button.box()
            get_i_box.label(text=f"Total Instances: {total_all_instances}")
    
        # TODO: button to swap all to proxy mesh
    
        pro_col = layout.column()
        pro_col.prop(props, "get_models_from_library")
        pro_col.prop(props, "use_proxy")
        pro_col.prop(props, "hide_buildable", text="Hide Buildable")
    
        choose_box = layout.box()
        choose_col = choose_box.column()
        choose_row = choose_col.row()
        choose_row.prop(props, "get_lightweight")
        choose_row = choose_col.row()
        choose_row.prop(props, "get_heavyweight")
        choose_row = choose_col.row()
        choose_row.prop(props, "get_signs")
        choose_row = choose_col.row()
        choose_row.prop(props, "get_splines")
    
        save_box = layout.box()
        row = save_box.row(align=True)
        row_box_l = row.box()
        row_box_r = row.box()
        row_box_l.label(text=f"{total_imported}/{total}")
        row_box_r.scale_x = 6.0
    
        value = remap(progress, 0, 100, 0, 1)
        value_in = remap(progress_in, 0, 100, 0, 1)
        bar_box_r = row_box_r.column(align=True)
        bar_box_r.progress(factor=value, text=f"{progress:.1f}%")
        if current_buildable:
            row_box_l.scale_y = 2.5
            bar_sub = bar_box_r.row(align=True)
            bar_sub.scale_y = 0.5
            bar_sub.progress(factor=value_in, text=f"{progress_in:.1f}%")
            bar_box_r.label(text=f"{current_buildable or "stuff"}")
        save_box.label(text=f"Start Time: {str(start_process)[:-4]}")
        save_box.label(text=f"Execution Time: {str(execution_time)[:-4]}")
        if per_time:
            for per in per_time:
                if per:
                    save_box.label(text=per)
        
class VIEW3D_PT_SF_Asset_Builder_panel(Panel):
    bl_idname = "SF_PT_ASSET_BUILDER"
    bl_label = "Build SF Asset Library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SF Importer'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        global progress,progress_in,per_time, is_scanning,build_total,total_buildings_imported,build_execution_time
        global current_buildable,start_process,is_get_scanning,marking_asset
        layout = self.layout
        scene = context.scene
        props = scene.sf_importer_props
        
        # check if currrent blend file is asset library file, if not, show a warning message
        if not "SF_Asset_Lib.blend" in Path(bpy.data.filepath).name:
            layout.label(text="Current blend file is not 'SF_Asset_Lib.blend'", icon='INFO')
            layout.label(text="Open 'SF_Asset_Lib.blend' to continue building asset library", icon='INFO')

        build_button = layout.column()
        build_button.scale_y = 1.5
        build_button.operator("button.build_assets", text="Stop Building" if is_asset_building else "Start Building")
        if is_get_scanning or is_scanning:
            build_button.active = False
        else:
            build_button.active = True
        
        # TODO: show time elapsed after finishing importing models
        
        if build_total:
            row = layout.row(align=True)
            row.label(text=f"Total Assets: {total_buildings_imported}/{build_total}")
        if build_execution_time:
            row = layout.row(align=True)
            row.label(text=f"Execution Time: {str(build_execution_time)[:-4]}")
        
        if marking_asset:
            row = layout.row(align=True)
            row.label(text="Marking Assets...")
        
        config_box = layout.box()
        config_box.prop(props, "mark_as_asset")
        config_box.prop(props, "build_materials")
        
classes = (
    SF_Importer_Properties,
    VIEW3D_PT_SF_Importer_panel,
    VIEW3D_PT_SF_Asset_Builder_panel,
    ImportSaveButton,
    GetTotIntButton,
    BuildAssetsButton,
    SFImportPreferences,
    GenerateBuildableToAsset,
    CopyBlendToAssetLib
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.sf_importer_props = bpy.props.PointerProperty(type=SF_Importer_Properties)
    bpy.types.Scene.scan_progress = bpy.props.FloatProperty(name="Save Import Progress", min=0, max=100, default=0.0, get=lambda self: progress)
    bpy.types.Scene.scan_progress = bpy.props.FloatProperty(name="Instance Progress", min=0, max=100, default=0.0, get=lambda self: progress_in)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    if hasattr(bpy.types.Scene, "sf_importer_props"):
        del bpy.types.Scene.sf_importer_props
    del bpy.types.Scene.scan_progress