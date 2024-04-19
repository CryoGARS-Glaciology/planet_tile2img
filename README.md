# planet_tile2img
[Jukes Liu](https://github.com/jukesliu), [Maddie Gendreau](https://github.com/Maddie-Katie), [Ellyn Enderlin](https://github.com/ellynenderlin), and [Rainey Aberle](https://github.com/RaineyAbe). Department of Geosciences and Cryosphere Remote Sensing and Geophysics (CryoGARS) Lab, Boise State University.
### Contact: jukesliu@boisestate.edu, jukes.liu@gmail.com

### Summary
This repository contains code to pre-process PlanetScope images that may be used as input for glacier velocity mapping using NASA's autonomous Repeat Image Feature Tracking (autoRIFT) software. The images are downloaded using the Planet Labs API as individual tiles that are likely to only partially cover a glacier site. Image pre-processing steps include standardizing the spatial resolution of the image tiles, mosaicking them together along- and across-track, and removing cloudy images prior to feature-tracking. The downloaded images have large file sizes and so the processing for months to years of data takes hours. Therefore, the scripts are also provided as .py scripts which are automatically run in sequence in a bash script `run_monthly_pipeline.sh`. The pipeline requires a user account with Planet Labs and its associated Planet API key, which may be acquired through the NASA Commercial Smallsat Data Acquisition (CSDA) Program.

### Citation
Liu, J., Gendreau, M., Enderlin, E., and Aberle, R. (submitted). Improved records of glacier flow instabilities using customized NASA autoRIFT applied to PlanetScope imagery. _The Cryosphere_.

The repository also contains the code `figure_generation_code.ipynb` used to generate the figures in the manuscript.

# Description
The following diagram visualizes the inputs and steps for our PlanetScope image processing pipeline, including the use of autoRIFT (code in a separate repository called [SK-surge-mapping](https://github.com/jukesliu/SK-surge-mapping)):

![flowchart_v2](https://github.com/CryoGARS-Glaciology/planet_tile2img/assets/48999537/95777145-baa0-4a10-9e7a-9a9ac27befa0)

There are Jupyter notebook (.ipynb) and .py versions of the majority of these scripts. The bash script run_monthly_pipeline.sh, runs the full pipeline for each month of imagery at a time. Choices of which steps to use (e.g., optional coregistration steps) can be modified in the bash script itself. 

### Inputs

The PS image to custom autoRIFT pipeline requires four independent input files to run on a glacier site: 
  1) Glacier outline shapefile

The glacier outline can be downloaded from the Global Land Ice Measurements from Space database with the Randolph Glacier Inventory (RGI) or manually delineated. 

  2) Area of Interest (AOI) shapefile

The AOI shapefile should be a rectangular polygon that covers the glacier and surrounding land. All downloaded images will be cropped to this AOI. If the glacier is large, you may consider cropping the glacier outline and AOI to cover only the portion of the glacier that is of interest in order to reduce computation time.  

  3) A 5-meter resolution geotiff covering the AOI

The 5-m resolution geotiff is used to standardize the spatial resolution for all downloaded imagery, and
contain any type of data. All downloaded PS images will be placed in the standard georeferenced grid extracted from the input 5-m geotiff. The content of the 5-m geotiff does not make a difference, only the spatial grid.
    
  4) A Digital Elevation Model (DEM) covering the AOI

The DEM guides the downstream search in the autoRIFT algorithm and for
georeferencing the output velocity map. The DEM can be of any spatial resolution (the higher the better) because it will be resampled in the `custom_geogrid_autorift_opt` step in the [SK-surge-mapping](https://github.com/jukesliu/SK-surge-mapping)) repo.

### Processing

The PlanetScope NIR-band images are downloaded as individual "tiles", which must be stitched along-track for each satellite overpass. The downloads and subsequent pre-processing steps are applied to monthly batches of images, which are split into subfolders renamed by their date, in yyyy-mm format (`planetAPI_image_download.py`). The download step may fail if a large number of tiles are available for the month. We provide an optional half-month alternative for the download script `planetAPI_image_download_halfmonth.py`, however, users must manually consolidate the folders for each month and rename them with the yyyy-mm to proceed with the following steps. 

The downloaded tiles will be of varying spatial resolutions (3.0-4.2 meters) and must be placed onto a standard (5 meter) grid using `standardize_grid.py`. At this point, we summarize the image tile availability and remove the raw imagery, keeping only the grid-standardized tiles to reduce storage needs using `gather_stats.py`.

The image tiles are first stitched along-track for each satellite, producing a "satellite swath" associated with the acquisition date and PS satellite ID using `stitch_by_sat.py`. Some of the image tiles may be affected by errors in coregistration and may not stitch together smoothly directly. Thus, there is an optional coregistration step, which performs a 2D cross-correlation of the images and finds the x/y offset that corresponds to the maximum normalized correlation value. For each pair of overlapping image tiles, if the correlation value is above the correlation threshold (default 0.8) and the x/y offset is less than the offset threshold (default 2 pixels), then the second image will be shifted by the x/y offset in `coregister_images.py`. These thresholds can be adjusted manually within the pipeline.

There may be multiple overlapping satellite swaths on a single day. Acquisition time for the swaths can differ by hours. In order to produce a single image for the day, one may select the largest satellite swath automatically using `select_largest_satswath.py` or manually select the best satellite swath. Another option available through the pipeline is to automatically stitch together all the satellite swaths for the day, which produces a final image with greater spatial coverage than the individual satellite swaths, using `stitch_satswaths_by_date`. The diagram below visualizes the process for both scenarios (single satellite swath versus multiple satellite swaths), including another optional coregistration step.

![workflow_withimagery](https://github.com/CryoGARS-Glaciology/planet_tile2img/assets/48999537/d59a901e-f5bc-4730-bad3-1d09a4fccf09)

Once the largest satellite swath or stitched swaths for each date are selected, these final images are cropped to the AOI. Those images with greater than 50% data coverage over the glacier area, determined using the glacier shapefile, are moved into a separate folder with `crop_move_finalimgs.py`. Then, images with clouds covering part or all of the glacier must be removed using manual or automated approaches. The `cloud_filtering.ipynb` script provided automatically plots the imagery to aid manual filtering and includes optional steps to test automated filtering methods, which analyze gradients in pixel intensities. 

### Directory structure
The directory structure required for each site:
```
.
├── ...
├── inputs                          # Folder containing the input GIS shapefiles
├── base_path                       # Folder holding the monthly Planet images
│   ├── noncloudy_images            # Empty folder that will contain the final processed images that are ready for input to custom autoRIFT
│   ├── yyyy-mm                     # Sub-directory with one month of imagery
│   ├── yyyy-mm                     # Sub-directory with one month of imagery
│   │   ├── standard_grid           # Folder that holds all the 5m resampled imagery
│   │   ├── stitched_by_sat         # Folder that holds the along-track mosaicked images
│   │   ├── stitched_imgs           # Folder that holds the final images for each acquisition date (either a single along-track swath or a mosaic of all swaths for the day)
│   │   └── ...
│   └── ...
└── ...
```

If the `planetAPI_image_download_halfmonth.py` download script is used, the user must consolidate the downloads into yyyy-mm subfolders that follow the structure shown above. Use of the `planetAPI_image_download.py` script automatically generates the monthly subfolders and the subsequent codes automatically generate the `stitched_by_sat` and `stitched_imgs` folders.

### Running the full pipeline using the bash script
Running several months at a time is recommended to start:
```
sh run_pipeline_monthly.sh 2021-06 2021-12 /path/to/WGS/projection/AOI/shapefile.shp /path/to/UTM/projection/AOI/shapefile_UTM.shp /path/to/5m/raster.tif / /path/to/glacier/outline.shp /path/to/desired/download/folder/ INSERT_PLANET_API_KEY /path/to/final/directory/to/store/noncloudy/images/
```
where 2021-06 is the starting month and 2021-12 is the ending month. Images will be downloaded an processed from June 1, 2021 to December 31, 2021.

## Installation of the CautoRIFT environment with micromamba

(0)	Install micromamba
```
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
```

(1) Create a new environment named "cautorift" with python 3.8.16
```
micromamba create -n cautorift python=3.8.16
```

(2) Activate the environment. Then, download the following packages into the environment in the following order:
```
micromamba activate cautorift

micromamba install autorift=1.1.0=py38hd9c93a9_0 -c conda-forge

micromamba install notebook matplotlib pandas -c conda-forge

micromamba install opencv=4.5.0 -c conda-forge

micromamba install rasterio=1.2.10
```
(2) Find the correct __autoRIFT.py__ script (within `micromamba/envs/cautorift/`) using the search bar in Finder and find & replace all the instances of __np.bool__ to __bool__ and __np.int__ to __int__. See my __autoRIFT.py__ path below for reference:

```
~/micromamba/envs/cautorift/lib/python3.8/site-packages/autoRIFT/autoRIFT.py

```
## Note on using the planetAPI_image_download code

PlanetScope is currently making changes to how their data is stored and accessed. If an error comes up which says "ModuleNotFoundError" or something similar indicating there might be a package issue, check the PlanetScope site documentation first to see if there was an update to how the data is stored/accessed which might require some tweaking to either the "planetAPI_image_download" code or the "PlanetScope_orders_utils.py" document.

(1) Open the terminal on your device and open a Jupyter Notebook.

(2) Open the "planetAPI_image_download" code. The first time you run the "Import necessary packages" code block at the top, you may find that you have to import some packages. When you do so, make sure to import the correct version (listed under "Download The autoRIFT Environment"). Where it says "sys.path.insert" in this block of code, make sure to point the directory to the location of the "planet_tile2img" package on your device.

(3) In the next block of code ("Define filters for image search"), make sure to point the "file_name" path towards your box shapefile around your glacier of interest. The output should say 'type,' 'polygon,' then list the coordinates of your shapefile.

(4) In the next block of code, you will be prompted to add the start and end dates between which you want images. One month is our recommended maximum time separation between the two dates, otherwise the download might fail or take 60 minutes+ to download. This code block also requires that you put in your API key and the outfolder where you would like the data to be saved.

(5) You won't need to change anything else in the planet_tile2img code. make sure to let each step run completely before moving onto the next. When you run the code block titled "Authentication via basic HTTP," you should get <Response [200]> as the output. When you run the two code blocks under the heading "Compile filters and use Quick Search to grab image IDs," you should get the number if images avaliable to download as the output. Polling for success and downloading the results could both take up to 30 minutes to finish, depending on the number of avaliable images.

## Customized autoRIFT code
The customized geogrid/autoRIFT code exists in a separate repository contained and described here: [SK-surge-mapping](https://github.com/jukesliu/SK-surge-mapping).

# Funding and Acknowledgements
This research is funded by NASA FINNEST Award 80NSSC21K1640, NSF Award ANS1954006, and the Department of Defense SMART Scholarship.
