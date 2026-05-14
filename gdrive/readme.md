# Google Drive Export Tools

### openet_monthly_image_gdrive_export.py

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

### openet_monthly_tiles_gdrive_export.py

This tool is similar to the composite tool except that separate exports are made for each tile that intersects the study area.
