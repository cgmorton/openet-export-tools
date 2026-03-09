# OpenET Export Tools

### Provisional Data

Note that images for the last three full months should be considered "early" or very provisional, and will be regenerated and updated a number of times over the first three months.  These updates are done to incorporate additional Landsat 8 images that may have a 2-3 week lag, to incorporate final GRIDMET meteorology and reference ET data that has ~60 day lag, and to account for the +/- 32 day window that is used for linear interpolation.   

Additionally, all images for the previous full year should also be considered "provisional" and will be updated without warning or notification as additional crop type information becomes available.

### OpenET Image Tiling Scheme

The OpenET monthly images are stored in tiles defined by MGRS Grid Zones.

https://upload.wikimedia.org/wikipedia/commons/b/b7/Universal_Transverse_Mercator_zones.svg

For example, the OpenET images for California are in the MGRS grid zones: 10S, 10T, 11S.

### Python Command Line Interface (CLI) Tools

# openet_monthly_image_gdrive_export.py

This tool can be used to export a single OpenET monthly image that is a composite (or merge) of all available tiles.

Note, composite exports will use considerable EECU since OpenET tiles are stored in different projections and end up needing to be reprojected to the target projections.

Example call to export a single ensemble monthly image for February 2026 for the study area.  Note that study area collection is currently hardcoded in the script.  You will need to set your Google Cloud Project ID for initializing Earth Engine.  In this example the output coordinate reference system (crs) is set to the California Albers projection used by Spatial CIMIS (https://epsg.io/3310).

```
python openet_monthly_image_gdrive_export.py --model ensemble --reference gridmet --start 2026-02-01 --end 2026-02-28 --project YOURPROJECTID --epsg 3310
```

Another example call, but this time with the output CRS set to the common "EPSG 4326" (https://epsg.io/4326) that is used by the OpenET API (I think).

```
python openet_monthly_image_gdrive_export.py --model ensemble --reference gridmet --start 2026-02-01 --end 2026-02-28 --project YOURPROJECTID --epsg 4326
```

Another example call but this time with "mgrs" parameter set to limit the exports to the MGRS grid zones that intersect the Central Valley of California.

```
python openet_monthly_image_gdrive_export.py --model ensemble --reference gridmet --start 2026-02-01 --end 2026-02-28 --project YOURPROJECTID --epsg 3310 --mgrs 10S 11S
```

# openet_monthly_tiles_gdrive_export.py

This tool is similar to the composite tool except that separate exports are made for each tile that intersects the study area.
