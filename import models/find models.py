import json
import os
from pathlib import Path


def main():
    print("---------------------------------------------------------")
    #bpy.ops.psk.import_file(psk=file,should_import_mesh=True, should_import_armature=True)

    FILE_EXTENTIONS = [
        "png",
        "tga"
    ]

    psk_files = list(Path(BASE_FILE_DIR).rglob("*.psk"))
    pskx_files = list(Path(BASE_FILE_DIR).rglob("*.pskx"))
    event_psk_files = list(Path(EVENT_FILE_DIR).rglob("*.psk"))
    event_pskx_files = list(Path(EVENT_FILE_DIR).rglob("*.pskx"))
    asset_files = psk_files + pskx_files + event_psk_files + event_pskx_files

    is_pskx = "ALL"
    clear_asset_col = True

    with open(BUILD_TO_ASSET_DIR, 'r', encoding='utf-8') as f:
        build_to_asset = json.load(f)
    count = 0
    for build in build_to_asset:
        buildable = build_to_asset[build]
        buildable_name = buildable['ObjectName']
        
        count += 1
        if count > 5:
            #break
            ...
        asset_list = {}
        support_name = ""
        support_mesh = []
        for component in buildable:
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
                            file = buildable_file
                    else:
                        print(f"Not Found: {asset_name}")
                        continue
            else:   
                
                asset_name = asset.get('Mesh')
                asset_dir = ""
                buildable_file = ""
                if '/' in asset_name:
                    asset_dir =Path(asset_name)
                    
                    asset_name = asset_name.split('/')[-1]
                    
                if "mSupportMeshInstanceData" in component:
                    support_name = asset_name
                print(f"does {build} have mSupportMeshInstanceData: {support_name}")
                    
                if asset_dir:
                    
                    for asset_file in asset_files:
                        print(asset_file.name)
                        if asset_dir.name in asset_file.parent.name:
                            print("st")
                        #if "TruckStation_static" in asset_file.name:
                        #    if "Truckstation_static" in asset_dir.name:
                        #        if asset_dir.name in asset_file.parent.name:
                        #            print(asset_file)
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
                        file = buildable_file
                else:
                    print(f"Not Found: {asset_name}")
                    continue

EXPORT_FILE_DIR = r"PATH-TO-FMODEL-EXPORTS"
BASE_FILE_DIR = r"F:\blenber\SF to blend\fmodel export\FactoryGame\Content\FactoryGame\Buildable"
EVENT_FILE_DIR = r"F:\blenber\SF to blend\fmodel export\FactoryGame\Content\FactoryGame\Events"
BUILD_TO_ASSET_DIR = r"F:\blenber\SF to blend\SF-2-Blender addon\satisfactory-to-blender\import models\buildable_to_asset.json"   

INTEGRATED_BUILD_LIST = [
    "ProductionIndicatorInstanced",
    "HubTerminal",
    "Integrate",
    "ElevatorCabin",
    "StorageBlueprint",
    "PipelineFlowIndicator"
]

if __name__ == "__main__":
    main()