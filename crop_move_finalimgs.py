#!/usr/bin/env python
# coding: utf-8

# # Remove images that cover < 50% of the glacier area

# In[4]:


import fiona
import os
import numpy as np
import sys
import subprocess
import shutil
import rasterio as rio
from rasterio.mask import mask


# In[ ]:


args = sys.argv
shp_path = args[1]
boxpath = args[2]
stitchedpath = args[3]
out_folder = args[4]


# In[76]:


# Read glacier shapefile
# shp_path = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/main_ice_outline.shp'
with fiona.open(shp_path, "r") as shapefile:
    shapes = [feature["geometry"] for feature in shapefile]


# In[77]:


# stitchedpath = basepath+'stitched_images/' # path to the stitched images
# boxpath = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/BoxTurner/BoxTurner_UTM_07.shp'

# multiply each image by glacier mask
for file in os.listdir(stitchedpath):
    if file.startswith('PS') and not file.endswith('clipped.tif'):
        print(file)
        
        # read image file and crop to glacier outline
        with rio.open(stitchedpath+file) as src:
            out_image, out_transform = mask(src, shapes, crop=True)

        # calculate number of non-empty pixels over the glacier
        total_pixels = np.count_nonzero(out_image[0])
        out_image[np.isnan(out_image)] = 0 # set all Nans to 0
        pixels_w_data = np.count_nonzero(out_image) # count non nans (number of pixels with data)
        
        # print data percent
        if pixels_w_data > 0:
            data_percent = int(pixels_w_data/total_pixels*100)
        else:
            data_percent = 0
        print(data_percent, '%')
        
        # remove if it does exist:
        if file[:-4]+'_clipped.tif' in os.listdir(stitchedpath):
            os.remove(stitchedpath+file[:-4]+'_clipped.tif')
            
        # if data percent > 50, and clipped version doesn't already exist:
        if data_percent >= 50:
            # Crop file
            crop_cmd = 'gdalwarp -cutline '+boxpath+' -crop_to_cutline '
            crop_cmd += stitchedpath+file+' '+stitchedpath+file[:-4]+'_clipped.tif'
            print(crop_cmd); print()

            subprocess.run(crop_cmd,shell=True,check=True); print()
        else:
            print('Remove', file)
#             os.remove(stitchedpath+file) # currently keeps it


# # Move into new folder

# In[78]:


# out_folder = '/Volumes/SURGE_DISK/PS_downloads_SK/noncloudy_for_autorift/'
    
for searchfile in os.listdir(stitchedpath):
    if searchfile.endswith('clipped.tif'):
        shutil.copy(stitchedpath+searchfile, out_folder+searchfile)


# In[ ]:




