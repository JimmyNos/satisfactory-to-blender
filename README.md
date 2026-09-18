# satisfactory-to-blender

A **Blender extension** that imports **save data and models** from Coffee Stain Studios' game [Satisfactory](https://www.satisfactorygame.com/).

The extension reconstructs your Satisfactory factories inside Blender using [satisfactory-3d-map](https://github.com/moritz-h/satisfactory-3d-map) for save parsing. Models and materials are imported from assets extracted using FModel.

---

## Features

### Save Data Import

- Rebuilds factories from Satisfactory save data in Blender.
- Displays import progress for each buildable.
- Displays execution time for each buildable type.
- Object culling based on distance from an object, such as a camera.
- Random object scaling to help reduce clipping.

### Model Import

- Reads build JSON files to determine which models are used by each buildable.
- Imports models from FModel-extracted assets.
- Builds and applies materials.
- Creates an asset library containing the imported models.

### Factory Reconstruction

- Buildables are imported as points with attributes used by Geometry Nodes.
- Geometry Nodes handles model instancing and buildable logic.
- Proxy meshes.
- Bounding-box imports.
- Hiding buildables after import.
- Importing different buildable types individually.

---

## Requirements
- **Blender 5.2 or higher**
- **Unreal PSK/PSA (.psk/.psa) Blender extension**

The [Unreal PSK/PSA](https://extensions.blender.org/add-ons/io-scene-psk-psa/) extension is required to import the models extracted from Satisfactory

---

## Installation

1. Download the latest version of the extension as `.zip` file
2. In Blender, go to **Edit → Preferences → Get Extensions**.
3. Select **Install from Disk**.
5. Select the downloaded `.zip` file.
6. After installation, the **SF Importer** panel will appear in Blender's side panel.

---

## Initial Setup

Before importing Satisfactory models or save data, the extension needs to be configured.

1. Open **Edit → Preferences**.
2. Navigate to **Add-ons**.
3. Search for **Satisfactory Importer**.
4. In the add-on preferences, set the paths:
   - Directory containing your FModel-extracted assets.
   - Custom directory to generate the `buildable_to_asset.json` file.
   - Directory specifing where to copy `SF_Asset_lib.blend` file to.

<img alt="preferences" src="resources/images/ui/prefrences.png" width="500" />

### Generate `buildable_to_asset.json`

The extension uses `buildable_to_asset.json` to determine which models belong to each Satisfactory buildable.

In the add-on preferences:

1. Set your FModel asset path.
2. Click **Generate `buildable_to_asset.json`**.

The extension searches the extracted files for `build.json` files and uses them to determine which models are used by each buildable. If no `build.json` files can be found, `buildable_to_asset.json` will be empty.

You can also specify a custom directory if you want to manually edit the file and choose which buildables the extension should import.

You can add additional models or buildables as long as they follow the same data structure described in the [Custom Buildables](#custom-buildables) section.

## Building the Asset Library

The extension provides an asset library containing the Shader Groups and Geometry Node groups required for save importing.

In the add-on preferences:

**Copy asset library file to asset library path**

This copies `SF_Asset_lib.blend` from the extension files to your selected asset-library location.

> **Important:** Do **not** use your main Blender asset library.

> The extension will overwrite `blender_assets.cats.txt`, which would remove categories created in your main asset library.

Use a separate directory for the Satisfactory asset library.

---

## FModel Setup

Before models can be imported, you need to extract the required files from Satisfactory using FModel:
* **Build files** (`.json`)
  * For example:
    * `Build_Blender.json`
    * `BP_ProductionIndicatorInstanced.json`
* **Models**
  * `.psk`
  * `.pskx`
* **Textures**
  * `.png`
* **Materials**
  * `.json`

You can export both build files and material files for most buildables by right-clicking the `buildable` folder in FModel and selecting:

**Export Folder → Properties (.json)**

> Not all buildables and models are located in the `buildable` folder. For example, Beam build files are stored under `/FactoryGame/Prototype/Buildable/Beams`.

![FModel export options](resources/images/FModel/fmodel%202.png)

---

## How to use

### Importing Models

To build the asset library from your FModel-extracted models:

1. Open the copied `SF_Asset_lib.blend` file.
2. Open the **SF Importer** side panel.
3. Select **Start Building**.
4. The extension will import the models one at a time.

After importing each buildable, its collection is hidden to reduce Blender's memory usage and prevent the viewport from becoming unresponsive. Selecting **Start Building** again, everything in the assets collection will be deleted before the models are imported again.

- Make sure **Mark as Asset** is enabled so Blender can create the asset library.
  - After importing all buildables, the extension attempts to generate previews in Blender's Asset Browser, but fails if there are a lot of buildables, you may need to generate some previews manually.

  Generating previews requires the buildable collections to be temporarily unhidden. The extension unhides them, generates the previews, and hides them again after approximately 20 seconds.

> **Note:** Importing the models can take a significant amount of time depending on how many assets are being imported.

I recommended that you review the imported models and materials because some assets may not import correctly.

---

## Importing a Satisfactory Save

Once the asset library and models are configured, you can import your Satisfactory save.

1. Open the **SF IMPORTER** panel from Blender's side panel.
2. Select your `.sav` file in the **Save File** field.
3. Make sure the selected file has a `.sav` extension.
4. Select **Start Scan**.

The extension will parse the save data and begin rebuilding the factory inside Blender.

![SF Importer side panel](resources/images/ui/side%20pannel.png)

## Save Import Options

### Use Library Models

Enable **Use Library Models** to use models from the Satisfactory asset library. The extension appends models from `SF_Asset_Lib.blend` before importing the save. Using the asset library increases import time, so enable this option only when you need to import models.

> Blender may temporarily become unresponsive while a model is being appended. You can open Blender's system console to check whether models are still being appended.

### Proxy Mesh

Enable **Proxy Mesh** to generate a proxy mesh for each buildable.

### Hide Buildable

Enable **Hide Buildable** to hide the buildable model after it has been imported.

### Bounding Box

You can limit the imported area using a bounding box. The boundaries are calculated using the **X and Y coordinates** and a specified distance.

The extension uses Blender coordinates, while Satisfactory save data uses Satisfactory coordinates. To convert Satisfactory coordinates:
- Divide **X** by `100`.
- Divide **Y** by `100`.
- Flip the Y axis.

For example:

```
Satisfactory:
X = -50,000
Y = -200,000

Blender:
X = -500
Y = 2,000
```

## Choosing Buildable Types

You can import the following buildable types individually or import all of them at once. **Signs and spline buildables are generally the most expensive to import.**

For buildables with a lot of instances, I recommended:

1. Use object culling using the Geometry Nodes group.
2. Hide or delete points or splines that will never be visible in the final render.
3. Import only the area required for your scene.

---

## How the Imported Factory Works

Buildables are imported as points with attributes attached to them. These attributes contain the information required to reconstruct the buildable using Geometry Nodes. The Geometry Nodes implementation is still being developed, so some buildables may not look exactly like they do in the original Satisfactory save. If models are not available, the extension uses a default mesh with the primary colour applied.

Buildable points can be:

* Deleted in **Edit Mode**.
* Separated into another object.
* Modified before being processed by Geometry Nodes.
* Used as the basis for additional custom logic.

### Geometry Nodes

The Geometry Nodes setup provides additional controls for:

* Instance position adjustments.
* Object culling.
* Model instancing.
* Buildable-specific logic.

```
To reimport updated Geometry Node groups:

1. Remove the 'Fake User' tag from the existing node group.
2. Reimport the Geometry Node groups.

The extension will not reimport a node group if a node group with the same name already exists in the current blend file and has a 'Fake User' tag.
```
### Sign Text

Sign text is generated through the Geometry Nodes modifier but can be expensive, additional culling options are available to improve performance.

The resolution of the text mask depends on the number of faces available on the screen, There are two subdivision controls:

- Base Subdivision, subdivides the entire sign face.
- Text Mask Subdivision, subdivides only the area containing the text mask.

---

## Recommended Workflow for Large Saves

recommended workflow is:

1. Import a small section of the save first without models to create a lightweight preview.
    - Only select lightweight buildables
2. Enable **Hide Buildable**.
3. Import buildable types separately.
4. Hide or delete splines/points that will not appear in the final render.
5. Use culling to further reduce unnecessary geometry.

---

## Custom Buildables

You can manually add buildables or models to `buildable_to_asset.json`.

The basic structure is:

```json
"Build_Name_C": {
    "ObjectName": "ObjectName",
    "Internal_Object_name": {
        "Mesh": "Path-To-Mesh/",
        "RelativeLocation": null,
        "RelativeRotation": null,
        "RelativeScale3D": null
    },
    "Internal_Object_name2": {
        "Parent": "Parent_ObjectName",
        "ParentAttach": null,
        "Mesh": "Path-To-Mesh/",
        "RelativeLocation": null,
        "RelativeRotation": null,
        "RelativeScale3D": null
    }
}
```

### Example

```json
"BP_ProductionIndicatorInstanced_C": {
    "ObjectName": "ProductionIndicatorInstanced",
    "Default__BP_ProductionIndicatorInstanced_C": {
        "Mesh": "FactoryGame/Buildable/Factory/-Shared/ProductionIndicator/Mesh/SM_ProductionLight_01",
        "RelativeLocation": null,
        "RelativeRotation": null,
        "RelativeScale3D": null
    }
}
```

> If an object has a parent, make sure the parent object is defined **before the child object**.

---

## Limitations

Blender's API must run on the main thread, so although save parsing occurs separately, Blender's UI can still become unresponsive when creating or modifying large numbers of objects and collections. 

The extension is still under development and there are some limitations such as missing buildables, models and large saves taking hours to import.

I'm working parse optimizations, and more buildables will be added in newer versions of this extension

> **Note:** Multithreading can crash blender, so this extension cannot currently be published on the Blender Extensions website.

## Examples
### Viewport renders
<img alt="viewport 2" src="resources/images/viewport 2.png" width="350" /><img alt="culling example" src="resources/images/couq sav/culling exmaple.png" width="350" />

### Renders

> Corporate Ladder

<img alt="ladder 1" src="resources/images/renders/ladder 1.png" width="500" />

> Couq's sav

<img alt="couq sav 04" src="resources/images/couq sav/04.png" width="350" /><img alt="couq sav 05" src="resources/images/couq sav/05.png" width="350" />

