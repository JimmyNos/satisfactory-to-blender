import bpy # type: ignore
from bpy.types import Operator, AddonPreferences,PropertyGroup,Panel # type: ignore
from bpy.props import StringProperty, IntProperty, BoolProperty # type: ignore

import threading
import time
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
x_corr = -500.0
y_corr = 2800.0
distance = 1000.0

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

class SFImportPreferences(AddonPreferences):
    bl_idname = __package__
    
    sf_asset_lib_path: StringProperty( #type: ignore
        name="SF asset Library path",
        description="Path to the Satisfactory asset library folder. this is where the addon will copy the asset library files to. e.g. C:/Users/username/Documents/Blender/SF Asset Library. Note: if there is already an 'SF Asset Library' and 'blender_assets.cats.txt' file in the dir, it will be overwritten.",
        subtype = "DIR_PATH",
        options = {"LIBRARY_EDITABLE"},
        default = "",
        maxlen = 1024
    )
    
    sf_asset_export_path: StringProperty( #type: ignore
        name="SF asset export path",
        description="Path to the folder where Fmodel exported Satisfactory assets.",
        subtype = "DIR_PATH",
        options = {"LIBRARY_EDITABLE"},
        default = "",
        maxlen = 1024
    )
    
    custom_buildable_to_asset_path: StringProperty( #type: ignore
        name="Buildable to Asset path",
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
        elif Path(self.sf_asset_lib_path,"SF_Asset_lib.blend").exists():
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
        global total_entries
        prefs = context.preferences.addons[__package__].preferences
        sf_asset_export_path = Path(prefs.sf_asset_export_path)
        
        buildable_to_asset_path = ""
        
        if not prefs.custom_buildable_to_asset_path:
            total_entries = populate_buildable_to_asset(sf_asset_export_path)
            buildable_to_asset_path = Path(__file__).parent / "buildable_to_asset.json"
        elif prefs.custom_buildable_to_asset_path:
            custom_buildable_to_asset_path = Path(prefs.custom_buildable_to_asset_path)
            if not custom_buildable_to_asset_path.exists():
                self.report({'ERROR'}, f"Custom buildable_to_asset.json path does not exist: {custom_buildable_to_asset_path}")
                return {'CANCELLED'}
            total_entries = populate_buildable_to_asset(sf_asset_export_path, custom_buildable_to_asset_path)
            buildable_to_asset_path = Path(prefs.custom_buildable_to_asset_path, "buildable_to_asset.json")

        self.report({'INFO'}, f"buildable_to_asset.json file generated at: {buildable_to_asset_path}")
        return {'FINISHED'}
    
def copy_blend_to_asset_lib(asset_lib_path: Path):
    # Copy the SF_Asset_lib.blend and blender_assets.cats.txt files to the asset library path
    source_blend = Path(__file__).parent / "SF asset lib" / "SF_Asset_lib.blend"
    source_cats = Path(__file__).parent / "SF asset lib" / "blender_assets.cats.txt"
    
    dest_blend = asset_lib_path / "SF_Asset_lib.blend"
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
    
class ImportSaveButton(bpy.types.Operator):
    bl_idname = "button.import_save"
    bl_label = "Start Save Import"

    def execute(self, context):
        global is_scanning,is_get_scanning,is_asset_building, stop_requested,execution_time,start_process
        
        sf_asset_lib_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_lib_path
        sf_asset_export_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_export_path
        if not bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path:
            buildable_to_asset_path = Path(__file__).parent / "buildable_to_asset.json"
        else:
            buildable_to_asset_path = bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path
        
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
        
            is_scanning = True
            self.report({'INFO'}, "Starting scan...")
            #t1_thread = threading.Thread(target=import_task,args=(save,color_map))
            #t1_thread.start()
            
            #bpy.app.timers.register(update_ui)
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
        global is_scanning,is_get_scanning,is_asset_building,stop_building_requested
        
        sf_asset_lib_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_lib_path
        sf_asset_export_path = bpy.context.preferences.addons[__package__].preferences.sf_asset_export_path
        if not bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path:
            buildable_to_asset_path = Path(__file__).parent / "buildable_to_asset.json"
        else:
            buildable_to_asset_path = bpy.context.preferences.addons[__package__].preferences.custom_buildable_to_asset_path
        
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
        
        if not is_scanning and not is_get_scanning:
            is_asset_building = True
            self.report({'INFO'}, "Starting asset building...")
        else:
            self.report({'INFO'}, "Stopping asset building...")
            stop_building_requested = True
            is_asset_building = False
        
        return {'FINISHED'}

class VIEW3D_PT_SF_Importer_panel(Panel):
    bl_idname = "SF_IMPORTER"
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
    bl_idname = "SF_ASSET_BUILDER"
    bl_label = "Build SF Asset Library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SF Importer'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        global progress,progress_in,per_time, is_scanning,total,total_imported,execution_time, current_buildable,start_process,is_get_scanning
        layout = self.layout
        scene = context.scene
        props = scene.sf_importer_props
        
        # check if currrent blend file is asset library file, if not, show a warning message
        if not Path(bpy.data.filepath).name == "SF_Asset_lib.blend":
            layout.label(text="Current blend file is not SF_Asset_lib.blend", icon='INFO')
            layout.label(text="Please open SF_Asset_lib.blend to continue building asset library", icon='INFO')

        build_button = layout.column()
        build_button.scale_y = 1.5
        build_button.operator("button.build_assets", text="Stop Building" if is_asset_building else "Start Building")
        if is_get_scanning or is_scanning:
            build_button.active = False
        else:
            build_button.active = True
        
        # TODO: show after finishing importing models
        row = layout.row(align=True)
        row.label(text=f"Total Assets: total_imported/total")
        
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