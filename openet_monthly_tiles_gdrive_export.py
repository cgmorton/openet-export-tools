import argparse
from datetime import datetime, timedelta
import logging
import math
import pprint
import re

from dateutil.relativedelta import relativedelta
import ee

# Override the default logging level for these modules that can be verbose
# logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('earthengine-api').setLevel(logging.INFO)
logging.getLogger('googleapiclient').setLevel(logging.INFO)
logging.getLogger('requests').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)


# Hardcoding the study area collection ID
study_area_coll_id = 'projects/swrcb-return-flows/assets/Scheduling/DUs/All_Central_Valley_DUs'


def main(
        model_name,
        reference_et,
        project_id,
        start_date,
        end_date,
        # extent=None,
        drive_folder='',
        mgrs_tiles=None,
        timestep='monthly',
        coll_version='v2_1',
):
    """Export OpenET Monthly Tiles to Google Drive

    Parameters
    ----------
    model_name : {'ensemble', 'disalexi', 'eemetric', 'geesebal', 'ptjpl', 'sims', 'ssebop'}
        OpenET model name.
    reference_et : {'gridmet', 'cimis'}
        Reference ET dataset keyword.
    project_id : str
        Google cloud project ID.
    start_date
        Inclusive end date in ISO date format (YYYY-MM-DD).
    end_date : str
        Exclusive end date in ISO date format (YYYY-MM-DD).
    drive_folder : str
        Images can be saved to a subfolder in your Google Drive,
        but this may cause problems with duplicate folders, so the default is
        to write to the root folder.
    mgrs_tiles : list
        List of specific MGRS grid zones to process.  The default is to process
        all MGRS grid zones that intersect the study area collection.
    timestep : {'monthly'}
        Only monthly time steps are currently supported
    coll_version : {'v2_1', 'v2_0'}
        OpenET collection version number
    """

    # Other input parameters
    # These may be made input function parameters in the future
    clip_study_area_flag = False

    # File naming format (e.g. "ensemble_gridmet_monthly_20260201_10S.tif")
    tif_name_fmt = f'{model_name}_{reference_et}_{timestep}_{{date}}_{{mgrs}}.tif'

    # Output datatype choices are "int16", "uint16", "float", "double"
    # Monthly images are stored as uint16 internally
    # Exporting as float prevents nodata and masking issues
    #   but does result in larger files
    output_dtype = 'float'
    # output_dtype = 'uint16'

    # Assume a default cellsize/scale of 30m for now
    cellsize = 30

    # Hardcoding the variable to the ET band for now
    if model_name.lower() == 'ensemble':
        variables = ['et_ensemble_mad']
    else:
        variables = ['et']

    # # A mask can be applied to the export images
    # # Mask must have values of 1 for pixels that are to be kept
    # # data_mask = ee.Image('projects/openet/assets/meteorology/cimis/ancillary/mask_epsg3310')
    # data_mask = None

    ########

    logging.info(f'\nExport monthly {model_name} images to bucket')
    logging.info(f'  {start_date.strftime("%Y-%m-%d")}')
    logging.info(f'  {end_date.strftime("%Y-%m-%d")}')

    ########

    # Initialize Earth Engine
    ee.Initialize(project=project_id)

    ########

    # Build a dictionary of the parameters that can be passed to the export call
    # Additional parameters will be included below
    export_params = {
        'maxPixels': int(1E12),
        'fileDimensions': 65536,  # 2**16
        'formatOptions': {
            'cloudOptimized': True,
            # 'skipEmptyTiles': True,
        },
    }

    # # TODO: Add support/checking for other projections
    # # Parse the input spatial reference parameter
    # if crs.upper() in ['EPSG:4326']:
    #     export_params['crs'] = crs
    #     # export_params['epsg'] = crs
    #     export_params['scale'] = cellsize
    # elif crs.upper() == 'EPSG:3310':
    #     # Passing EPSG:3310 as the crs wasn't working, so pulling wkt from a CIMIS like image
    #     export_params['crs'] = ee.Image('projects/openet/assets/meteorology/cimis/ancillary/mask').projection().wkt()
    #     # export_params['epsg'] = 'EPSG:3310'
    # elif re.match('EPSG:326\d{2}', crs.upper()):
    #     export_params['crs'] = crs
    #     # export_params['epsg'] = crs
    # else:
    #     raise ValueError(f'unsupported crs parameter: {crs}')

    ########

    # Compute the export extent from the study area feature collection subset
    study_area_coll = ee.FeatureCollection(study_area_coll_id)
    # # TODO: Add support for filtering the study area collection
    # if study_area_property and study_area_features:
    #     study_area_coll = (
    #         study_area_coll
    #         .filter(ee.Filter.inList(study_area_property, study_area_features)
    #     )
    study_area_geom = study_area_coll.geometry()

    # study_area_bounds = study_area_geom.bounds(maxError=1, proj=crs).coordinates().get(0).getInfo()
    # study_area_extent = [
    #     min([round(x[0], 6) for x in study_area_bounds]),
    #     min([round(x[1], 6) for x in study_area_bounds]),
    #     max([round(x[0], 6) for x in study_area_bounds]),
    #     max([round(x[1], 6) for x in study_area_bounds]),
    # ]
    # logging.debug(f'\nStudy Area Extent: {study_area_extent}')

    # # If the output projection is a Landsat default project (EPSG:32610, EPSG:32611, etc.)
    # #   adjust the extent and transform to be snapped to the Landsat "grid"
    # # TODO: This should probably be controlled based on a function parameter
    # #   of either a boolean or snap points
    # if crs in ['EPSG:326{:02d}'.format(utm) for utm in range(1, 61)]:
    #     snap_x, snap_y = 15, 15
    # else:
    #     snap_x, snap_y = 0, 0
    #
    # if crs in ['EPSG:4326']:
    #     # Buffer extents out to the 3rd decimal place
    #     cs = 0.001
    # else:
    #     # Include 10 extra buffer cells when adjusting the extent
    #     cs = cellsize * 10
    #
    # export_extent = [
    #     int(math.floor((study_area_extent[0] - snap_x) / cs)) * cs + snap_x,
    #     int(math.floor((study_area_extent[1] - snap_y) / cs)) * cs + snap_y,
    #     int(math.ceil((study_area_extent[2] - snap_x) / cs)) * cs + snap_x,
    #     int(math.ceil((study_area_extent[3] - snap_y) / cs)) * cs + snap_y,
    # ]
    # logging.debug(f'Export Extent: {export_extent}')
    # input('ENTER')

    ########

    # # Set the export pixel grid parameters
    # if crs in ['EPSG:4326']:
    #     export_params['crs'] = 'EPSG:4326'
    #     export_params['scale'] = cellsize
    #     export_params['region'] = ee.Geometry.Rectangle(export_extent, proj=crs, geodesic=False)
    # else:
    #     # Compute the export geo transform and shape
    #     crs_transform = [cellsize, 0, export_extent[0], 0, -cellsize, export_extent[3]]
    #     shape_2d = [
    #         abs(int((export_extent[2] - export_extent[0]) / cellsize)),
    #         abs(int((export_extent[3] - export_extent[1]) / cellsize))
    #     ]
    #     logging.debug(f'\nExtent:    {export_extent}')
    #     logging.debug(f'Transform: {crs_transform}')
    #     logging.debug(f'Shape:     {shape_2d}\n')
    #
    #     export_params['dimensions'] = '{0}x{1}'.format(*shape_2d)
    #     export_params['crsTransform'] = '[' + ','.join(map(str, crs_transform)) + ']'

    # Nodata values are a function of the output datatype
    nodata_values = {
        'float': -9999,
        'double': -9999,
        'int16': -32768,
        'uint16': 65535,
    }
    export_params['formatOptions']['noData'] = nodata_values[output_dtype]

    # Clamp integer values to the following range
    if output_dtype == 'uint16':
        dtype_min = 0
        dtype_max = 65534
    elif output_dtype == 'int16':
        dtype_min = -32767
        dtype_max = 32767
    else:
        dtype_min = None
        dtype_max = None

    # Build the collection ID
    if reference_et.lower() == 'gridmet':
        region = 'conus/gridmet'
    elif reference_et.lower() == 'cimis':
        region = 'california/cimis'
    else:
        raise ValueError(f'Unsupported reference ET dataset: {reference_et}')

    # 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1'
    month_coll_id = (
        f'projects/openet/assets/{model_name.lower()}/'
        f'{region.lower()}/{timestep.lower()}/{coll_version.lower()}'
    )

    # Build the date ranges to process
    iter_dates = [
        datetime(y, m, 1)
        for y in range(start_date.year, end_date.year + 2)
        for m in range(1, 13)
        if datetime(y, m, 1) >= start_date
    ]
    iter_dates = [
        [dt.strftime('%Y-%m-%d'), (iter_dates[i + 1] - timedelta(days=1)).strftime('%Y-%m-%d')]
        for i, dt in enumerate(iter_dates[:-1])
        if (iter_dates[i + 1] - timedelta(days=1)) <= end_date
    ]

    # Export the images
    for iter_start_date, iter_end_date in iter_dates:
        logging.info(f'{iter_start_date} {iter_end_date}')

        # Build date strings for filterDate calls
        iter_start_dt = datetime.strptime(iter_start_date, '%Y-%m-%d')
        iter_end_dt = datetime.strptime(iter_end_date, '%Y-%m-%d')

        # Make end date exclusive for filterDate() and the days count
        exclusive_end_dt = iter_end_dt + timedelta(days=1)
        exclusive_end_date = exclusive_end_dt.strftime('%Y-%m-%d')
        # logging.debug(f'  {iter_start_dt.strftime("%Y-%m-%d")}')
        # logging.debug(f'  {exclusive_end_date}')

        # Build the source image collection
        month_coll = (
            ee.ImageCollection(month_coll_id)
            .filterDate(iter_start_dt, exclusive_end_date)
        )

        if study_area_geom:
            month_coll = month_coll.filterBounds(study_area_geom)

        # Limit the collection to the MGRS tile list if it is set
        if mgrs_tiles:
            month_coll = month_coll.filter(ee.Filter.inList('mgrs_tile', mgrs_tiles))

        if month_coll.size().getInfo() == 0:
            logging.info('  No model images available, skipping')
            continue

        # Get the list of available tiles
        month_image_list = month_coll.aggregate_array('system:index').getInfo()

        # Process each MGRS grid zone image
        for month_img_id in month_image_list:
            logging.info(f'  {month_img_id}')

            output_img = ee.Image(f'{month_coll_id}/{month_img_id}').select(variables)
            img_info = output_img.getInfo()
            mgrs_tile = img_info['properties']['mgrs_tile']
            utm_zone = int(mgrs_tile[:2])
            # transform = img_info['bands'][0]['crs_transform']
            # dimensions = img_info['bands'][0]['dimensions']

            # Build the export file name and description
            export_tif = tif_name_fmt.format(
                date=iter_start_dt.strftime('%Y%m%d'), mgrs=mgrs_tile,
            )
            description = export_tif.replace('.tif', '').replace('/', '_') + '_gdrive_export'
            logging.debug(f'  {export_tif}')
            logging.debug(f'  {description}')

            # Set the export parameters for each tile image
            export_params['crs'] = f'EPSG:326{utm_zone}'
            export_params['crsTransform'] = img_info['bands'][0]['crs_transform']
            export_params['dimensions'] = img_info['bands'][0]['dimensions']

            # Round to the nearest integer for integer dtypes
            if output_dtype in ['int16', 'uint16']:
                output_img = output_img.round().clamp(dtype_min, dtype_max)

            # Cast to the target datatype
            output_img = output_img.cast({v: output_dtype for v in variables})

            if clip_study_area_flag:
                output_img = output_img.clip(study_area_geom)

            # # Apply a mask to the output image
            # if data_mask:
            #     output_img = output_img.updateMask(data_mask)

            # Unmask to set the nodata value for the COG export
            output_img = output_img.unmask(nodata_values[output_dtype])

            logging.info('  Starting export task')
            task = ee.batch.Export.image.toDrive(
                image=output_img,
                description=description,
                folder=drive_folder,
                fileNamePrefix=export_tif.replace('.tif', ''),
                **export_params,
            )
            task.start()

    logging.info('\nDone')


# TODO: Move to a utils module or read from openet-core
def arg_valid_date(input_date):
    """Check that a date string is ISO format (YYYY-MM-DD)

    This function is used to check the format of dates entered as command
      line arguments.
    DEADBEEF - It would probably make more sense to have this function
      parse the date using dateutil parser (http://labix.org/python-dateutil)
      and return the ISO format string

    Parameters
    ----------
    input_date : string

    Returns
    -------
    datetime

    Raises
    ------
    ArgParse ArgumentTypeError

    """
    try:
        return datetime.strptime(input_date, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{}'.".format(input_date)
        raise argparse.ArgumentTypeError(msg)


def arg_parse():
    """"""
    today = datetime.today()

    # start_month_offset = 2
    start_month_offset = 1
    end_month_offset = 0

    parser = argparse.ArgumentParser(
        description='Export OpenET Monthly Assets to Google Drive',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--model', required=True,
        choices=['ensemble', 'disalexi', 'eemetric', 'geesebal', 'ptjpl', 'sims', 'ssebop'],
        help='OpenET model')
    parser.add_argument(
        '--reference', choices=['cimis', 'gridmet'],
        help='Reference ET source dataset')
    parser.add_argument(
        '--project', required=True, default=None,
        help='Google cloud project ID to use for GEE authentication')
    parser.add_argument(
        '--start', type=arg_valid_date, metavar='DATE',
        default=(datetime(today.year, today.month, 1) -
                 relativedelta(months=start_month_offset)).strftime('%Y-%m-%d'),
        help='Start date (format YYYY-MM-DD)')
    parser.add_argument(
        '--end', type=arg_valid_date, metavar='DATE',
        default=(datetime(today.year, today.month, 1) -
                 relativedelta(months=end_month_offset)).strftime('%Y-%m-%d'),
        help='End date (format YYYY-MM-DD)')
    # # CGM - Extent parameter is not yet supported
    # parser.add_argument(
    #     '--extent', default=None, nargs='+', metavar='xmin ymin xmax ymax',
    #     help='Bounding extent')
    parser.add_argument(
        '--folder', default='', help='Drive folder')
    parser.add_argument(
        '--mgrs', default=[], nargs='+',
        help='Space separated list of MGRS grid zone tiles')
    parser.add_argument(
        '--version', default='v2_1', choices=['v2_1', 'v2_0'],
        help='OpenET Collection version')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = arg_parse()
    logging.basicConfig(level=args.loglevel, format='%(message)s')

    main(
        model_name=args.model,
        reference_et=args.reference,
        project_id=args.project,
        start_date=args.start,
        end_date=args.end,
        drive_folder=args.folder,
        # CGM - Extent parameter is not yet supported
        # extent=args.extent,
        mgrs_tiles=args.mgrs,
        coll_version=args.version,
        # study_area_coll_id=args.study,
    )

