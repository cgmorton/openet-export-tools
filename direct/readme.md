# Direct Download Export Tools (using Xee module)

### Xee module

Images are downloaded directly from Google Earth Engine using the Xee module (https://github.com/google/Xee) to read the images as numpy arrays, and the rasterio module (https://github.com/rasterio/rasterio) to save the numpy arrays as geotiffs.

The version of Xee that is currently available on PyPi (v0.0.24) has some major limitations that make it unusable for saving exact copies of GEE images.  There is a major refactor being done that is intended to be released as v0.1 that fixes most of the issues with Xee (https://github.com/google/Xee/pull/275).  It is not clear when this pull request will be merged and the updated version released, but until then the user will need to manually download or clone the pull request and install the updated version into their python environment.

### openet_monthly_image_direct_download.py

