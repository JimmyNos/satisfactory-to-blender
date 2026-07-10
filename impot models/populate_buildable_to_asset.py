import json
import os
from pathlib import Path

# path to build files
BUILD_FILES_DIR = r"PATH-TO-FMODEL-EXPORTS\Content\FactoryGame\Buildable"

# Output file location (in the script directory)
OUTPUT_FILE = Path(__file__).parent / "buildable_to_asset.json"
#OUTPUT_FAILED_FILE = Path(__file__).parent / "failed_to_asset.json"

EXCLUDE_LIST = [
    "Cheat",
    "Build_VehiclePath",
    "Build_TradingPost", # NOTE: excluded for now
    "Integrate",
    "Build_HubTerminal_C",
    "Build_AutomatedWorkBench",
    #"Build_Blueprint",
    #"Build_Pipeline_NoIndicator",
    #"Build_BlueprintDesigner",
]

EXCLUDE_MESH_LIST = [
    "SM_BlenderLiquid_01",
    "_proxy",
    "FactoryLegsProxy",
    "FogPlane",
    "_SKProxy_01",
    "FactoryLeg",
    "Plane",
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
    "mLadderSegmentMesh"
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
    "Build_Ladder_C"
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


def extract_build_data(json_file_path):
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
                
                if not any(m_type in root_node_component_m_type for m_type in MESH_NODE_TYPES):
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
                models[root_node_component_name] = None
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
                        models[child_node_name] = None
                        child_nodes = {}
                        
                        
            print(f"parent nodes: {parent_nodes.keys()}")
            print(f"parent and children: {parent_nodes}")    
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
        
        
        if "AbstractInstanceDataObject" in node_type:
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
                model = get_ProIndicatorComponents(node_props)
            
            models.update({node_name:model})  
        elif any(st in node_type for st in MESH_NODE_TYPES):
            if node_props:
                models_list = get_Components(node_props,node_name,parent_nodes)
            
            if models_list:
                if len(models_list) == 1:
                    models.update({node_name:models_list[0]})
                else:
                    models.update({node_name:models_list})
        else:
            continue
        
        # TODO: get rot and pos for FoundationPassthrough buildables
        # TODO: get correct models for TradingPost buildable for each phase
        
        print(f"{len(models)} models found")
        if not models:
            continue
        
        if models:
            mesh.update(models)
                
                
        
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

def get_ProIndicatorComponents(
    node_props: dict):
    model_mesh = "SM_ProductionLight_01"
    model_translation = None
    model_rotation = None
    model_scale = None
    model = {}
    
    model_translation = node_props.get("RelativeLocation")
    model_rotation = node_props.get("RelativeRotation")
    model_scale = node_props.get("RelativeScale3D")
        
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
        model_mesh = node_props[m]["ObjectName"].split("'")[1]
        model_translation = node_props.get("RelativeLocation")
        model_rotation = node_props.get("RelativeRotation")
        model_scale = node_props.get("RelativeScale3D")
    
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
                print(parent_nodes[parent])
                if any(node_name in child for child in parent_nodes[parent]):
                    print(parent_nodes[parent][node_name])
                    print(f"{node_name} is a child of {parent}")
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
            model_mesh = node_props[j].get(m_type)["ObjectName"].split("'")[1]
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
        model_mesh = node_support_mesh["StaticMesh"]["ObjectName"].split("'")[1]
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

    
def main():
    """Scan all build_*.json files and populate buildable_to_asset.json."""
    all_data = {}
    
    build_dir = Path(BUILD_FILES_DIR)
    
    if not build_dir.exists():# or not build_beam_dir.exists():
        print(f"Error: Directory does not exist: {build_dir}")# or {build_beam_dir}")
        return
    
    # Find all build_*.json files recursively
    build_files = list(build_dir.rglob("build_*.json"))
    print(f"Found {len(build_files)} build files")
    count = 0
    ex_count = 0
    ex_list = []
    failed_list = {}
    for build_file in build_files:
        print(f"Processing: {build_file.name}")
        try:
            print(build_file.name)
            if any(ex in build_file.name for ex in EXCLUDE_LIST):
                print(f"excluded {build_file.name}")
                ex_list.append(build_file.name)
                ex_count+=1
                continue
                
            data = extract_build_data(build_file)
            if data:
                count+=1
                
                if data.get("Build_Pipeline_C"):
                    data["Build_Pipeline_NoIndicator"] = data.get("Build_Pipeline_C")
                    count+=1
                elif data.get("Build_PipelineMK2_C"):
                    data["Build_PipelineMK2_NoIndicator"] = data.get("Build_PipelineMK2_C")
                    count+=1
                all_data.update(data)
            else:
                print(f"No models processed for {build_file.name}")
                failed_list.update({build_file.name: None})
        except Exception as e:
            print(f"⚠️ Failed to process {build_file.name}: {e}")
            failed_list.update({build_file.name: str(e)})
    
    print(f"Found {len(build_files)} build files")
    print(f"processed {count} buildables")
    print(f"excluded {ex_count,ex_list} build files")
    print(f"failed {len(failed_list)} build files")
    
    # Write to output file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    
    #with open(OUTPUT_FAILED_FILE, 'w', encoding='utf-8') as f:
    #    json.dump(failed_list, f, indent=2)
    
    print(f"\nPopulated {len(all_data)} entries in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
