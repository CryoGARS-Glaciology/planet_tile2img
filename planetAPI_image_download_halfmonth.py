#!/usr/bin/env python
# coding: utf-8

# # Notebook to bulk download PlanetScope imagery through an API
# 
# Contributors: Rainey Aberle (raineyaberle@boisestate.edu), Maddie Gendreau, Jukes Liu
# 
# Modified from [Planet Developers API Tutorial](https://developers.planet.com/docs/apis/data/) and [Planet Labs: `ordering_and_delivery.ipynb`](https://github.com/planetlabs/notebooks/blob/master/jupyter-notebooks/orders/ordering_and_delivery.ipynb )
# 

# ### Import necessary packages

# In[85]:


import os
import glob
import json
import requests
import time
import geopandas as gpd
from shapely import geometry as sgeom
from pathlib import Path
import rasterio as rio
import numpy as np
import sys
from rasterio.plot import show
from requests.auth import HTTPBasicAuth
# add path to functions
sys.path.insert(1, '/Users/jukesliu/Documents/GitHub/planet_tile2img/')
import PlanetScope_orders_utils as orders


# inputs: -start_month yyyy-mm -end_month yyyy-mm -aoi_shpfile_path -api_key

# In[113]:


args = sys.argv
start_month = args[1]
end_month = args[2]
aoi_path = args[3]
API_key = args[4]
out_folder=args[5]


# ### Install Planet API Client
# 
# This will allow you to interact with the Planet API through this notebook. Refer to the __[Planet API documentation](https://developers.planet.com/docs/apis/data/)__ for more info. 

# In[ ]:


# !conda install -c conda-forge planet -y


# ### Define filters for image search
# #### _Modify these sections_

# In[86]:


#### OPTION 2: Import an existing shapefile

# Name of your file
# If your shapefile is not currently in this directory, you need to include the full file path in 'file_name' below
# file_name = '/Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/BoxTurner/BoxTurner_WGS.shp'

# Read in the shapefile
AOI = gpd.read_file(aoi_path)

# File extension index (we don't want the .shp extension in the next line)
i = aoi_path.index('.shp')

# Convert to geojson
AOI.to_file(aoi_path[0:i]+'.geojson', driver='GeoJSON')

# Adjust AOI polygon to a rectangular shape 
# Planet only excepts a bounding BOX as a spatial filter, 
# so we need to convert our AOI to a box (if it is not already). 
AOI_box = {"type": "Polygon",
           "coordinates": [[
               [AOI.bounds.minx[0],AOI.bounds.miny[0]],
               [AOI.bounds.maxx[0],AOI.bounds.miny[0]],
               [AOI.bounds.maxx[0],AOI.bounds.maxy[0]],
               [AOI.bounds.minx[0],AOI.bounds.maxy[0]],
               [AOI.bounds.minx[0],AOI.bounds.miny[0]]
           ]]
          }
AOI_box_shape = sgeom.shape(AOI_box)
AOI_box


# In[95]:


# ----------AOI clipping----------
# Would you like to clip images to the AOI (True/False)?
clip_AOI = True

# ----------Date Range----------
# Format: 'YYYY-MM-DD'
start_date = start_month+"-01"
end_date = start_month+'-15'

# ----------Cloud Filter----------
# Format: decimal (e.g., 50% max cloud cover = 0.5)
max_cloud_cover = 0.8

# ----------Item Type----------
# See here for possible image ("item") types:
# https://developers.planet.com/docs/apis/data/items-assets/
# item_type = "PSScene4Band" #OLD (now deprecated)
item_type = "PSScene"
asset_type = "ortho_analytic_4b_sr"

# ----------Planet API Key---------- MAKE THIS PRIVATE USING BOTO3?
# Find your API key on your Planet Account > My Settings > API Key

# ----------Output folder----------
# AKA, where you want your images to be downloaded in your directory
# out_folder = '/Volumes/SURGE_DISK/PS_downloads_SK/'


# ### Authentication via basic HTTP

# In[96]:


# set API key as environment variable
os.environ['PL_API_KEY'] = API_key

# Setup the API Key stored as the `PL_API_KEY` environment variable
PLANET_API_KEY = os.getenv('PL_API_KEY')

# Orders URL
orders_url = 'https://api.planet.com/compute/ops/orders/v2'

# Authorize
auth = HTTPBasicAuth(PLANET_API_KEY, '')
response = requests.get(orders_url, auth=auth)
response


# ### Compile filters and use Quick Search to grab image IDs

# In[97]:


# get images that overlap with our AOI 
geometry_filter = {
  "type": "GeometryFilter",
  "field_name": "geometry",
  "config": AOI_box
}

# get images acquired within a date range
date_range_filter = {
  "type": "DateRangeFilter",
  "field_name": "acquired",
  "config": {
    "gte": start_date + "T00:00:00.000Z",
    "lte": end_date + "T00:00:00.000Z"
  }
}

# only get images which have <50% cloud coverage
cloud_cover_filter = {
  "type": "RangeFilter",
  "field_name": "cloud_cover",
  "config": {
    "lte": max_cloud_cover
  }
}

# combine our geo, date, cloud filters
combined_filter = {
  "type": "AndFilter",
  "config": [geometry_filter, date_range_filter, cloud_cover_filter]
}

# define the clip tool
clip = {
    "clip": {
        "aoi": AOI_box
    }
}

# -----AOI clipping
# Determine whether to clip images to the AOI (True/False)
# This greatly speeds up the ordering and downloading process and decreases the usage of your imagery quota
clip_to_AOI = True

# -----Sentinel-2 Harmonization
# option to harmonize PlanetScope imagery to Sentinel-2
harmonize = True # = True to harmonize

# -----Create request
QS_request = orders.build_QS_request(AOI_box_shape, max_cloud_cover, start_date, end_date, item_type, asset_type)
        
# -----Planet API Quick Search using created request
# fire off the POST request
QS_result = \
  requests.post(
    'https://api.planet.com/data/v1/quick-search',
    auth=HTTPBasicAuth(PLANET_API_KEY, ''),
    json=QS_request)
# Print resulting image IDs
im_ids = [feature['id'] for feature in QS_result.json()['features']]
im_ids = sorted(im_ids)
print(len(im_ids),'images found')


# In[98]:


# only download images that don't already exist in directory
im_ids_filtered = []
for im_id in im_ids:
    num_exist = len(glob.glob(out_folder + im_id+'_SR_clip.tif'))
    if num_exist==0:
        im_ids_filtered = im_ids_filtered + [im_id]
print(str(len(im_ids_filtered)) + ' new images to be downloaded')


# ## Place order

# In[99]:


# -----Build new request
request = orders.build_request_itemIDs(AOI_box, clip_to_AOI, harmonize, im_ids_filtered, item_type, asset_type)

# -----Place order
if orders_url!="N/A":
    order_url = orders.place_order(orders_url, request, auth)


# ### Poll for Order Success
# - This section outputs the status of the order every ~10 sec. This will take a few minutes... 
# - Wait until it outputs `success` to proceed to the next section. It will stop after 30 loops, so try proceeding to the next section if it finishes running and does not output `success`.
# - If you are ordering a LOT of images, consider narrowing your date range to download less images at a time. 

# In[100]:


# -----Poll the order every 10s until it outputs "success," "failed," or "partial"
# Only continue to the next cell if outputs "success". Otherwise, try again or submit a new search request. 
orders.poll_for_success(order_url, auth)


# In[101]:


# -----View results
r = requests.get(order_url, auth=auth)
response = r.json()
results = response['_links']['results']
# print all files to be downloaded from order
[r['name'] for r in results]


# In[102]:


orders.download_results(results, out_folder)


# In[111]:


# # rename folder using month-day combination
# folderid = results[0]['name'].split('/')[0] # grab the folder id
# os.rename(out_folder+folderid, out_folder+start_date[:7]+'/')
# print('Image downloaded to',out_folder+start_date[:7]+'/')


# ----------Date Range----------
# Format: 'YYYY-MM-DD'
start_date = start_month+"-15"
end_date = end_month+'-01'

# ----------Cloud Filter----------
# Format: decimal (e.g., 50% max cloud cover = 0.5)
max_cloud_cover = 0.8

# ----------Item Type----------
# See here for possible image ("item") types:
# https://developers.planet.com/docs/apis/data/items-assets/
# item_type = "PSScene4Band" #OLD (now deprecated)
item_type = "PSScene"
asset_type = "ortho_analytic_4b_sr"

# ----------Planet API Key---------- MAKE THIS PRIVATE USING BOTO3?
# Find your API key on your Planet Account > My Settings > API Key
# API_key = 'c2e92a042f6744eba732c282d09539f8'

# ----------Output folder----------
# AKA, where you want your images to be downloaded in your directory
# out_folder = '/Volumes/SURGE_DISK/PS_downloads_SK/'


# ### Authentication via basic HTTP

# In[96]:


# set API key as environment variable
os.environ['PL_API_KEY'] = API_key

# Setup the API Key stored as the `PL_API_KEY` environment variable
PLANET_API_KEY = os.getenv('PL_API_KEY')

# Orders URL
orders_url = 'https://api.planet.com/compute/ops/orders/v2'

# Authorize
auth = HTTPBasicAuth(PLANET_API_KEY, '')
response = requests.get(orders_url, auth=auth)
response


# ### Compile filters and use Quick Search to grab image IDs

# In[97]:


# get images that overlap with our AOI 
geometry_filter = {
  "type": "GeometryFilter",
  "field_name": "geometry",
  "config": AOI_box
}

# get images acquired within a date range
date_range_filter = {
  "type": "DateRangeFilter",
  "field_name": "acquired",
  "config": {
    "gte": start_date + "T00:00:00.000Z",
    "lte": end_date + "T00:00:00.000Z"
  }
}

# only get images which have <50% cloud coverage
cloud_cover_filter = {
  "type": "RangeFilter",
  "field_name": "cloud_cover",
  "config": {
    "lte": max_cloud_cover
  }
}

# combine our geo, date, cloud filters
combined_filter = {
  "type": "AndFilter",
  "config": [geometry_filter, date_range_filter, cloud_cover_filter]
}

# define the clip tool
clip = {
    "clip": {
        "aoi": AOI_box
    }
}

# -----AOI clipping
# Determine whether to clip images to the AOI (True/False)
# This greatly speeds up the ordering and downloading process and decreases the usage of your imagery quota
clip_to_AOI = True

# -----Sentinel-2 Harmonization
# option to harmonize PlanetScope imagery to Sentinel-2
harmonize = True # = True to harmonize

# -----Create request
QS_request = orders.build_QS_request(AOI_box_shape, max_cloud_cover, start_date, end_date, item_type, asset_type)
        
# -----Planet API Quick Search using created request
# fire off the POST request
QS_result = \
  requests.post(
    'https://api.planet.com/data/v1/quick-search',
    auth=HTTPBasicAuth(PLANET_API_KEY, ''),
    json=QS_request)
# Print resulting image IDs
im_ids = [feature['id'] for feature in QS_result.json()['features']]
im_ids = sorted(im_ids)
print(len(im_ids),'images found')


# In[98]:


# only download images that don't already exist in directory
im_ids_filtered = []
for im_id in im_ids:
    num_exist = len(glob.glob(out_folder + im_id+'_SR_clip.tif'))
    if num_exist==0:
        im_ids_filtered = im_ids_filtered + [im_id]
print(str(len(im_ids_filtered)) + ' new images to be downloaded')


# ## Place order

# In[99]:


# -----Build new request
request = orders.build_request_itemIDs(AOI_box, clip_to_AOI, harmonize, im_ids_filtered, item_type, asset_type)

# -----Place order
if orders_url!="N/A":
    order_url = orders.place_order(orders_url, request, auth)


# ### Poll for Order Success
# - This section outputs the status of the order every ~10 sec. This will take a few minutes... 
# - Wait until it outputs `success` to proceed to the next section. It will stop after 30 loops, so try proceeding to the next section if it finishes running and does not output `success`.
# - If you are ordering a LOT of images, consider narrowing your date range to download less images at a time. 

# In[100]:


# -----Poll the order every 10s until it outputs "success," "failed," or "partial"
# Only continue to the next cell if outputs "success". Otherwise, try again or submit a new search request. 
orders.poll_for_success(order_url, auth)


# In[101]:


# -----View results
r = requests.get(order_url, auth=auth)
response = r.json()
results = response['_links']['results']
# print all files to be downloaded from order
[r['name'] for r in results]


# In[102]:


orders.download_results(results, out_folder)
# ## You did it!
# 
# <div>
# <img src="sandy-cheeks.jpeg" width="400"/>
# </div>
