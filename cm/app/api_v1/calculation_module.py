# from osgeo import gdal
import io
import logging
import os
import pathlib
import secrets
import subprocess as sub
import tempfile
from pprint import pprint
from shutil import copyfile
from zipfile import ZipFile

import pandas as pd
import requests
from grass_session import TmpSession

from ..constant import CM_NAME
from ..helper import create_zip_shapefiles, generate_output_file_shp
from .heatsrc import technical as tech

# set a logger
LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
logging.basicConfig(format=LOG_FORMAT)
LOGGER = logging.getLogger(__name__)

WWTP = "WWTP"
WWTP_C = WWTP + "_capacity"
WWTP_P = WWTP + "_power"
CLC = "clc2018"
URB = "urbanareas"

BASEURL = "https://gitlab.com/hotmaps/potential/" "{repo}/-/raw/master/data/{filename}"

PARAMS = (("inline", "false"),)


COOKIES = {
    "__cfduid": "dbd0d275a4b34a54d96de0a86eb0c852a1593641560",
    "sidebar_collapsed": "false",
    "event_filter": "all",
    "_gitlab_session": "153f4bba604b81dd52df575e869a2969",
    "cf_clearance": "3399cada8eccda468f49a61ba8fa59a0f900bd6d-1596033647-0-1z93698c68z875df92cz197f3d1c-150",
    "known_sign_in": "aUp4SXNyVy9iZHZkU2MvRUdiUWhsditwcFRGSUFONWhpb1RkWFBtMmVlenJmM3V3Zm5vWWJCR1ROdG1BQVNYQmVzTVpDajdQRHJ6YllDaVBPL2tLRSt5MEFWUUFaU216M2lTRzg5QVJVeDlpODF0QitXNXRYSkh0eldFZ1AzelQtLUQ1Z0FLbnZXbkthNzVxMlF3STVjMWc9PQ%3D%3D--681814bf3633a4a9c26b71bedeb2e08bb62472a2",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it,en-US;q=0.7,en;q=0.3",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "TE": "Trailers",
}

URLS = {
    WWTP: dict(
        repo="WWTP",
        filename="WWTP_2015.csv",
        url=(
            "https://gitlab.com/hotmaps/potential/"
            "{repo}/-/raw/master/data/2015/{filename}"
        ),
        params=PARAMS,
        headers=HEADERS,
    ),
    WWTP
    + "csvt": dict(
        repo="WWTP",
        filename="WWTP_2015.csvt",
        url=(
            "https://gitlab.com/hotmaps/potential/"
            "{repo}/-/raw/master/data/2015/{filename}"
        ),
        params=PARAMS,
        headers=HEADERS,
    ),
    WWTP
    + "prj": dict(
        repo="WWTP",
        filename="WWTP_2015.prj",
        url=(
            "https://gitlab.com/hotmaps/potential/"
            "{repo}/-/raw/master/data/2015/{filename}"
        ),
        params=PARAMS,
        headers=HEADERS,
    ),
    CLC: dict(
        repo="corine_land_cover",
        filename="clc2018.tif",
        url="https://gitlab.com/hotmaps/corine_land_cover/-/raw/master/data/clc2018.tif",
        params=PARAMS,
        cookies=COOKIES,
        headers=HEADERS,
    ),
}


def read_csv(csvpath):
    try:
        return pd.read_csv(csvpath, header=0, index_col=0)
    except Exception as exc:
        LOGGER.exception(f"Failed to read: {csvpath} >> " f"exception = {exc}")
        raise exc


def get_data(repo, filename, url=BASEURL, **kwargs):
    """Retrieve/read agricultural residues data"""
    # TODO: once the dataset is integrated remove this function
    # check if the file exists and in case download
    filepath = pathlib.Path(tempfile.gettempdir(), filename)
    if not filepath.exists():
        url = url.format(repo=repo, filename=filename)
        print(f"Download {filepath} from: {url}")
        with requests.get(url, stream=True, **kwargs) as response:
            response.raise_for_status()

            with open(filepath, mode="wb") as cfile:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        cfile.write(chunk)
    return filepath


def extract_inidicators(wwtp_plants, indicators=None):
    indicators = indicators if indicators else []
    # verify result (here abbreviated)
    proc = tech.run_command(
        "v.db.select",
        map=wwtp_plants,
        stdout_=sub.PIPE,
        separator="pipe",
        vertical_separator="newline",
    )

    stdout = proc.outputs["stdout"].value
    # "indicators": [
    #     {"unit": "MWh","name": "Heat demand indicator with a factor divided by 2","value": 281244.5},
    # ],
    if stdout:
        res = pd.read_csv(io.StringIO(stdout), sep="|", header=0)
        for suit in res["suitability"].drop_duplicates():
            if str(suit).lower() != "nan":
                idx = res["suitability"] == suit
                pwr = res.loc[idx, "power"]
                indicators.append(
                    dict(
                        unit="kW",
                        name=f"{idx.sum()} heatsources classified as {suit}, total power",
                        value=f"{pwr.sum()}",
                    )
                )
    return indicators


def gen_zip(shpfile, fname, odir):
    print("shafefile", shpfile)
    odir = pathlib.Path(odir)
    shppath = shpfile[:-4]
    # copy all file in the output directory
    for ext in (".shp", ".dbf", ".prj", ".shx"):
        copyfile(shppath + ext, odir / (fname + ext))

    os.chdir(odir)
    # determine file name
    import sys

    # modify the coding in fly for writing
    sys.getfilesystemencoding = lambda: "UTF-8"

    zip_file = odir / (fname + ".zip")
    with ZipFile(zip_file, "w") as zf:
        for ext in (".shp", ".dbf", ".prj", ".shx"):
            zf.write(fname + ext)
        return zip_file


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

    # initialize the CM result
    result = dict()
    result["name"] = CM_NAME

    # validate the input parameters
    warnings = []
    near_dist, within_dist = int(params["near_dist"]), int(params["within_dist"])
    # check if the max within distance is < of max near distance or raise an issue
    if near_dist <= within_dist:
        warnings.append(
            {
                "unit": "-",
                "name": (
                    "near distance limit "
                    f"({near_dist}) <= within "
                    f"distance limit ({within_dist}),"
                    " please correct the values and try again"
                ),
                "value": "",
            }
        )

        result["indicator"] = warnings
        result["graphics"] = []
        result["vector_layers"] = []
        result["raster_layers"] = []
        print("result", result)
        return result

    print("=" * 50)
    print("=> inputs_raster_selection")
    pprint(inputs_raster_selection)
    print("=> inputs_vector_selection")
    pprint(inputs_vector_selection)
    # {'wwtp_capacity': '/var/tmp/e36e76f0b70b4b2e8fe974c593ebac93.csv'}
    try:
        cpth = inputs_vector_selection["wwtp_capacity"]
        proc = sub.Popen(f"head {cpth}", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
        so, se = proc.communicate()
        print(so.decode())
        print("---")
        print(se.decode())
        print("---")
    except Exception:
        print("Not able to reat the wwtp_capacity csv file")

    print("=> inputs_parameter_selection")
    pprint(inputs_parameter_selection)
    # get or download the missing datasets
    wwtp_c = inputs_vector_selection["wwtp_capacity"]
    wwtp_p = inputs_vector_selection["wwtp_power"]

    # download data from the repository
    # wwtprepo = get_data(**URLS[WWTP])
    wwtprepocsvt = get_data(**URLS[WWTP + "csvt"])
    wwtprepoprj = get_data(**URLS[WWTP + "prj"])
    clc = get_data(**URLS[CLC])

    # create the csvt and prj file to the input file provided by the platform
    # these files are requide to properly import the CSV considering the
    # common type and the Geographical coordination system
    # capacity
    wwpth_c = pathlib.Path(wwtp_c)
    wwfld_c = wwpth_c.parent
    wwnam_c = wwpth_c.name

    copyfile(wwtprepocsvt, wwfld_c / (wwnam_c[:-4] + ".csvt"))
    copyfile(wwtprepoprj, wwfld_c / (wwnam_c[:-4] + ".prj"))

    # power
    wwpth_p = pathlib.Path(wwtp_p)
    wwfld_p = wwpth_p.parent
    wwnam_p = wwpth_p.name

    copyfile(wwtprepocsvt, wwfld_p / (wwnam_p[:-4] + ".csvt"))
    copyfile(wwtprepoprj, wwfld_p / (wwnam_p[:-4] + ".prj"))

    # define the path to the default GRASS GIS working directory
    gisdb = pathlib.Path(tempfile.gettempdir(), "gisdb")
    location = "wwtp"

    overwrite = False
    rasters = {CLC: clc}
    vectors = {}  # {WWTP: wwtp}
    actions = [(tech.clc2urban, (CLC, URB, [111, 112, 121], overwrite))]

    if not gisdb.exists():
        # the directory do not exists and need to be created
        tech.create_location(
            gisdb,
            location,
            overwrite=overwrite,
            rasters=rasters,
            vectors=vectors,
            actions=actions,
        )

    # generate the shape file
    wwtp_out = generate_output_file_shp(output_directory)

    # create a new temporary mapset for computation and importing the wwtp points
    with TmpSession(
        gisdb=os.fspath(gisdb),
        location=location,
        mapset=f"mset_{secrets.token_urlsafe(8)}",
        create_opts="",
    ) as tmp:
        # import user inputs
        tech.run_command(
            "v.import", input=os.fspath(wwtp_c), output=WWTP_C, overwrite=overwrite
        )
        tech.run_command(
            "v.import", input=os.fspath(wwtp_p), output=WWTP_P, overwrite=overwrite
        )
        # create a copy
        tech.run_command("g.copy", vector=(WWTP_C, WWTP), overwrite=overwrite)
        # join the table
        tech.run_command(
            "v.db.join",
            map=WWTP,
            column="gid",
            other_table=WWTP_P,
            other_column="gid",
            subset_columns="power",
        )

        # compute the tech potential
        try:
            tech.tech_potential(
                wwtp_plants=WWTP,
                urban_areas=URB,
                dist_min=int(params["within_dist"]),
                dist_max=int(params["near_dist"]),
                capacity_col="capacity",
                power_col="power",
                suitability_col="suitability",
                dist_col="distance_label",
                plansize_col="plantsize_label",
                conditional_col="conditional",
                suitable_col="suitable",
                overwrite=overwrite,
            )
        except Exception as exc:
            print(f"Issue in mapset: {tmp._kwopen['mapset']}")
            raise exc

        # extract indicators
        indicators = extract_inidicators(WWTP, warnings)

        # export result
        tech.tech_export(wwtp_plants=WWTP, wwtp_out=wwtp_out, buffer=1.0)
        # copy the output back to the repository to have a cache
        print(
            f"\n\n=> Compute the heatsource potential using: {within_dist} and {near_dist} m. Done!"
        )
        wwtp_zip = create_zip_shapefiles(output_directory, wwtp_out)
        print(f"{output_directory} => {wwtp_out} => {wwtp_zip}")
    
    zip = ZipFile(wwtp_zip)
    # available files in the container
    print("shapefile name: ", wwtp_out)
    print("########## files in zip file")
    print(zip.namelist())
    size = sum([zinfo.file_size for zinfo in  wwtp_zip.filelist])
    zip_kb = float(size)/1000 #kB
    print("#################", zip_kb)
                  
    result = dict()
    result["name"] = CM_NAME
    result["indicator"] = indicators
    result["graphics"] = []
    result["vector_layers"] = [
        {
            "name": "Heatsource potential",
            "path": wwtp_zip,
        },
    ]
    '''
    # result["vector_layers"] = [
        # {
            # "name": "Heatsource potential",
            # "path": wwtp_zip,  # os.path.join(output_directory, wwtp_zip),
            # "type": "custom",
            # "symbology": [
                # {
                    # "red": 24,
                    # "green": 139,
                    # "blue": 125,
                    # "opacity": 0.8,
                    # "value": "Suitable",
                    # "label": "Suitable",
                # },
                # {
                    # "red": 217,
                    # "green": 194,
                    # "blue": 89,
                    # "opacity": 0.8,
                    # "value": "Conditionally",
                    # "label": "Conditionally",
                # },
                # {
                    # "red": 243,
                    # "green": 70,
                    # "blue": 22,
                    # "opacity": 0.8,
                    # "value": "Not suitable",
                    # "label": "Not suitable",
                # },
            # ],
        # },
    # ]
    '''
    result["raster_layers"] = []
    print("result", result)
    return result
