#!/bin/bash
#####################################################################
# By Jukes Liu

# Run this bash script from the terminal with starting YYYY-MM,
# ending YYYY-MM (inclusive) of image download, path to AOI shapefile (WGS projection),
# path to AOI shapefile (UTM projection), path to the 5m raster,
# path to the glacier shapefile (UTM projection), the base download folder,
# and your planet API Key.
#
# E.g.:
#sh run_pipeline_monthly.sh 2021-06 2021-12 /Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/BoxTurner/BoxTurner_WGS.shp /Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/BoxTurner/BoxTurner_UTM_07.shp /Users/jukesliu/Documents/TURNER/DATA/VELOCITY_MAPS/forAutoRIFT/IfSAR_DSM_5m_cropped.tif /Users/jukesliu/Documents/TURNER/DATA/shapefiles_gis/main_ice_outline.shp /Volumes/SURGE_DISK/PS_downloads_SK/ c2e92a042f6744eba732c282d09539f8 /Volumes/SURGE_DISK/PS_downloads_SK/noncloudy_for_autorift/
#
# Last updated 2023 10 05
######################################################################

# terminus picking threshold
start_yyyy_mm=$1
end_yyyy_mm=$2
aoi_path_WGS=$3
aoi_path_UTM=$4
raster_5m_path=$5
glaciershp_path=$6
basefolder=$7
API_key=$8
final_outfolder=$9

echo "Downloading images into monthly folders from $start_yyyy_mm to $end_yyyy_mm"
echo "Using AOI polygon at $aoi_path_WGS and $aoi_path_UTM"
echo "Using 5m raster at $raster_5m_path"
echo "Using glacier polygon at $glaciershp_path"
echo "Using base download folder: $basefolder"
echo "Using API key: $API_key"

# Create list of start months and end months to run
start_yyyy=${start_yyyy_mm:0:4} # grab the starting year
start_mm=${start_yyyy_mm:5:6} # grab starting month
end_yyyy=${end_yyyy_mm:0:4} # grab the ending year
end_mm=${end_yyyy_mm:5:6} # grab starting month (inclusive)
#echo $start_yyyy $start_mm $end_yyyy $end_mm

if (($end_yyyy < $start_yyyy+0)); then # ending year less than starting year (error)
echo "Error: ending year needs to greater than or equal to the starting year"
elif (($end_yyyy == $start_yyyy)); then # ending year equal to starting year (ok)
    if (($end_mm < $start_mm)); then # ending month less than starting (error
    echo "Error: ending month needs to be equal to or greater than starting month"
    else # ending month greater than starting month in same year
    # CREATE YEAR,MONTH LIST ACCORDINGLY
    yyyymm_list=()
    mm=${start_mm#0}
    until (($mm == ${end_mm#0}+1)); do
        mm_str=$(printf "%02d" $mm) # two digit month string
        yyyymm_str=$start_yyyy"-"$mm_str # yyyy-mm
#        echo $yyyymm_str
        yyyymm_list=(${yyyymm_list[@]} $yyyymm_str) # add to list
        mm=$((mm+1)) # increment month
    done
    fi
else # ending year greater than starting year
    # CREATE YEAR, MONTH LIST ACCORDINGLY
    yyyymm_list=()
    
    # generate all months for first year
    mm=${start_mm#0}
    until (($mm == 13)); do
        mm_str=$(printf "%02d" $mm) # two digit month string
        yyyymm_str=$start_yyyy"-"$mm_str # yyyy-mm
#        echo $yyyymm_str
        yyyymm_list=(${yyyymm_list[@]} $yyyymm_str) # add to list
        mm=$((mm+1)) # increment month
    done
    
    # if there are years in between the first and the last
    # generate full 1-12 months for those
    if (($end_yyyy-$start_yyyy > 1)); then
        year=$((start_yyyy+1))
        until(($year == ${end_yyyy})); do
            mm=1
            until (($mm == 13)); do
                mm_str=$(printf "%02d" $mm) # two digit month string
                yyyymm_str=$year"-"$mm_str # yyyy-mm
                yyyymm_list=(${yyyymm_list[@]} $yyyymm_str) # add to list
                mm=$((mm+1)) # increment month
            done
            year=$((year+1))
        done
    fi

    # generate all months for last year
    mm=1
    until (($mm == ${end_mm#0}+1)); do
        mm_str=$(printf "%02d" $mm) # two digit month string
        yyyymm_str=$end_yyyy"-"$mm_str # yyyy-mm
#        echo $yyyymm_str
        yyyymm_list=(${yyyymm_list[@]} $yyyymm_str) # add to list
        mm=$((mm+1)) # increment month
    done
fi

echo ${yyyymm_list[@]}
month_count=${#yyyymm_list[@]}
echo "$month_count months of data"

for ((a=0; a < $month_count; a++)); do
    monthfolder=${yyyymm_list[$a]}
    echo "Processing all imagery for $monthfolder"

    # Calculate next month folder for image download
    month=${monthfolder:5:6}
    year=${monthfolder:0:4}
    month=${month#0}
    if (($((month+1)) == 13)); then
        # add 1 to year and set month to 01
        year=$((year+1))
        next_month=01
    else
        # otherwise, calculate next month normally
        next_month=$((month+1))
    fi
    next_month_folder=$year-$(printf "%02d" $next_month)
#    echo $next_month_folder

##    # download the imagery
    python3 planetAPI_image_download.py $monthfolder $next_month_folder $aoi_path_WGS $API_key $basefolder

    # standardize grid
    python3 standardize_grid.py $aoi_path_UTM $raster_5m_path $basefolder$monthfolder/PSScene/ $basefolder$monthfolder/PSScene/standard_grid/

    # gather stats (deletes raw imagery)
    python3 gather_stats.py $basefolder$monthfolder/

#    # OPTIONAL coregistration step
#    python3 coregister_images.py $basefolder$monthfolder/PSScene/standard_grid/ $glaciershp_path

    # stitch along-track satellite chunks together
    python3 stitch_by_sat.py $basefolder$monthfolder/PSScene/standard_grid/ $aoi_path_UTM

    # coregister satellite chunks
    python3 coregister_images.py $basefolder$monthfolder/PSScene/standard_grid/stitched_by_sat/ $glaciershp_path

    # stich satellite chunks for a single date
    python3 stitch_satchunks_by_date.py $basefolder$monthfolder/PSScene/standard_grid/ $glaciershp_path

    # crop and move final images
    python3 crop_move_finalimgs.py $glaciershp_path $aoi_path_UTM $basefolder$monthfolder/PSScene/standard_grid/stitched_images/ $final_outfolder
#
    #    # coregister all final images - can be saved until all batches are finished running
#    python3 coregister_images.py $basefolder$monthfolder/PSScene/standard_grid/stitched_images/ $glaciershp_path
    
done
echo "Finished running."
echo "Final images are placed in $final_outfolder"
