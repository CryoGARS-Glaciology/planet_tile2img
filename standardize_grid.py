#!/usr/bin/env python
# coding: utf-8

# # standardize_grid
# 
# - Resample images to standard grid using a 5m geotiff
# - Remove those that do not cover any of the glacier

# In[ ]:


import rasterio as rio
from rasterio.mask import mask
from shapely.geometry import mapping
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp2d
from rasterio.warp import reproject, Resampling
from osgeo import gdal
import shutil
import geopandas as gpd


# inputs: -aoi_shpfile_path -dem_path -img_path -out_path

# In[ ]:


import sys
args = sys.argv
aoi_shp = args[1]
dempath = args[2]
imgpath = args[3]
outpath = args[4]


# ### Glacier shapefile

# In[ ]:


# path to study area shapefile
# aoi_shp = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/BoxTurner_UTM_07.shp'
aoi_gdf = gpd.read_file(aoi_shp)
aoi = aoi_gdf.geometry.values
aoi[0]


# ### Read in DEM (or any 5m resolution geotiff) that is clipped to the AOI used to download the images

# In[ ]:


##############
# dempath = '/Users/jukesliu/Documents/TURNER/DATA/VELOCITY_MAPS/forAutoRIFT/IfSAR_DSM_5m_cropped.tif'
##############


# In[ ]:


dsm = rio.open(dempath) # open using rasterio
elev = dsm.read(1) # read in the first and only band (elevations)
dsm_resolution = dsm.transform[0]
print(dsm_resolution)


# ### Grab the spatial information (that the images will be standardized to)

# In[ ]:


# grab the x and y grid values for the DSM
dsm_x = np.linspace(dsm.bounds.left, dsm.bounds.right, num=np.shape(elev)[1])
dsm_y = np.linspace(dsm.bounds.top, dsm.bounds.bottom, num=np.shape(elev)[0])


# In[ ]:


# # Display the raster
# fig, ax1 = plt.subplots(1,1)
# hs_im = ax1.imshow(elev, cmap='Greys_r', vmin=0)
# fig.colorbar(hs_im, ax=ax1,label='Elevation [m]')
# plt.show()


# # Standardize all images in a folder to the DEM

# In[ ]:


# imgpath = '/Volumes/SURGE_DISK/PS_downloads_SK/2020-09/PSScene/' # enter path to folder with all the images to resample
# outpath = '/Volumes/SURGE_DISK/PS_downloads_SK/2020-09/PSScene/standard_grid/' # output files
if not os.path.exists(outpath):
    os.mkdir(outpath)
    
    
for imgname in os.listdir(imgpath): # loop through all images
    if imgname.endswith("SR_harmonized_clip.tif"):
        print(imgname)
        
        # create folder to hold reprojected images
        if not os.path.exists(imgpath + 'reprojected/'):
            os.mkdir(imgpath + 'reprojected/')
        
        # grab the CRS for the image and the DEM
        raster = gdal.Open(imgpath + imgname)
        projstg = raster.GetProjection()
        imgcrs = projstg.split('EPSG')[-1][3:8]
        # if they aren't equal, then reproject and copy
        if 'EPSG:' + imgcrs != str(dsm.crs):
            gdal.Warp(imgpath + 'reprojected/' + imgname, imgpath + imgname, dstSRS=str(dsm.crs))
            print('reprojecting' + imgname)
        else:
            # otherwise just copy
            shutil.copy(imgpath + imgname, imgpath + 'reprojected/'+ imgname)
    
        # open the reprojected image
        img = rio.open(imgpath + 'reprojected/'+ imgname) # open using rasterio
        img_data = img.read() # grab the NIR band, 4
        
        try:
            # remove those that don't overlap the glacier at all
            # crop to glacier outline
            out_image, out_transform = mask(img, [mapping(aoi[0])], crop=True)
            crop_array = out_image[0,:,:]

#             plt.imshow(crop_array); plt.colorbar()  # plot
#             plt.show()

            coverage = np.count_nonzero(crop_array[~np.isnan(crop_array)]) # count coverage

            # If image is empty, remove:
            if np.nanmax(crop_array) == 0 or coverage == 0:
                print('remove empty tile',imgname)
                os.remove(imgpath + 'reprojected/'+ imgname)
        except Exception:
            print('remove empty tile',imgname)
            os.remove(imgpath + 'reprojected/'+ imgname)
            continue
            
        # select band and gather image dimensinos
        print(len(img_data))
        if len(img_data) == 4:
            nir = img_data[3]
        elif len(img_data) == 1:
            nir = img_data[0]
        print("Image dimensions:",nir.shape)
        # grab the x and y grid values for the DSM
        img_x = np.linspace(img.bounds.left, img.bounds.right, num=np.shape(nir)[1])
        img_y = np.linspace(img.bounds.top, img.bounds.bottom, num=np.shape(nir)[0])
        
        # resample
        f = interp2d(img_x, img_y, nir) # create img interpolation object
        nir_resamp = np.zeros(np.shape(elev)) # initialize resampled image with DSM shape
        nir_resamp = f(dsm_x,dsm_y) # resample the NIR data to the DSM coordinates
        nir_resamp = np.flipud(nir_resamp) # flip up down
        print("Resample to DSM dimensions:",elev.shape)
        
        # save the resampled image to georeferenced tif file
        outfile = imgname[:-4]+'_'+str(round(dsm_resolution))+'m.tif' # generate new filename with 5m suffix
        print("Save resampled image to", outfile)
        with rio.open(outpath+outfile,'w',
                            driver='GTiff',
                            height=nir_resamp.shape[0],
                            width=nir_resamp.shape[1],
                            dtype=nir_resamp.dtype,
                            count=1,
                            crs=dsm.crs,
                            transform=dsm.transform) as dst:
                dst.write(nir_resamp, 1)
        print(imgname + ' resampled')
        print(np.nanmin(nir_resamp), np.nanmax(nir_resamp))

#         plt.imshow(nir_resamp, cmap='Greys')
#         plt.colorbar()
#         plt.show()

print("All images resampled.")

print("outpath", outpath)
print("outfile", outfile)



# In[ ]:




