#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute WWTP technical potential
==================================


"""
import math
import os
import secrets
import shutil
from typing import Any, Dict, List

import pandas as pd

from grass_session import Session  # isort:skip

from grass.pygrass.modules import Module
from grass.script import core as gcore
from grass.script import mapcalc


# Define constants values
RADIUS = [150, 1000]

DIST_DICT = {"Within": [">0", ">=25"], "Near": ["=0", ">=25"], "Far": ["< 25 ", "< 25"]}

PLANT_SIZE = {
    "Small": [2000, 5000],
    "Medium-small": [5001, 50000],
    "Medium-high": [50001, 150000],
    "High": [150000, None],
}

DATA_MATRIX = [
    ["Conditionally", "Conditionally", "Not suitable"],
    ["Suitable", "Conditionally", "Conditionally"],
    ["Suitable", "Suitable", "Conditionally"],
    ["Suitable", "Suitable", "Suitable"],
]

SUSTAINABILITY = pd.DataFrame(
    data=DATA_MATRIX,
    index=["Small", "Medium-small", "Medium-high", "High"],
    columns=["Within", "Near", "Far"],
)

COLORS = {"Suitable": "#188B7D", "Conditionally": "#D9C259", "Not suitable": "#F34616"}


## DATA NAMES
CLC = "clc"
URB = "urbanareas"
WWTP = "wwtp"


def run_command(*args, **kwargs):
    """Wrap pygrass.Module.run method to log commands"""
    kwargs["run_"] = False
    kwargs["quiet"] = True
    mod = Module(*args, **kwargs)
    # print(f"\n» Execute: `{' '.join(mod.make_cmd())}`")
    mod.run()
    return mod


def load_rasters(rasters: Dict[str, str], overwrite: bool = False):
    """
    Load raster in the mapset and update the dictionary with input a new name
    Args:
        dic_raster: a dictionary with key the name of the file and
                    value the path
    Return:
        data: update the dictionary with the new name in the grass mapset
    """
    for rname, raster in rasters.items():
        print(f"» Importing: {rname} from {raster}")
        run_command(
            "r.import", input=os.fspath(raster), output=rname, overwrite=overwrite
        )
        print(f"» {rname} imported!")


def load_vectors(vectors: Dict[str, str], overwrite: bool = False):
    """
    Load raster in the mapset and update the dictionary with input a new name
    Args:
        dic_raster: a dictionary with key the name of the file and
                    value the path
    Return:
        data: update the dictionary with the new name in the grass mapset
    """
    for vname, vector in vectors.items():
        print(f"» Importing: {vname} from {vector}")
        run_command(
            "v.import", input=os.fspath(vector), output=vname, overwrite=overwrite
        )
        print(f"» {vname} imported!")


def buffer(
    points: str,
    distance: int,
    buffpoints: str,
    urban_areas: str,
    overwrite: bool = False,
):
    run_command(
        "v.buffer",
        input=points,
        output=buffpoints,
        distance=distance,
        flags="t",
        overwrite=overwrite,
    )
    col = f"dist{distance:d}m"
    run_command(
        "v.rast.stats",
        map=buffpoints,
        raster=urban_areas,
        column_prefix=col,
        method="sum",
    )
    # set NULL to 0
    run_command(
        "db.execute",
        sql=(f"UPDATE {buffpoints} SET    {col}_sum = 0 WHERE  {col}_sum IS NULL"),
    )
    # join buffer layer with the original layer
    run_command(
        "v.db.join",
        map=points,
        column="cat",
        other_table=buffpoints,
        other_column="cat",
        subset_columns=col + "_sum",
    )


def clc2urban(clc: str, urbanareas: str, cats: List[int], overwrite: bool = False):
    """
    111: 230,  0, 77,255, Continuous_urban_fabric
    112: 255,  0,  0,255, Discontinuous_urban_fabric
    121: 204, 77,242,255, Industrial_or_commercial_units

    Parameters
    ----------
    clc : str
        DESCRIPTION.
    urbanareas : str
        DESCRIPTION.
    overwrite : bool, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    None.

    """
    print(f"» Reclass {clc} into {urbanareas} aggregating: {cats}")
    run_command(
        "r.reclass",
        input=clc,
        output=urbanareas,
        rules="-",
        title=(
            "Urban Areas from Corine Land Cover "
            f"({', '.join([str(cat) for cat in cats])})"
        ),
        stdin_=(
            f"{' '.join([str(cat) for cat in cats])}    = 1 "
            "urban areas\n*           = NULL"
        ),
    )


def tech_potential(
    wwtp_plants: str,
    urban_areas: str,
    dist_min: int = 150,
    dist_max: int = 1000,
    capacity_col: str = "capacity",
    power_col: str = "power",
    suitability_col: str = "suitability",
    dist_col: str = "distance_label",
    plansize_col: str = "plantsize_label",
    conditional_col: str = "conditional",
    suitable_col: str = "suitable",
    overwrite: bool = False,
):
    # set computational region to the raster used as input
    run_command("g.region", align=urban_areas, vector=wwtp_plants, flags="p")
    run_command("g.region", grow=100, flags="p")
    # create pid for tmp files
    for distance in (dist_min, dist_max):
        print(f"\n\n» Compute buffer around WWTP of {distance}")
        buffer(
            points=wwtp_plants,
            distance=int(distance),
            buffpoints=f"{wwtp_plants}__buf{distance}m",
            urban_areas=urban_areas,
            overwrite=overwrite,
        )

    # add columns
    cols = [
        (f"{suitability_col}", "varchar(16)"),
        (f"{dist_col}", "varchar(16)"),
        (f"{plansize_col}", "varchar(16)"),
        (f"{conditional_col}", "DOUBLE PRECISION"),
        (f"{suitable_col}", "DOUBLE PRECISION"),
        # add columns for output rendering
        ("color", "varchar(16)"),
        ("fillColor", "varchar(16)"),
        ("opacity", "DOUBLE PRECISION"),
    ]

    run_command(
        "v.db.addcolumn",
        map=wwtp_plants,
        columns=",".join(f"{cname} {ctype}" for cname, ctype in cols),
    )

    # run_command("db.describe", flags="c", table=wwtp_plants)
    # run_command("db.describe", flags="c", table=f"{wwtp_plants}__buf{dist_min}m")
    # run_command("db.describe", flags="c", table=f"{wwtp_plants}__buf{dist_max}m")

    print("\n\n» Update WWTP columns")
    for (dlabel, clabel), sustain in SUSTAINABILITY.unstack().items():
        dmin, dmax = DIST_DICT[dlabel]
        cmin, cmax = PLANT_SIZE[clabel]
        if cmax:
            cond_cap = (
                f"( {capacity_col} >  {cmin}\n"
                f"           AND {capacity_col} <= {cmax} )\n"
            )
        else:
            cond_cap = f"( {capacity_col} >  {cmin} )\n"
        where = (
            f"( {cond_cap}"
            f"         AND ( dist{dist_min:d}m_sum {dmin}\n"
            f"               AND dist{dist_max:d}m_sum {dmax} ) )"
        )

        clr = COLORS[sustain]
        sqlcmd = (
            f"UPDATE {wwtp_plants}\n"
            f"SET    {suitability_col}='{sustain}',\n"
            f"       {dist_col}='{dlabel}',\n"
            f"       {plansize_col}='{clabel}',\n"
            f"       color='{clr}',\n"
            f"       fillColor='{clr}',\n"
            f"       opacity=0.8\n"
            f"WHERE  {where}"
        )
        run_command("db.execute", sql=sqlcmd)

    run_command(
        "db.execute",
        sql=(
            f"UPDATE {wwtp_plants} "
            f"SET    {conditional_col} = CASE"
            f"          WHEN {suitability_col} = 'Conditional' THEN {power_col}"
            f"          ELSE 0 END"
        ),
    )

    run_command(
        "db.execute",
        sql=(
            f"UPDATE {wwtp_plants} "
            f"SET    {suitable_col} = CASE"
            f"         WHEN {suitability_col} = 'Suitable' THEN {power_col}"
            f"         ELSE 0 END;"
        ),
    )


def tech_stats(wwtp_plants: str, areas: str, columns: List[str]):
    # run_command(
    #     "v.vect.stats",
    #     points=wwtp_plants,
    #     areas=nuts3,
    #     method=sum,
    #     points_column=yes,
    #     count_column=yes_count,
    #     stats_column=yes_sum,
    # )

    # run_command(
    #     "v.vect.stats",
    #     points=wwtp_plants,
    #     areas=nuts3,
    #     method=sum,
    #     points_column=conditional,
    #     count_column=conditional_count,
    #     stats_column=conditional_sum,
    # )
    pass


def tech_export(wwtp_plants: str, wwtp_out: str, buffer: float = 1.0):
    # run_command(
    #     "v.out.ogr", input=nuts3, output=nuts3_wwtp_potential, format=ESRI_Shapefile
    # )

    # run_command(
    #     "r.out.gdal", input=urban_area, output=clc_urban_area, format=GTiff
    # )
    from grass.pygrass.vector import VectorTopo

    # overcome the DBF limitation on the maximum column lenght
    with VectorTopo(wwtp_plants) as vect:
        for col in vect.table.columns.names():
            if len(col) > 10:
                vect.table.columns.rename(col, col[:10])
        vect.table.conn.commit()

    # perform a buffer, point vector are not supported as output
    wwtp_buf = wwtp_plants + "__buffer"
    run_command(
        "v.buffer", input=wwtp_plants, output=wwtp_buf, distance=buffer, flags="t"
    )

    # run_command("db.describe", flags="c", table=wwtp_buf)

    run_command(
        "v.out.ogr",
        input=wwtp_buf,
        output=wwtp_out,
        format="ESRI_Shapefile",
    )
    print(f"Exported output to {wwtp_out}")


def create_location(
    gisdb: str,
    location: str,
    epsg: int = 3035,
    overwrite: bool = False,
    rasters: Dict[str, str] = None,
    vectors: Dict[str, str] = None,
    actions: List[Any] = None,
):
    os.makedirs(gisdb, exist_ok=True)

    # initialize / handle empty values
    rasters = rasters if rasters else {}
    vectors = vectors if vectors else {}
    actions = [] if actions is None else actions

    # define location path
    loc = os.path.join(gisdb, location)

    if overwrite:
        print(f"» Remove old location ({loc})")
        shutil.rmtree(loc)

    if not os.path.exists(loc):
        print(f"» Created a new location ({loc})")
        with Session(
            gisdb=os.fspath(gisdb),
            location=location,
            mapset="PERMANENT",
            create_opts=f"EPSG:{epsg}",
        ):
            print("» Import rasters")
            load_rasters(rasters, overwrite=overwrite)
            print("» Import vectors")
            load_vectors(vectors, overwrite=overwrite)
            print("» Apply actions")
            for faction, fargs in actions:
                print(f"» Apply {faction.__name__}(*{fargs})")
                faction(*fargs)


def run_module(
    clcraster: str,
    popdensity: str,
    wwtp_plants: str,
    gisdb: str,
    out_folder: str,
    location: str = "location",
    mapset: str = None,
    overwrite: bool = False,
    dist_min: int = 150,
    dist_max: int = 1000,
):
    """
    Create location with input data in PERMANENT and genereted raster in
    test. The region is setting according to the conductivity raster file
    Args:
        data: dictionary with args to pass to GRASS module
        path_gisdb: path where temporary file are created
        out_folder: folder where output file are saved
    """
    mapset = f"mset_{secrets.token_urlsafe(8)}" if mapset is None else mapset
    # dowload default data set
    # TODO:
    rasters = dict(clc=clcraster, popdens=popdensity)

    # create location and import default data set
    actions = [(clc2urban, (CLC, URB, [111, 112, 121], overwrite))]
    create_location(
        gisdb, location, rasters=rasters, overwrite=overwrite, actions=actions
    )

    # create a new mapset for computation and importing the wwtp points
    with Session(
        gisdb=os.fspath(gisdb), location=location, mapset=mapset, create_opts=""
    ) as sess:
        print(f"» Created a new temporary mapset for the computations: {mapset}")
        # import wwtp points
        run_command(
            "v.import", input=str(wwtp_plants), output=WWTP, overwrite=overwrite
        )
        try:
            tech_potential(
                wwtp_plants=WWTP,
                urban_areas=URB,
                dist_min=dist_min,
                dist_max=dist_max,
                overwrite=overwrite,
            )
        except Exception as exc:
            print(f"Issue in mapset: {sess._kwopen['mapset']}")
            raise exc
