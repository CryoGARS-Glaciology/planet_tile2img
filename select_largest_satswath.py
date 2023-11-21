#!/usr/bin/env python
# coding: utf-8

# In[1]:


import rasterio as rio
from rasterio.mask import mask
import cv2
import fiona
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import os
import subprocess
import shutil
from scipy.interpolate import interp2d
import glob 
import pandas as pd
from shapely.geometry import mapping
import geopandas as gpd


# In[43]:


import sys
args = sys.argv
basepath = args[1]
glacier_outline = args[2]


# In[33]:


# basepath = '/Volumes/SURGE_DISK/PS_downloads_VG/2021-06/PSScene/standard_grid/' # path to grid standardized images
# glacier_outline = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/VG/Variegated_polygon_UTM07.shp'
if not os.path.exists(basepath+'largest_satchunk/'):
    os.mkdir(basepath+'largest_satchunk/')


# In[37]:


# read in glacier shapefile
glacier_gdf = gpd.read_file(glacier_outline)
glacier = glacier_gdf.geometry.values


# In[19]:


# grab all the unique dates
dates = []
for file in os.listdir(basepath): # path
    date = file.split('_')[1] # grab the date from the file name
    dates.append(date)
unique_dates = list(set(dates)) # save a list of the dates
unique_dates.sort() # sort the dates
print(unique_dates)


# In[42]:


for date in unique_dates:  
    print('TILES FOR', date)
    tiles = glob.glob(basepath+'/PS_'+date+'*.tif') # grab all file paths for that date
    print(tiles)
    if len(tiles) > 1:
        coverage_compare = [] # find the tile with the greatest coverage over the glacier outline
        for tile in tiles:
            reader = rio.open(tile) # open the file
            # crop image to glacier outline to determine coverage
            try:
                out_image, out_transform = mask(reader, [mapping(glacier[0])], crop=True)
                crop_array = out_image[0,:,:]
                coverage = np.count_nonzero(crop_array[~np.isnan(crop_array)]) # calculate pixels of coverage
                coverage_compare.append(coverage)
            except Exception:
                coverage_compare.append(np.NaN)
                continue
            
        # determine the file with the greatest glacier coverage
        ref_img_idx = np.nanargmax(coverage_compare)
        reffile = tiles[ref_img_idx]
        print(reffile)
        
        # copy over that image to new folder
        shutil.copyfile(reffile, basepath+'largest_satchunk/'+reffile.split('/')[-1][:11]+'.tif')    
            
    elif len(tiles) == 1: # if there is only one, copy it over and remove sat ID
        shutil.copyfile(tiles[0], basepath+'largest_satchunk/'+tiles[0].split('/')[-1][:11]+'.tif')
        


# In[ ]:




