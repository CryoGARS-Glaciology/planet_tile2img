# planet_tile2img Workflow

The following diagram visualizes the input and output for each step of our Python Package including the use of autoRIFT:

![planet_tile2img_workflow](https://github.com/CryoGARS-Glaciology/planet_tile2img/assets/48999537/98cfa837-720f-4603-bbfe-07ac1a614822)


## A Note on PlanetScope
PlanetScope is currently making changes to how their data is stored and accessed. If an error comes up which says "ModuleNotFoundError" or something similatr indicating there might be a package issue, check the PlanetScope site documentation first to see if there was an update to how the data is stored/accessed which might require some tweaking to either the "planetAPI_image_download" code or the "PlanetScope_orders_utils.py" document.

## Create the autoRIFT Environment
** This will be added, or all the specification for what needs to be downloaded into the new environment will be added **

(1) Create a new environment

(2) Download the following packages into the environment:

PLEASE NOTE THESE ARE VERSION SPECIFIC!

** This will be added, or how to download the environment will be added **

## Using the planetAPI_image_download Code
(1) Open the terminal on your device and open a Jupyter Notebook.

(2) Open the "planetAPI_image_download" code. The first time you run the "Import necessary packages" code block at the top, you may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment"). Where it says "sys.path.insert" in this block of code, make sure to point the directory to the location of the "planet_tile2img" package on your device.

(3) In the next block of code ("Define filters for image search"), make sure to point the "file_name" path towards your box shapefile around your glacier of interest. The output should say 'type,' 'polygon,' then list the coordinates of your shapefile.

(4) In the next block of code, you will be prompted to add the start and end dates between which you want images. One month is our recommended maximum time seperation between the two dates, otherwise the download might fail or take 60 minutes+ to download. This code block also requires that you put in your API key and the outfolder where you would like the data to be saved.

(5) You won't need to change anything else in the planet_tile2img code. make sure to let each step run completely before moving onto the next. When you run the code block titled "Authentication via basic HTTP," you should get <Response [200]> as the output. When you run the two code blocks under the heading "Compile filters and use Quick Search to grab image IDs," you should get the number if images avaliable to download as the output. Polling for success and downloading the results could both take up to 30 minutes to finish, depending on the number of avaliable images.

## Using the interpolate_images_to_DEM Code
(1) Run the code block to import all necessary packages. You may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment").

(2) Set the "dempath" to the path to your DEM for your glacier of interest. We recommend a 5m DEM to take advantage of the high-resolution PlanetScope images.

(3) Set your imagepath to where the images currently exist and your outpath to where you'd like the referenced set of images to go. Make sure to put a folder named "out" in your outpath.

You should not need to change anything else in this code.

Please note, all images need to be on a standard grid. The DSM is used as a target spatial reference system to which image scenes will be referenced if the source spatial reference system does not match the DSM. This reprojection specifically references the images to the target spatial reference system and does not change the actual coordinate reference system. For all images scenes, the final product is saved in the designated out folder and “_5m” is added to the end of the image name to designate that it had been resampled.

## Using the planet_stitch_coreg_boundaries Code
(1) Run the code block to import all necessary packages. You may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment").

(2) Set the basepath as the pervious code's outpath. Under "mask_path," are in the directory to your rasterized glacier mask. Make sure this is in the same UTM zone as your galcier (or at least, as the majority of your glacier).

(3) In the code block under "Remove those images that cover less than 50% of the glacier and crop images to the bounding box," add in the path to your glacier shapefile where it says "with fiona.open..." Where is says 'Boxpath", point it to the box shapefile for the glacier.

You should not need to change anything else in this code. The final imaged will have "_clipped" added to the end.

Please note, at this point, the images have been stitched and can be used. We continue on to describe the use of our customized autoRIFT code, but the images themselves are done being mosaicked and are useable at this point in the pipeline. Even with earlier filtering, some images will be obstructed by clouds or shadows. If the images are to be used in autoRIFT or another processing pieline, we recommend they first be manually filtered to remove obstructed images.

## Using the autoRIFT Code
The customized geogrid/autoRIFT code exists in a separate repository linked here: [SK-surge-mapping](https://github.com/jukesliu/SK-surge-mapping).
