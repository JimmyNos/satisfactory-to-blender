import json
import os
from pathlib import Path
import time

# path to build files
#BUILD_FILES_DIR = r"PATH-TO-FMODEL-EXPORTS\FactoryGame\Content\FactoryGame\Buildable"
#BEAM_BUILD_FILES_DIR = r"PATH-TO-FMODEL-EXPORTS\FactoryGame\Content\FactoryGame\Prototype\Buildable\Beams"

# Output file location (in the script directory)
#OUTPUT_FILE = Path(__file__).parent / "buildable_to_asset.json"
#OUTPUT_FAILED_FILE = Path(__file__).parent / "failed_to_asset.json"

EXCLUDE_LIST = [
    "Cheat",
    "Build_VehiclePath",
    "Build_HubTerminal_C",
    "Build_AutomatedWorkBench",
    "BUILD_SingleDoor_Base_01",
    "Build_RailroadTrackIntegrated",
    "Concave",
    #"Integrate",
    #"Build_TradingPost",
    #"Build_Blueprint",
    #"Build_Pipeline_NoIndicator",
    #"Build_BlueprintDesigner",
]

INTEGRATED_BUILD_LIST = [
    "ProductionIndicatorInstanced",
    "HubTerminal",
    "Integrate",
    "ElevatorCabin",
    "StorageBlueprint",
    "PipelineFlowIndicator"
]

EXCLUDE_MESH_LIST = [
    #"SM_BlenderLiquid_01",
    "_proxy",
    "FactoryLegsProxy",
    "FogPlane",
    "_SKProxy_01",
    "FactoryLeg",
    "Plane",
    "SM_TradingPostMeshBF_01",
    "SM_Hub_Stg_01"
]

MESH_TYPES = [
    "StaticMesh",
    "SkeletalMesh",
    "mMesh",
    "mWireMesh",
    "mMeshMesh",
    "mBottomMesh",
    "mMidMesh",
    "mHalfMidMesh",
    "mTopMesh",
    "mBellowMesh",
    "mShelfMesh",
    "mPoleVariations",
    "mHeightSegment1m",
    "mHeightSegment4m",
    "mCapMesh",
    "mLadderSegmentMesh",
    "mButtonMesh"
]

MESH_NODE_TYPES = [
    "StaticMeshComponent",
    "SkeletalMeshComponent",
    "BP_ProductionIndicatorInstanced_C",
    "FGVertexAnimatedMeshComponent",
    "FGColoredInstanceMeshProxy",
    "AbstractInstanceDataObject",
    "FGBuildableElevatorSparseData",
    "FGBuildableConveyorLiftSparseData",
    "Build_ConveyorBelt",
    "Build_Pipeline",
    "Build_FoundationPassthrough",
    "Build_PipeHyper",
    "Build_RailroadTrack",
    "Build_Ladder_C",
    "Build_TradingPost_C",
    "BP_ElevatorCabin_C"
]

CONVEYOR_LIFT_MESHES = [
    "mBottomMesh",
    "mMidMesh",
    "mHalfMidMesh",
    "mTopMesh",
    "mBellowMesh",
    "mShelfMesh",
]

ELEVATOR_MESHES = [
    "mTopMesh",
    "mBottomMesh",
]

SUPPORT_MESHES = [
    "Build_ConveyorPole_",
    "Build_PipelineSupport",
    "Build_SignPole",
    "Build_PipeHyperSupport",
]

TRADING_POST_MESHES = [
    #"mSkeletalMeshSoftPtr",
    "mStages",
    "mGenerator1Location",
    "mGenerator2Location",
    "mStorageLocation",
    "mHubTerminalLocation",
    "mWorkBenchLocation",
    "mCalendarLocation",
]

def extract_build_data(json_file_path,PI_mesh):
    """Extract ObjectName and Translation data from a build JSON file."""
    #try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(json_file_path.name)
    print(f" len(data): {len(data)}")
    
    entries = {}
    #entries = []
    meshes = []
    entry_name = os.path.basename(json_file_path).split(".")[0]+"_C"
    mesh = {}
    #mesh['ObjectName'] = entry_name.split('_')[1]
    mesh['ObjectName'] = "_".join(entry_name.split('_')[1:-1])
    mesh_duplicate = {}
    mesh_temp = {}
    
    models = {}
    root_nodes = []
    definitive_models = []
    parent_nodes = {}
    
    for item in data:
        # create list of root models with children
        child_nodes = {}
        if item.get("Type") == "SimpleConstructionScript":
            root_props = item["Properties"]
            print("checking if file has root nodes")    
            csc_root_nodes = root_props.get('RootNodes')
            if not csc_root_nodes:
                print(f"file has no root nodes")
                continue
            print(f"file has {len(csc_root_nodes)} root nodes")
                
            csc_root_nodes_name = ""
            csc_root_nodes_path = ""

            for i in range(len(csc_root_nodes)):
                csc_root_nodes_name = csc_root_nodes[i]['ObjectName'].split('.')[1][:-1]
                csc_root_nodes_path = int(csc_root_nodes[i]['ObjectPath'].split('.')[1])
                print(f"processing root node {csc_root_nodes_name}: idx: {csc_root_nodes_path}")
                
                root_node = data[csc_root_nodes_path]
                root_node_name = item.get("Name")
                root_node_props = root_node["Properties"]
                root_node_component_m_type  = root_node_props['ComponentTemplate']['ObjectName'].split("'")[0]
                root_node_component_name  = root_node_props['ComponentTemplate']['ObjectName'].split(":")[1][:-1]
                root_node_child_nodes  = root_node_props.get('ChildNodes')
                if not any(m_type in root_node_component_m_type for m_type in MESH_NODE_TYPES) and not "Props" in root_node_props['ComponentTemplate']['ObjectName']:
                    print(f"{root_node_name} is not a mesh node")
                    continue
                
                if not root_node_child_nodes:
                    print(f"{root_node_name} has no children")
                    continue
                
                # populating parent_nodes and child_nodes lists
                for i in range(len(root_node_child_nodes)):
                    child_node_name = root_node_child_nodes[i].get("ObjectName").split('.')[1][:-1]
                    child_node_path = int(root_node_child_nodes[i].get("ObjectPath").split('.')[1])
                    child_node = data[int(child_node_path)]
                    child_node_comp = child_node.get("Properties").get("ComponentTemplate")
                    child_atn_name = child_node.get("Properties").get("AttachToName")
                    child_comp_name = child_node_comp.get("ObjectName").split(":")[1][:-1]
                    child_nodes.update({child_comp_name:child_atn_name})
                
                parent_nodes[root_node_component_name] = child_nodes
                
                models[root_node_component_name] = {
                    "Mesh": "Empty",
                    "RelativeLocation": None,
                    "RelativeRotation": None,
                    "RelativeScale3D": None,
                    "Props" : None
                    
                    }
                child_nodes = {}
                
                # check if children nodes are parents
                for i in range(len(root_node_child_nodes)):
                    child_node_path = root_node_child_nodes[i].get("ObjectPath").split('.')[1]
                    child_node = data[int(child_node_path)]
                    
                    child_node_name = child_node['Properties']['ComponentTemplate'].get("ObjectName").split(':')[1][:-1]
                    child_child_nodes = child_node['Properties'].get("ChildNodes")
                    
                    if child_child_nodes:
                        for i in range(len(child_child_nodes)):
                            child_child_node_name = child_child_nodes[i].get("ObjectName").split('.')[1][:-1]
                            child_child_node_path = int(child_child_nodes[i].get("ObjectPath").split('.')[1])
                            child_child_node = data[int(child_child_node_path)]
                            child_child_node_comp = child_child_node.get("Properties").get("ComponentTemplate")
                            child_child_atn_name = child_child_node.get("Properties").get("AttachToName")
                            child_child_comp_name = child_child_node_comp.get("ObjectName").split(":")[1][:-1]
                            child_nodes.update({child_child_comp_name:child_child_atn_name})

                        parent_nodes[child_node_name] = child_nodes
                        models[child_node_name] = {
                            "Mesh": "Empty",
                            "RelativeLocation": None,
                            "RelativeRotation": None,
                            "RelativeScale3D": None,
                            "Props" : None
                            }
                        child_nodes = {}
                        
                        
            #print(f"parent nodes: {parent_nodes.keys()}")
            #print(f"parent and children: {parent_nodes}")    
            #print(f"models: {models}")    
            

    print("Getting models in the files")
    for i in range(len(data)):
        # create list of models in build file
        node_type =  data[i].get("Type")
        node_name =  data[i].get("Name")
        node_props = data[i].get("Properties")
        if not node_props:
            continue
        
        if "FloorMesh" in node_name:# or "PoleMeshProxy" in node_name:
            continue
        
        #if "Props" in node_name:
        #    if node_props:
        #        model_translation = node_props.get("RelativeLocation")
        #        model_rotation = node_props.get("RelativeRotation")
        #        model_scale = node_props.get("RelativeScale3D")
        #        models_list = {
        #            #"Mesh": "Empty",
        #            "RelativeLocation": model_translation,
        #            "RelativeRotation": model_rotation,
        #            "RelativeScale3D": model_scale
        #        }
        #    
        #    #models.update({node_name:models_list})
        
        if "Build_TradingPost_C" in node_type:
            if node_props:
                models_list,stage_list = get_TradingPostComponents(node_props,data)
                
            models.update({"TP_Stage":stage_list})
            models.update({node_name:models_list})
        
        elif "Props" in node_name:
            if node_props:
                model_translation = node_props.get("RelativeLocation")
                model_rotation = node_props.get("RelativeRotation")
                model_scale = node_props.get("RelativeScale3D")
                models_list = {
                    "Mesh": "Empty",
                    "RelativeLocation": model_translation,
                    "RelativeRotation": model_rotation,
                    "RelativeScale3D": model_scale
                }
            
            models.update({node_name:models_list})        
        elif "AbstractInstanceDataObject" in node_type:
            if "PowerPole" in entry_name:
                continue
            
            node_props = data[i].get("Properties").get("Instances")
            if node_props:
                models_list = get_AbstractInstanceComponent(node_props)

            models.update({node_name:models_list})
        elif any(st in node_type for st in SUPPORT_MESHES):
            node_props = data[i].get("Properties")
            node_poles = node_props.get("mPoleVariations")
            node_support_mesh = node_props.get("mSupportMeshInstanceData")
            if node_poles:
                node_name = "mPoleVariations"
                models_list,support_model = get_PoleComponents(node_poles,node_support_mesh)
            else:
                continue
            if support_model:
                models.update(support_model)
            models.update({node_name:models_list})
        elif "BP_ProductionIndicatorInstanced_C" in node_type:
            if node_props:
                model = get_ProIndicatorComponents(node_props,PI_mesh)
            
            models.update({node_name:model})  
        elif any(st in node_type for st in MESH_NODE_TYPES):
            if node_props:
                models_list = get_Components(node_props,node_name,parent_nodes)
            
            
            
            if models_list:
                if len(models_list) == 1:
                    if models_list[0].get("Parent"):
                        if "Props" in models_list[0].get("Parent"):
                            if models[models_list[0].get("Parent")].get("Props"):
                                models[models_list[0].get("Parent")].get("Props").update({node_name:models_list[0]})
                            else:
                                models[models_list[0].get("Parent")]["Props"] = {node_name:models_list[0]}
                            if mesh.get(node_name):
                                mesh.pop(node_name)
                                models.pop(node_name)
                        else:
                            models.update({node_name:models_list[0]})
                    else:
                        models.update({node_name:models_list[0]})
                else:
                    models.update({node_name:models_list})
        else:
            continue
        
        print(f"{len(models)} models found")
        if not models:
            continue
        
        if models:
            mesh.update(models)
            
    if "WidgetSign" in entry_name:
        if "FGColoredInstanceMeshProxy_GEN_VARIABLE" in mesh and "SignMeshProxy" in mesh:
            object_name = mesh['ObjectName']
            sign = mesh["SignMeshProxy"]
            pole_holder = mesh["FGColoredInstanceMeshProxy_GEN_VARIABLE"]
            update_pole_holder = {
                "Parent": "SignMeshProxy",
                "Mesh":pole_holder["Mesh"],
                "RelativeLocation":pole_holder["RelativeLocation"],
                "RelativeRotation":pole_holder["RelativeRotation"],
                "RelativeScale3D":pole_holder["RelativeScale3D"]
            }
            mesh = {
                "ObjectName": object_name,
                "SignMeshProxy":sign,
                "FGColoredInstanceMeshProxy_GEN_VARIABLE":update_pole_holder
            }
    
    if "Build_DroneStation_C" in entry_name:
        if "FGColoredInstanceMeshProxy_GEN_VARIABLE" in mesh and "BP_ProductionIndicatorInstanced_GEN_VARIABLE" in mesh:
            object_name = mesh['ObjectName']
            station = mesh["FGColoredInstanceMeshProxy_GEN_VARIABLE"]    
            indicator = mesh["BP_ProductionIndicatorInstanced_GEN_VARIABLE"]    
            update_indicator = {
                "Parent": "FGColoredInstanceMeshProxy_GEN_VARIABLE",
                "Mesh":indicator["Mesh"],
                "RelativeLocation":indicator["RelativeLocation"],
                "RelativeRotation":indicator["RelativeRotation"],
                "RelativeScale3D":indicator["RelativeScale3D"]
            }
            mesh["BP_ProductionIndicatorInstanced_GEN_VARIABLE"] = update_indicator
            
        
    #print(mesh)
    remove_mesh = []
    for m in mesh:
        if not mesh[m]:
            remove_mesh.append(m)
            
    for re in remove_mesh:
        mesh.pop(re)
    try:
        entries[entry_name] = mesh
    except:
        print(f"⚠️Error adding entry for {entry_name} in {json_file_path}")
    
    if 1 == len(mesh):
        return None 
    
    
    
    return entries

def get_TradingPostComponents(
    node_props: dict,
    data
):
    m_type = []
    model_mesh = ""
    model_translation = None
    model_rotation = None
    model_scale = None
    models_list = []
    stage_list = []
    models_p_list = []
    
    for prop in node_props:
        for tp_mesh_type in TRADING_POST_MESHES:
            if prop == tp_mesh_type:
                m_type.append(prop)
                #break
                
    if not m_type:
        return None
    
    for m in m_type:
        if "mStages" in m:
            stages = node_props["mStages"]
            for stg in range(len(stages)):
                model_mesh = stages[stg].get("AssetPathName")[6:].split(".")[0]
                model_translation = node_props.get("RelativeLocation")
                model_rotation = node_props.get("RelativeRotation")
                model_scale = node_props.get("RelativeScale3D")

                stage_list.append({
                    "Mesh": model_mesh,
                    "RelativeLocation": model_translation,
                    "RelativeRotation": model_rotation,
                    "RelativeScale3D": model_scale
                })
            if len(stage_list) == 7:
                if stage_list[4] == stage_list [5]:
                    stage_list.pop(5)
                ...
        else:
            mesh_idx = int(node_props.get(m)["ObjectPath"].split('.')[1])
            model_mesh = node_props.get(m)["ObjectName"].split(':')[1][:-1]
            mesh_data = data[mesh_idx].get("Properties")
            model_translation = mesh_data.get("RelativeLocation")
            model_rotation = mesh_data.get("RelativeRotation")
            model_scale = mesh_data.get("RelativeScale3D")
            
            models_list.append({
                "Mesh": model_mesh,
                "RelativeLocation": model_translation,
                "RelativeRotation": model_rotation,
                "RelativeScale3D": model_scale
            })
                
    return models_list, stage_list
    
def get_ProIndicatorComponents(
    node_props: dict,PI_mesh):
    model_mesh = PI_mesh
    model_translation = None
    model_rotation = None
    model_scale = None
    model = {}
    
    model_translation = node_props.get("RelativeLocation")
    model_rotation = node_props.get("RelativeRotation")
    model_scale = node_props.get("RelativeScale3D")
    
    if node_props.get("StaticMesh"):
        model_mesh = node_props["StaticMesh"]["ObjectPath"][6:].split(".")[0]
        
    model.update({
        "Mesh": model_mesh,
        "RelativeLocation": model_translation,
        "RelativeRotation": model_rotation,
        "RelativeScale3D": model_scale
    })
    
    return model

def get_Components(
    node_props: dict,
    node_name: str,
    parent_nodes:dict,):
    m_type = []
    model_mesh = ""
    model_translation = None
    model_rotation = None
    model_scale = None
    models_list = []
    models_p_list = []
    
    for prop in node_props:
        for mesh_type in MESH_TYPES:
            if prop == mesh_type:
                m_type.append(prop)
                #break
    if not m_type:
        return None
        
    for m in m_type:
        model_mesh = node_props[m]["ObjectPath"][6:].split(".")[0]
        model_translation = node_props.get("RelativeLocation")
        model_rotation = node_props.get("RelativeRotation")
        model_scale = node_props.get("RelativeScale3D")
        if m == "mCapMesh":
            model_translation = node_props.get("mEndCapTranslation")
            model_rotation = node_props.get("mEndCapRotation")
        if m == "mMidMesh" and "mCapMesh" in m_type:
            model_rotation = node_props.get("mMidMeshRotation")
            if model_rotation:
                model_rotation['Pitch'] = model_rotation['Pitch']*-1
                if model_rotation['Pitch'] == -180:
                    model_rotation['Pitch'] = 0
            
    
        if any(ex in model_mesh for ex in EXCLUDE_MESH_LIST):
            print(f"excluding {model_mesh}")
            return None
    
        if not parent_nodes:
            #models[node_name].update({"12":2})
            models_list.append({
                "Mesh": model_mesh,
                "RelativeLocation": model_translation,
                "RelativeRotation": model_rotation,
                "RelativeScale3D": model_scale
            })
        else:
            models_list.append({
                "Mesh": model_mesh,
                "RelativeLocation": model_translation,
                "RelativeRotation": model_rotation,
                "RelativeScale3D": model_scale
            })
            for parent in parent_nodes:
                if any(node_name in child for child in parent_nodes[parent]):
                    models_p_list.append({
                        "Parent": parent,
                        "ParentAttach":parent_nodes[parent][node_name],
                        "Mesh": model_mesh,
                        "RelativeLocation": model_translation,
                        "RelativeRotation": model_rotation,
                        "RelativeScale3D": model_scale
                    })
    if models_p_list:
        models_list = models_p_list
    return models_list

def get_AbstractInstanceComponent(
    node_props: dict):
    m_type = ""
    node_idx = 0
    model_mesh = ""
    model_translation = None
    model_rotation = None
    model_scale = None
    models_list = []
    
    for j in range(len(node_props)):
        for prop in node_props[j]:
            for mesh_type in MESH_TYPES:
                if prop == mesh_type:
                    m_type = prop
                    #break
        if m_type:
            node_idx = j
            model_mesh = node_props[j].get(m_type)["ObjectPath"][6:].split(".")[0]
            model_translation = node_props[j].get("RelativeTransform").get("Translation")
            model_rotation = node_props[j].get("RelativeTransform").get("Rotation")
            model_scale = node_props[j].get("RelativeTransform").get("Scale3D")
        else:
            continue
        
        if any(ex in model_mesh for ex in EXCLUDE_MESH_LIST):
            print(f"excluding {model_mesh}")
            continue
        models_list.append(
            {
                "Mesh": model_mesh,
                "RelativeLocation": model_translation,
                "RelativeRotation": model_rotation,
                "RelativeScale3D": model_scale
            }
        )
        
    #models.update({node_name:models_list})
    return models_list

def get_PoleComponents(
    node_poles: dict,
    node_support_mesh: dict):
    m_type = ""
    node_idx = 0
    model_mesh = ""
    model_translation = None
    model_rotation = None
    model_scale = None
    models_list = []
    support_model = {}
    pole_height = 0.0
    
    if node_support_mesh:
        model_mesh = node_support_mesh["StaticMesh"]["ObjectPath"][6:].split(".")[0]
        RelativeTransform = node_support_mesh.get("RelativeTransform")
        if RelativeTransform:
            model_translation = RelativeTransform.get("Translation")
            model_rotation = RelativeTransform.get("Rotation")
            model_scale = RelativeTransform.get("Scale3D")
        
        support_model["mSupportMeshInstanceData"] = {
                "Mesh": model_mesh,
                "RelativeLocation": model_translation,
                "RelativeRotation": model_rotation,
                "RelativeScale3D": model_scale
            }
                
    for j in range(len(node_poles)):
        model_translation = None
        model_rotation = None
        model_scale = None
        for prop in node_poles[j]:
            for mesh_type in MESH_TYPES:
                if prop == mesh_type:
                    m_type = prop
                    #break
        if m_type:
            model_mesh = node_poles[j].get(m_type)["ObjectName"].split("'")[1]
            pole_height = node_poles[j].get("Height")
            #model_translation = node_poles[j].get("RelativeTransform").get("Translation")
            #model_rotation = node_poles[j].get("RelativeTransform").get("Rotation")
            #model_scale = node_poles[j].get("RelativeTransform").get("Scale3D")
        else:
            continue
        
        if any(ex in model_mesh for ex in EXCLUDE_MESH_LIST):
            print(f"excluding {model_mesh}")
            continue
        models_list.append(
            {
                "Mesh": model_mesh,
                "Height": pole_height,
                "RelativeLocation": model_translation,
                "RelativeRotation": model_rotation,
                "RelativeScale3D": model_scale
            }
        )
        
    #models.update({node_name:models_list})
    return models_list,support_model

    
def populate_buildable_to_asset(SF_export_dir, custom_output_path=None):
    """Scan all build_*.json files and populate buildable_to_asset.json."""
    
    if custom_output_path:
        OUTPUT_FILE = Path(custom_output_path, "buildable_to_asset.json")
    else:
        OUTPUT_FILE = Path(__file__).parent / "buildable_to_asset.json"
    
    build_files_dir = Path(SF_export_dir, "FactoryGame", "Content", "FactoryGame", "Buildable")
    beam_build_files_dir = Path(SF_export_dir, "FactoryGame", "Content", "FactoryGame", "Prototype", "Buildable", "Beams")
    
    start_time = time.perf_counter()
    all_data = {}
    PI_build = "BP_ProductionIndicatorInstanced"
    build_dir = Path(build_files_dir)
    beam_build_dir = Path(beam_build_files_dir)
    
    if not build_dir.exists():# or not build_beam_dir.exists():
        print(f"Error: Directory does not exist: {build_dir}")# or {build_beam_dir}")
        return
    
    # Find all build_*.json files recursively
    integrated_builds = []
    for i in INTEGRATED_BUILD_LIST:
        if list(build_dir.rglob(f"BP_*{i}.json")):
            integrated_builds.extend(build_dir.rglob(f"BP_*{i}.json"))
        else:
            integrated_builds.extend(build_dir.rglob(f"build_*{i}*.json"))
    build_files = integrated_builds + list(build_dir.rglob("build_*.json"))
    build_files = build_files + list(beam_build_dir.rglob("build_*.json"))
    #build_files(list(build_dir.rglob("BP_ProductionIndicatorInstanced.json"))[0])
    print(f"Found {len(build_files)} build files")
    count = 0
    ex_count = 0
    ex_list = []
    failed_list = {}
    PI_mesh = ""
    for build_file in build_files:
        print(f"Processing: {build_file.name}")
        try:
            if any(ex in build_file.name for ex in EXCLUDE_LIST):
                print(f"excluded {build_file.name}")
                ex_list.append(build_file.name)
                ex_count+=1
                continue
                
            data = extract_build_data(build_file,PI_mesh)
            
            if data.get(f"{PI_build}_C") and build_file.stem == PI_build:
                PI_mesh = data.get(f"{PI_build}_C")[f"Default__{PI_build}_C"]["Mesh"]
            
            if data:
                count+=1
                
                if data.get("Build_Pipeline_C"):
                    data["Build_Pipeline_NoIndicator"] = data.get("Build_Pipeline_C")
                    count+=1
                elif data.get("Build_PipelineMK2_C"):
                    data["Build_PipelineMK2_NoIndicator"] = data.get("Build_PipelineMK2_C")
                    count+=1
                if data.get("Build_PowerTowerPlatform_C"):
                    if all_data.get("Build_PowerTower_C"):
                        Build_PowerTower_C = all_data["Build_PowerTower_C"]
                        if Build_PowerTower_C.get("PoleMeshProxy"):
                            tower_data = all_data["Build_PowerTower_C"]["PoleMeshProxy"]
                            data["Build_PowerTowerPlatform_C"].update({
                                "PoleMeshProxy":tower_data
                                })
                if data.get("Build_MinerMk3_C"):
                    if all_data.get("Build_MinerMk2_C"):
                        Build_MinerMk2_C = all_data["Build_MinerMk2_C"]
                        if Build_MinerMk2_C.get("MainMesh_GEN_VARIABLE"):
                            minermk2_data = all_data["Build_MinerMk2_C"]["MainMesh_GEN_VARIABLE"]
                            data["Build_MinerMk3_C"].update({
                                "MainMesh_GEN_VARIABLE":minermk2_data
                                })
                all_data.update(data)
            else:
                print(f"No models processed for {build_file.name}")
                failed_list.update({build_file.name: None})
        except Exception as e:
            print(f"⚠️ Failed to process {build_file.name}: {e}")
            failed_list.update({build_file.name: str(e)})
    
    #print(f"Found {len(build_files)} build files")
    #print(f"processed {count} buildables")
    #print(f"excluded {ex_count,ex_list} build files")
    #print(f"failed {len(failed_list)} build files")
    
    # Write to output file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    
    #with open(OUTPUT_FAILED_FILE, 'w', encoding='utf-8') as f:
    #    json.dump(failed_list, f, indent=2)
    
    print(f"\nPopulated {len(all_data)} entries in {OUTPUT_FILE}")
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Importing models time: {execution_time:.6f} seconds")
    
    return len(all_data) # return the number of entries populated

