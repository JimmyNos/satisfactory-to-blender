import json
from pathlib import Path
from typing import Any, List, Tuple
import bpy
import time

def find_translation_points(data: Any, path: str = "",u_type: int = 0) -> List[Tuple[str, float, float]]:
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
            results.extend(find_translation_points(item, new_path,u_type))
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
    
    for i in data:
        if "LandscapeComponent" in i["Type"]:
            u_type = 2
            #print("type: Landscape")
            break
    #print()
    return find_translation_points(data,u_type=u_type)


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
    import_files = []
    delete_files = []
    map_col = bpy.data.collections.get("map")
    if not map_col:
        map_col = bpy.data.collections.new("map")
        bpy.context.scene.collection.children.link(map_col)
        
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
            
            search_file = list(Path(search_path,file_path.stem).rglob("Persistent_Level.usda"))
            #print(f"found File: {search_file[0]}")
            import_files.append(search_file[0])
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
    for ro_col in  map_col.children:
        bpy.data.collections.remove(ro_col)
    
    imported_count = 0
    for file_path in import_files:
        #break
        print("================================")
        umap_name = file_path.parent.name
        
        
        umap_col = bpy.data.collections.get(umap_name)
        if map_col.children.get(umap_name):
            print(f"Removing existing collection: {umap_name}")
            bpy.data.collections.remove(umap_col)
            umap_col = bpy.data.collections.new(umap_name)
            map_col.children.link(umap_col)
        if not umap_col:
            umap_col = bpy.data.collections.new(umap_name)
            map_col.children.link(umap_col)
        
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[map_col.name].children[umap_col.name]
        
        bpy.ops.wm.usd_import(
            filepath=str(file_path),
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
        umap_col.hide_viewport = True
        imported_count += 1
        print(f" Imported {imported_count}/{no_matches} files")
        print("================================")
        
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
