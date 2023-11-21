#!/usr/bin/env python
# coding: utf-8

# # stitch_by_sat
# 
# For each day's satellite acquisitions, grab all the tiles for each satellite and stitch them together into a "satellite chunk". Remove those satellite chunks that cover less than a third of the glacier (evaluated using a glacier outline shapefile).

# In[139]:


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


# In[ ]:


import sys
args = sys.argv
basepath = args[1] # image path
aoi_shp = args[2] # aoi shapefile path


# inputs: -img_path -glacier_shpfile_path

# In[149]:


# basepath = '/Volumes/SURGE_DISK/PS_downloads_SK/2020-09/PSScene/standard_grid/' # path to grid standardized images


# In[141]:


# path to study area shapefile
# aoi_shp = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/BoxTurner_UTM_07.shp'
aoi_gdf = gpd.read_file(aoi_shp)
aoi = aoi_gdf.geometry.values
print(aoi[0])


# In[150]:


# # path to glacier shapefile
# glacier_shp = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/main_ice_outline.shp'
# glacier_gdf = gpd.read_file(glacier_shp)
# glacier = glacier_gdf.geometry.values
# glacier[0]


# # Coregister and stitch all Planet tiles for each image date

# In[143]:


# grab all satellite IDs and dates of imagery
filelist = os.listdir(basepath); filelist.sort()
dates = []; IDs = []; files = []
no_tiles  = 0
for file in filelist:
    if file.startswith('2') and file.endswith('.tif'):
        date = file.split('_')[0] # grab the date
        sID = file.split('_')[-7] # grab the satellite ID (4 digit code)
        dates.append(date); IDs.append(sID); files.append(file) # append to list
        no_tiles+=1
sorted_dates = list(set(list(zip(dates, IDs)))) # set of the zipped date and ID
sorted_dates.sort() # sorted
satdate_df = pd.DataFrame(sorted_dates, columns=['date','sat_ID'])
satdate_df.head()


# In[144]:


# Grab the first Planet tile for reference CRS and Transform
reftile = rio.open(basepath+filelist[3])
print(reftile.crs)
print(reftile.transform)
print(reftile.shape)


# In[145]:


binary_thresh = 1
for idx, row in satdate_df.iterrows():
    date = row.date
    ID = row.sat_ID
    print('TILES FOR', date, ID)
    outfilename = 'PS_'+date+'_'+ID+'.tif'
    if not os.path.exists(basepath+"stitched_by_sat/"):
        os.mkdir(basepath+"stitched_by_sat/")
    if not os.path.exists(basepath+"stitched_by_sat/"+outfilename):
    
        # Grab the Planet tiles corresponding to each unique date
        tiles = glob.glob(basepath+'/'+date+'*'+ID+'*clip_5m.tif') # grab all file paths for that date
        tiles.sort()
        print(tiles)

        # initialize empty arrays
        overlap_total = np.zeros(reftile.shape);
        sr_stitched = np.zeros(reftile.shape) # start with empty stitched product
        t = 0 # tile count

        for tile in tiles:
            # open image tile, determine overlap with AOI, remove if none
            reader = rio.open(tile); sr = reader.read(1) # load the tile
            try:
                out_image, out_transform = mask(reader, [mapping(aoi[0])], crop=True)
                crop_array = out_image[0,:,:]
                # if no overlapping pixels, remove
    #             if np.count_nonzero(~np.isnan(crop_array)) == 0:
                if np.count_nonzero(crop_array[~np.isnan(crop_array)]) == 0:
                    print('remove '+tile)
                    os.remove(tile)
                    continue
            except Exception:
                # if it fails to crop, then remove
    #             print('remove '+tile)
                continue

            # if there is overlap, continue with processing
            sr[sr == 0] = np.NaN # remove black background, replace with Nans
            sr_data = sr.copy() # make a copy of the data before making the data binary
            sr[sr>0.0] = 1 ; sr[np.isnan(sr)] = 0 # make tile binary

            tilesize = np.count_nonzero(sr) # grab the current tile size (pixels)
            overlap_total = overlap_total+sr # add new overlap to overlap total

            if t==0: # just add the first one
                sr_stitched = np.nansum([sr_data, sr_stitched],0) # add them to the stitched product
            else:
                # for all subsequent, find the overlapping area:
                overlap_band = ma.masked_not_equal(overlap_total, 2) # identify non-overlapping area (not 2)
                overlap_band_mask = ma.getmaskarray(overlap_band)

                # identify which tile is larger
                if tilesize > prev_tilesize:
                    print('Current tile is larger.')
                    larger_tile = sr_data; smaller_tile = sr_stitched # assign the tiles
                elif tilesize < prev_tilesize:
                    print('Previous tile is larger.')
                    larger_tile = sr_stitched; smaller_tile = sr_data # assign the tiles
                else: # equal sizes
                    print('Tiles are the same size.')
                    larger_tile = sr_data; smaller_tile = sr_stitched # use current tile to coregister

                # identify which overlapping tile is larger or smaller
                overlap_values_l = ma.masked_where(overlap_band_mask, larger_tile)
                overlap_values_larger = ~overlap_values_l.mask*overlap_values_l.data
                overlap_values_s = ma.masked_where(overlap_band_mask, smaller_tile)
                overlap_values_smaller = ~overlap_values_s.mask*overlap_values_s.data

                # remove overlap area from smaller tile and add to total
                smaller_tile_coreg = ma.masked_where(~overlap_band_mask, smaller_tile) 
                masked_smaller_tile_coreg = ~smaller_tile_coreg.mask*smaller_tile_coreg.data
                sr_stitched = np.nansum([masked_smaller_tile_coreg, larger_tile],0) 

                overlap_total[overlap_total > 1] = 1 # reset overlap total values to be 1
                # Store tile info for the next round of comparison
                prev_overlap = overlap_band.size # amount of pixels overlapping
            prev_tilesize = np.count_nonzero(sr_stitched) # previous tile size (pixels w/ data)
            sr_prev = sr_data
            sr_stitched[sr_stitched == 0]=np.NaN # fill black pixels with NaNs
            t += 1 # increment tile count

    #     # Plot final stitched image
    #     fig = plt.figure(); im = plt.imshow(sr_stitched, cmap='gray'); plt.title('Stitched'); 
    #     fig.colorbar(im); plt.show()

        # Export stitched image

        with rio.open(basepath+"stitched_by_sat/"+outfilename,'w',
                          driver='GTiff',
                          height=sr_stitched.shape[0], # new shape
                          width=sr_stitched.shape[1], # new shape
                          dtype=sr_stitched.dtype, # data type
                          count=1,
                          crs=reftile.crs, # the EPSG from the original DEM
                          transform=reftile.transform) as dst:
                dst.write(sr_stitched, 1)

        del overlap_total; del sr_stitched # clear variables
    


# # Delete those empty images

# In[148]:


for newfile in os.listdir(basepath+"stitched_by_sat/"):
    if newfile.startswith('PS') and newfile.endswith('.tif'):
        reader = rio.open(basepath+"stitched_by_sat/"+newfile)
        try:
            # crop to glacier outline
            out_image, out_transform = mask(reader, [mapping(glacier[0])], crop=True)
            crop_array = out_image[0,:,:]
            
#             # plot
#             plt.imshow(crop_array); plt.colorbar(); plt.title(newfile)
#             plt.show()
            
            # count coverage
            coverage = np.count_nonzero(crop_array[~np.isnan(crop_array)])
            
            # If image is empty, remove:
            if np.nanmax(crop_array) == 0:
                print('remove empty tile',newfile)
                os.remove(basepath+"stitched_by_sat/"+newfile)
                
#             # set all nonzeros to 1 to count glacier pixels
#             crop_array[crop_array != 0] = 1
#             glacier_pixels = np.count_nonzero(crop_array)
            
#             # if overlapping pixels is less than 25% of the total glacier pixels 
#             if coverage/glacier_pixels < 0.33:
#                 print('Coverage is',str(int(coverage/glacier_pixels*100)),'% remove '+newfile)
#                 os.remove(basepath+"stitched_by_sat/"+newfile)
        except Exception:
            # if it fails to crop, then remove
#             print('remove '+tile)
            continue


# In[ ]:




