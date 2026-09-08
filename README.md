# satisfactory-to-blender
A **blender extension** that imports **save data** and **models** for the game Satisfactory by Coffee Stain Studios. This addon reconstructs your satisfactory save file in blender using (repo) by (name) for save parsing and imports models and materials you have extracted using Fmodel.

## Features
Import save data:
- Rebuild save file in blender
- Rebuild the buildable logic using geometry nodes
- Auto appends models from asset library into file or use models in blend files
- Option to only import buildables with a set boundary 
- Option to import specific buildable types
- Option to generate a proxy mesh in viewport 
- Option to hide buildable after import
- Shows import progress for each buildable
- Show execution time for each buildable type
- Object culling based on their distance from an object (e.g. camera)
- Random object scale to help with clipping

Import models:
- Uses the json build file to look for and import the models used by that buildable.
- Builds and applies materials
- Creates an asset library and the imported models

>Note: save importing, can take a really long time depending on the amount of buildables in the save file

>Note: there are still a few buildables and models that this addon doesn’t import yet, such as items, resources and vehicles. I will try to add them over time.

>Note: this addon is very memory heavy

## Installation
1. Download the latest version of the extension as `.zip` file
2. In Blender, go to Edit > Preferences > Get Extensions.
3. Click Install from disk and select the .zip file.
4. Blender will then install the addon and a new panel called ‘SF Importer’ will appear in the side panel.

> Note: this addon uses the Unreal PSK/PSA (.psk/.psa) addon for importing models. Make sure this is installed before using the addon


## Configuration
### addon preferences tab
1. Open the preferences data, navigate to ‘Add-ons’ and search for ‘Satisfactory Importer’,
In the addon preferences tab:
2. In the addon preferences tab, add the path to where Fmodel extracted models.
3. Click the ‘generate buildable_to_asset.json’ button to generate in the addon's files, or to a custom directory if you want. You can then edit that file to choose what buildables the addon should try and import.
4. Click Copy asset library file to asset library path button to get the SF_Asset_lib.blend file from the addon file, which will have the geo node groups and materials shader groups needed for the import save logic and material logic.
   
> Note: Copy the asset library in a different directory from your main asset library, as it will overwrite the ‘blender_assets.cats.txt’, deleting any categories you’ve made.

## How to use
### Importing and building asset library
1. To build your asset library, open the blend file it copied and click ‘Start Building’ in the side panel to import the extracted models into the blend file, make sure you enable Mark as Asset so it can build your asset library. You can import models in a different blender, but it will not be able to build materials and create the asset library automatically.

> Note: this process can take a while depending on the amount of models it needs to import

### Importing SF sav data and building factories
1. To make the addon use your asset library, enable ‘Use Library Models’. This will append the models from the SF_Asset_Lib file before importing save data instead of using models in the current blend file. Blender will hang while it appends the model, so you can open the system console to see if it's still appending models. If the buildable uses a lot of models such as the trading post, it will take a minute to import them all.

The addon parses the save file in a separate thread, so it does not freeze blender’s ui. any blender api has to run on the main thread, so the ui will be frozen when creating/modifying objects and collections. This can be very noticeable when working with buildables with large amounts of instances.
Appending models from your asset library will cause the save import to take longer, luckily, it only needs to be enabled if there's a buildable missing from your blend file.

Note: Blender doesn't like multi-threading all that much, so this add-on can not be published on the blender extensions website :/

You can choose to import between 4 buildable types individually or all at once
Signs and spline buildables are usually the most heavy to import, I recommend importing them separately.


## Examples

## Links
Blend files and models:
https://drive.google.com/drive/folders/1WsMy-5pSLq6aG9CHV5y8WLRiKYzqA5k9
