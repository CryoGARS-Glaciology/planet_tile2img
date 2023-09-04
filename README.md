# planet_tile2img Workflow

The following PDF visualizes the input and output for each step of our Python Package including the use of autoRIFT:

[planet_tile2img Workflow.pdf](https://github.com/CryoGARS-Glaciology/planet_tile2img/files/12516182/planet_tile2img.Workflow.pdf)

## A Note on PlanetScope
PlanetScope is currently making changes to how their data is stored and accessed. If an error comes up which says "ModuleNotFoundError" or something similatr indicating there might be a package issue, check the PlanetScope site documentation first to see if there was an update to how the data is stored/accessed which might require some tweaking to either the "planetAPI_image_download" code or the "PlanetScope_orders_utils.py" document.

## Download The autoRIFT Environment
** This will be added, or all the specification for what needs to be downloaded into the new environment will be added **

(1) Create a new environment

(2) Download the following packages into the environment:

PLEASE NOTE THESE ARE VERSION SPECIFIC!

** This will be added, or how to download the environment will be added **

## Download or fork then download the planet_tile2img code
Make sure the code exists on your device.

## Using the planetAPI_image_download Code
(1) Open the terminal on your device and open a Jupyter Notebook.

(2) Open the "planetAPI_image_download" code. The first time you run the "Import necessary packages" code block at the top, you may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment"). Where it says "sys.path.insert" in this block of code, make sure to point the directory to the location of the "planet_tile2img" package on your device.

(3) In the next block of code ("Define filters for image search"), make sure to point the "file_name" path towards your box shapefile around your glacier of interest. The output should say 'type,' 'polygon,' then list the coordinates of your shapefile.

(4) In the next block of code, you will be prompted to add the start and end dates between which you want images. I would recommend one month as a maximum time seperation between the two dates, otherwise the download might fail or take 60 minutes+ to download. This code block also requires that you put in your API key and the outfolder where you would like the data to be saved.

(5) You won't need to change anything else in the planet_tile2img code. make sure to let each step run completely before moving onto the next. When you run the code block titled "Authentication via basic HTTP," you should get <Response [200]> as the output. When you run the two code blocks under the heading "Compile filters and use Quick Search to grab image IDs," you should get the number if images avaliable to download as the output. Polling for success and downloading the results could both take up to 30 minutes to finish, depending on the number of avaliable images.

## Using the interpolate_images_to_DEM Code
(1) Run the code block to import all necessary packages. You may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment").

(2) Set the "dempath" to the path to your DEM for your glacier of interest. I recommend a 5m DEM to take advantage of the high-resolution PlanetScope images.

(3) Set your imagepath to where the images currently exist and your outpath to where you'd like the referenced set of images to go. Make sure to put a folder named "out" in your outpath.

You should not need to change anything else in this code.

## Using the planet_stitch_coreg_boundaries Code
(1) Run the code block to import all necessary packages. You may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment").

(2) Set the basepath as the pervious code's outpath. Under "mask_path," are in the directory to your rasterized glacier mask. Make sure this is in the same UTM zone as your galcier (or at least, as the majority of your glacier).

(3) In the code block under "Remove those images that cover less than 50% of the glacier and crop images to the bounding box," add in the path to your glacier shapefile where it says "with fiona.open..." Where is says 'Boxpath", point it to the box shapefile for the glacier.

You should not need to change anything else in this code.

## Using the autoRIFT Code
** Coming Soon **
