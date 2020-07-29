# from osgeo import gdal

# from ..helper import generate_output_file_tif, create_zip_shapefiles
from ..constant import CM_NAME

# from .heatsrc import technical as tech
# import time

""" Entry point of the calculation module function"""

# TODO: CM provider must "change this code"
# TODO: CM provider must "not change input_raster_selection,output_raster  1 raster input => 1 raster output"
# TODO: CM provider can "add all the parameters he needs to run his CM
# TODO: CM provider can "return as many indicators as he wants"
def calculation(
    output_directory,
    inputs_raster_selection,
    inputs_vector_selection,
    inputs_parameter_selection,
):
    params = inputs_parameter_selection
    # validate the input parameters
    warnings = []
    # check if the max within distance is < of max near distance or raise an issue
    if params["near_dist"] <= params["within_dist"]:
        warnings.append(
            {
                "unit": "-",
                "name": (
                    "near distance limit "
                    f"({params['near_dist']}) <= within "
                    f"distance limit ({params['within_dist']}),"
                    " please correct the values and try again"
                ),
                "value": "",
            }
        )

    # TODO: check if the grass location has been already created
    # if is missing, then:
    # 1. download the CLC data,
    # 2. create a GRASS GIS location,
    # 3. import the data into PERMANENT
    # 4. create the urban areas map

    # TODO: do the computation
    # tech.tech_potential(
    #     wwtp_plants: str,
    #     urban_areas: str,
    #     dist_min: int = 150,
    #     dist_max: int = 1000,
    #     capacity_col: str = "capacity",
    #     power_col: str = "power",
    #     suitability_col: str = "suitability",
    #     dist_col: str = "distance_label",
    #     plansize_col: str = "plantsize_label",
    #     conditional_col: str = "conditional",
    #     suitable_col: str = "suitable",
    #     overwrite: bool = False,
    # )

    # # generate the output raster file
    # output_raster1 = generate_output_file_tif(output_directory)

    # #retrieve the inputs layes
    # input_raster_selection =  inputs_raster_selection["heat"]

    # #retrieve the inputs layes
    # input_vector_selection =  inputs_vector_selection["heating_technologies_eu28"]

    # #retrieve the inputs all input defined in the signature
    # factor =  float(inputs_parameter_selection["multiplication_factor"])

    # # TODO this part bellow must be change by the CM provider
    # ds = gdal.Open(input_raster_selection)
    # ds_band = ds.GetRasterBand(1)

    # #----------------------------------------------------
    # pixel_values = ds.ReadAsArray()
    # #----------Reduction factor----------------

    # pixel_values_modified = pixel_values* float(factor)
    # hdm_sum  = float(pixel_values_modified.sum())/1000

    # gtiff_driver = gdal.GetDriverByName('GTiff')
    # #print ()
    # out_ds = gtiff_driver.Create(output_raster1, ds_band.XSize, ds_band.YSize, 1, gdal.GDT_UInt16, ['compress=DEFLATE',
    #                                                                                                      'TILED=YES',
    #                                                                                                      'TFW=YES',
    #                                                                                                      'ZLEVEL=9',
    #                                                                                                      'PREDICTOR=1'])
    # out_ds.SetProjection(ds.GetProjection())
    # out_ds.SetGeoTransform(ds.GetGeoTransform())

    # ct = gdal.ColorTable()
    # ct.SetColorEntry(0, (0,0,0,255))
    # ct.SetColorEntry(1, (110,220,110,255))
    # out_ds.GetRasterBand(1).SetColorTable(ct)

    # out_ds_band = out_ds.GetRasterBand(1)
    # out_ds_band.SetNoDataValue(0)
    # out_ds_band.WriteArray(pixel_values_modified)

    # del out_ds
    # output geneneration of the output

    # TODO to create zip from shapefile use create_zip_shapefiles from the helper before sending result
    # TODO exemple  output_shpapefile_zipped = create_zip_shapefiles(output_directory, output_shpapefile)
    result = dict()
    result["name"] = CM_NAME
    result["indicator"] = warnings
    result["graphics"] = []
    result["vector_layers"] = []
    result["raster_layers"] = []
    print("result", result)
    return result


def colorizeMyOutputRaster(out_ds):
    ct = gdal.ColorTable()
    ct.SetColorEntry(0, (0, 0, 0, 255))
    ct.SetColorEntry(1, (110, 220, 110, 255))
    out_ds.SetColorTable(ct)
    return out_ds
