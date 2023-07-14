#!/usr/bin/env python3
"""
Module to redistribute ozone for dynamic tropopause.

Example usage:

HPC:
module load scitools/preproduction_legacy-os42
python ./redistribute_ozone_new.py -t '/data/users/hadvh/as326_test/*.pp' -r '/data/users/hadvh/hadgem3_orography.pp' -d '/data/users/hadvh/bb582/density/*.pp' -z '/data/users/hadvh/mmro3_monthly_CMIP6_1850_N96_edited-ancil_2anc.pp' -o '/scratch/hdyson/OzoneRedistribution/output.anc'

On desktop/SPICE, a preproduction OS42 environment is not yet available, so
use the following:

/data/users/support/ants/_dev/environments/latest/bin/python ./redistribute_ozone_new.py -t '/data/users/hadvh/as326_test/*.pp' -r '/data/users/hadvh/hadgem3_orography.pp' -d '/data/users/hadvh/bb582/density/*.pp' -z '/data/users/hadvh/mmro3_monthly_CMIP6_1850_N96_edited-ancil_2anc.pp' -o '/scratch/hdyson/OzoneRedistribution/output.anc'

Note that a netCDF will be created alongside the ancillary.

"""

import argparse
import numpy as np

import ants
import iris
import iris.analysis.cartography
import iris.coord_categorisation as coord_cat


def get_dim(cube, name):
    """Get the dimension on the 'cube' of the coordinate named 'name'."""
    dim = cube.coord_dims(name)
    # dim is a tuple; we expect a single dimension though - rather than return
    # the tuple let's verify that assumption and return only the index of the
    # dimension we're interested in:
    if len(dim) != 1:
        msg = ('Expected single dimension for coordinate {} on cube {}, got {}'
               ' dimensions')
        raise ValueError(msg.format(name, cube.name(), len(dim)))
    return dim[0]


def fix_fields(cube):
    """
    Tweak cube derived from fields file to be compatible with one from a pp.

    CAVEAT: Assumes that the fields file is a single time - will fall over if
    there's multiple times in the cube (assumes a scalar time coordinate and
    promotes it to an axis to allow concatenation with multiple time pp
    fields).

    """
    cube.data = np.array(cube.data, dtype=np.float32)
    cube = iris.util.new_axis(cube, 'time')
    return cube


def fix_pp(cube):
    """Tweak cubes derived from pp files to add ENDGame grid staggering."""
    cube.attributes['grid_staggering'] = 6
    return cube


def fix_nc(cube):
    """Tweak cubes derived from pp files to add ENDGame grid staggering."""
    cube.attributes['grid_staggering'] = 6
    if 'history' in cube.attributes:
        del cube.attributes['history']
    return cube

def remove_extra_time_coords(cube):
    """Remove time coordinates that don't belong on ancillaries."""
    coords_to_remove = ['forecast_period', 'forecast_reference_time', ]
    for coord in coords_to_remove:
        try:
            cube.remove_coord(coord)
        except iris.exceptions.CoordinateNotFoundError:
            pass


def load_data(data, constraint):
    """
    Load data files, and fix some common problems.

    Use data type to distinguish between pp and fields files, make the fields
    files consistent with the pp files, and finally concatenate into a single
    cube.

    """
    cubes = iris.load(data, constraint)

    fields_constraint = iris.Constraint(
        cube_func=lambda x: x.dtype == np.float64)
    pp_constraint = iris.Constraint(cube_func=lambda x: x.dtype == np.float32 and 'Conventions' not in x.attributes)
    nc_constraint = iris.Constraint(cube_func=lambda x: 'Conventions' in x.attributes)
    fields_files = cubes.extract(fields_constraint)
    pp_files = cubes.extract(pp_constraint)
    nc_files = cubes.extract(nc_constraint)

    fields_files = [fix_fields(ff) for ff in fields_files]
    cubes = iris.cube.CubeList(fields_files)

    pp_files = [fix_pp(pp) for pp in pp_files]
    if pp_files:
        # If there's multiple pp cubes, we need to be careful to distinguish
        # between a cubelist and a cube (which is iterable) later - possible, but
        # adds some complexity we can hopefully avoid.
        if len(pp_files) != 1:
            msg = ("pp files were not merged into a single cube - this script "
                   "needs to be updated to handle this case")
            raise ValueError(msg)
        # why pp_files[0]?  pp_files is a cubelist, so adding it directly results
        # in a cubelist containing a cube for the fields_file and a cubelist for
        # the pp_file.  Preceding check ensures there is no pp_files[N] for N>0.
        cubes.append(pp_files[0])

    nc_files = [fix_nc(ff) for ff in nc_files]
    cubes += nc_files

    # Discard forecast_period/forecast_reference_time coordinates for all
    # cubes - they don't belong in ancillaries:
    [remove_extra_time_coords(cube) for cube in cubes]
    cube = cubes.concatenate_cube()

    return cube


def reconcile_lat_lon(cube1, cube2):
    """
    Fix horizontal coordinates.

    To allow further processing, if the lat/lon of the two cubes are
    sufficiently similar, this function replaces the horizontal coordinates of
    cube2 with those from cube1.

    Operates on the cubes in place.
    """
    # For n216e, there's small (4th decimal place) differences between the
    # lat/lon coord values for the UMDIR orography and density files.  Let's
    # check that they're close, and if so, replace the density values with
    # those from the orography:
    def _reconcile_coords(coord1, coord2):
        if np.allclose(coord1.points, coord2.points, atol=3e-4):
            coord2.points = coord1.points
        else:
            maxdiff = np.max(np.abs(coord1.points-coord2.points))
            raise RuntimeError(
                '{} points differ.  '
                'Maximum difference: {}'.format(coord1.name(), maxdiff))
        if np.allclose(coord1.bounds, coord2.bounds, atol=3e-4):
            coord2.bounds = coord1.bounds
        else:
            maxdiff = np.max(np.abs(coord1.bounds-coord2.bounds))
            raise RuntimeError(
                '{} bounds differ.  '
                'Maximum difference: {}'.format(coord1.name(), maxdiff))

    _reconcile_coords(cube1.coord('latitude'), cube2.coord('latitude'))
    _reconcile_coords(cube1.coord('longitude'), cube2.coord('longitude'))

    # Fix for circular attribute
    cube2.coord('longitude').circular = cube1.coord('longitude').circular


def process(args):
    # READ IN dyn tropopause and orography **from MASS**
    # Want last 2 years worth of monthly mean data
    # **Will also read density from MASS, and oz from ancillary**

    th = load_data(args.tropopause, 'tropopause_altitude')
    # th = iris.load_cube('/data/local/hadvh/cmip6/bb582/*.pp',
    #                    iris.Constraint('tropopause_altitude'))  # [24,nlat,nlon]
    # **Orog is resolution dependent file** [nlat,nlon]
    orog = iris.load_cube(args.orography, 'surface_altitude')

    # Form monthly climatologies

    coord_cat.add_month(th, 'time', name='month')
    th = th.aggregated_by(['month'], iris.analysis.MEAN)  # [12,nlat,nlon]

    # Add orography

    for i in np.arange(12):
        th.data[i, :, :] = th.data[i, :, :] + orog.data

    # Form grid_areas

    if th.coord('latitude').bounds is None:
        th.coord('latitude').guess_bounds()

    if th.coord('longitude').bounds is None:
        th.coord('longitude').guess_bounds()

    grid_areas = iris.analysis.cartography.area_weights(th)

    # Form zonal mean

    th = th.collapsed(['longitude'],
                      iris.analysis.MEAN, weights=grid_areas)  # [12,nlat]

    # READ IN ozone and pressure(or density)

    # Density*r*r (STASH 253):  **Need to add STASH 253 to CMIP6 jobs**

    # [24,85,nlat,nlon]
    rhoa2 = load_data(args.density,
                      iris.AttributeConstraint(STASH='m01s00i253'))
    coord_cat.add_month(rhoa2, 'time', name='month')
    rhoa2 = rhoa2.aggregated_by(['month'], iris.analysis.MEAN)  # [12,85,nlat,nlon]
    # ** oz should be ancillary created for previous year (except in yr1 of run) **
    ozone_constraint = iris.Constraint(
        time=lambda cell: cell.point.year == args.year)
    try:
        oz = iris.load_cube(args.ozone, ozone_constraint)
    except iris.exceptions.ConstraintMismatchError:
        if args.strict_year:
            raise
        else:
            # Single year ozone file doesn't fit constraint since it's missing the
            # year from the time coordinate:
            oz = iris.load_cube(args.ozone)
            # But still worth checking it really is a single year
            if len(oz.coord(axis='t').points) != 12:
                raise RuntimeError(
                    "Ozone file {} doesn't have expected time coordinates"
                    .format(args.ozone))
    # [12,85,nlat,nlon]

    if oz.coord('latitude').bounds is None:
        oz.coord('latitude').guess_bounds()

    if oz.coord('longitude').bounds is None:
        oz.coord('longitude').guess_bounds()

    # Vertically interpolate rhoa2 onto ozone grid

    alt = oz.coord('level_height').points
    # rhoa2_interp = rhoa2.interpolate([('level_height', alt)],
    rhoa2_interp = rhoa2.interpolate([('atmosphere_hybrid_height_coordinate', alt)],
                                     iris.analysis.Linear())
    rhoa2 = rhoa2_interp.copy()

    # Make rhoa2 and oz meta-data the same

    rhoa2.coord('latitude').var_name = None
    rhoa2.coord('longitude').var_name = None
    rhoa2.coord('longitude').circular = False

    time_dim = get_dim(rhoa2, 'time')
    rhoa2.remove_coord('time')
    rhoa2.add_dim_coord(oz.coord('time'), time_dim)

    rhoa2.remove_coord('month')

    # Since the density data was on DALLRH levels rather than DALLTH levels, we
    # effectively want to interpolate the data only but preserve the vertical
    # coordinates.  Simplest way to achieve this is to restore the vertical
    # coordinates from the ozone file:
    level_height = iris.coords.AuxCoord.from_coord(oz.coord('level_height'))
    vertical_dim = get_dim(rhoa2, 'atmosphere_hybrid_height_coordinate')
    rhoa2.remove_coord('atmosphere_hybrid_height_coordinate')
    rhoa2.add_aux_coord(level_height, vertical_dim)

    sigma = iris.coords.AuxCoord.from_coord(oz.coord('sigma'))
    try:
        rhoa2.remove_coord('sigma')
    except iris.exceptions.CoordinateNotFoundError:
        # Post-processed netCDF files don't have this
        pass
    rhoa2.add_aux_coord(sigma, vertical_dim)

    model_level_number = iris.coords.DimCoord.from_coord(
        oz.coord('model_level_number'))
    try:
        rhoa2.remove_coord('model_level_number')
    except iris.exceptions.CoordinateNotFoundError:
        # Post-processed netCDF files don't have this
        pass
    rhoa2.add_dim_coord(model_level_number, vertical_dim)

    # Form mass weighted zonal mean -- int(oz*p)/int(p)

    if rhoa2.coord('latitude').bounds is None:
        rhoa2.coord('latitude').guess_bounds()

    if rhoa2.coord('longitude').bounds is None:
        rhoa2.coord('longitude').guess_bounds()

    grid_areas = iris.analysis.cartography.area_weights(rhoa2)

    # If density has an orography, remove it - we want to be working with
    # level heights:
    if len(rhoa2.coords('surface_altitude')) == 1:
        # The altitude coordinate gets lost in the merge of fields from netCDF files
        # for some reason.
        if rhoa2.aux_factories:
            rhoa2.remove_aux_factory(rhoa2.aux_factory(name='altitude'))
        rhoa2.remove_coord('surface_altitude')

    oz2d = oz.copy()

    reconcile_lat_lon(oz2d, rhoa2)

    oz2d = iris.analysis.maths.multiply(oz2d, rhoa2)
    oz2d = oz2d.collapsed(
        ['longitude'], iris.analysis.MEAN, weights=grid_areas)
    rhoa2_2d = rhoa2.collapsed(['longitude'],
                               iris.analysis.MEAN, weights=grid_areas)
    oz2d = iris.analysis.maths.divide(oz2d, rhoa2_2d)

    # Calculate actual height(x,y,z) corresp to ozone hybrid_ht

    oz_withheight = oz.copy()

    orog_coord = iris.coords.AuxCoord(
        points=orog.data, units="m", standard_name="surface_altitude")

    lat_dim = get_dim(oz_withheight, 'latitude')
    lon_dim = get_dim(oz_withheight, 'longitude')
    oz_withheight.add_aux_coord(orog_coord, (lat_dim, lon_dim))

    factory = iris.aux_factory.HybridHeightFactory(
        delta=oz_withheight.coord("level_height"),
        sigma=oz_withheight.coord("sigma"),
        orography=oz_withheight.coord("surface_altitude"))

    oz_withheight.add_aux_factory(factory)

    hz = oz_withheight.coord("altitude").points

    # REDISTRIBUTION

    longitude = oz.coord('longitude').points  # [nlon]
    latitude = oz.coord('latitude').points  # [nlat]
    nlon = np.size(longitude)
    nlat = np.size(latitude)
    coslat = np.cos(latitude*np.pi/180.)
    dlon = np.ones(nlon)
    dlat = np.ones(nlat)
    dz = np.ones([85, nlat, nlon])  # m

    for i in np.arange(1, nlon-1):
        dlon[i] = (longitude[i+1] - longitude[i-1])/2.
    dlon[0] = longitude[1] - longitude[0]
    dlon[nlon-1] = longitude[nlon-1] - longitude[nlon-2]

    for i in np.arange(1, nlat-1):
        dlat[i] = (latitude[i+1] - latitude[i-1])/2.
    dlat[0] = latitude[1] - latitude[0]
    dlat[nlat-1] = latitude[nlat-1] - latitude[nlat-2]

    dlon = (np.pi/180.)*dlon
    dlat = (np.pi/180.)*dlat

    for j in np.arange(nlat):
        for k in np.arange(nlon):
            for i in np.arange(1, 84):
                dz[i, j, k] = (hz[i+1, j, k] - hz[i-1, j, k])/2.
            dz[0, j, k] = hz[1, j, k] - hz[0, j, k]
            dz[84, j, k] = hz[84, j, k] - hz[83, j, k]

    # REMOVE tropospheric ozone = dT ...

    dz2d = np.average(dz, axis=2)
    hz = np.average(hz, axis=2)  # [85,nlat]
    oz2d_dat = oz2d.data
    oz_redist = oz2d_dat.copy()

    th_dat = th.data
    for l in np.arange(12):
        for j in np.arange(nlat):
            # Define height of ozone tropopause (for each lat)
            # = 1km below dynamical tropopause
            counter_dyntrop = np.where(hz[:, j] > (th_dat[l, j] - 1000.))[0]
            counter_dyntrop = counter_dyntrop[0]
            # Set ozone to 80ppbv at ozone tropopause.
            # Linearly interpolate to value 2km above dynamical tropopause.
            oz_redist[l, counter_dyntrop, j] = 1.32e-7  # 80ppbv
            counter_highoz = np.where(hz[:, j] > (th_dat[l, j] + 2000.))[0]
            counter_highoz = 1+counter_highoz[0]
            # linearly interpolate log(ozone)
            # in height between highoz values and 80ppbv
            ozint = [np.log(oz_redist[l, counter_dyntrop, j]),
                     np.log(oz2d_dat[l, counter_highoz, j])]
            htint = [hz[counter_dyntrop, j], hz[counter_highoz, j]]
            htsint = hz[counter_dyntrop:counter_highoz, j]
            oz_redist[l, counter_dyntrop:counter_highoz, j] = np.exp(
                np.interp(htsint, htint, ozint))
            # If orig ozone is < 80ppbv at 1km below, then set at 80ppbv
            # and linearly interpolate down to value 2km below this
            if (oz2d_dat[l, counter_dyntrop, j] < 1.32e-7):
                counter_lowoz = np.where(hz[:, j] > (th_dat[l, j] - 3000.))[0]
                counter_lowoz = counter_lowoz[0]
                # linearly interpolate log(ozone) in height
                # between lowoz values and 80ppbv
                ozint = [np.log(oz2d_dat[l, counter_lowoz, j]),
                         np.log(oz_redist[l, counter_dyntrop, j])]
                htint = [hz[counter_lowoz, j], hz[counter_dyntrop, j]]
                htsint = hz[counter_lowoz:counter_dyntrop, j]
                oz_redist[l, counter_lowoz:counter_dyntrop, j] = np.exp(
                    np.interp(htsint, htint, ozint))
            # If orig ozone is > 80ppbv at 1km below, then keep at 80ppbv
            # until height where it becomes 80ppbv
            if (oz2d_dat[l, counter_dyntrop, j] > 1.32e-7):
                counter_oztrop = np.where(oz2d_dat[l, :, j] < 1.32e-7)[0]
                counter_oztrop = counter_oztrop[np.size(counter_oztrop)-1]
                oz_redist[l, counter_oztrop+1:counter_dyntrop, j] = 1.32e-7

    # Calculate mass of ozone removed (dT)

    glob_dt = np.ones([12])
    oz2d_diff = oz2d.copy()
    oz2d_diff.data = oz_redist - oz2d_dat
    oz2d_diff = iris.analysis.maths.multiply(oz2d_diff, rhoa2_2d)
    oz2d_diff_dat = oz2d_diff.data
    for l in np.arange(12):
        for i in np.arange(85):
            for j in np.arange(nlat):
                glob_dt[l] = glob_dt[l] - \
                    oz2d_diff_dat[l, i, j]*coslat[j]*2.*np.pi*dlat[j]*dz2d[i, j]

    # Calculate mass of stratospheric ozone (S)

    strat_oz2d = np.ones([12])
    oz2d_diff = oz2d.copy()
    oz2d_diff.data = oz_redist
    oz2d_diff = iris.analysis.maths.multiply(oz2d_diff, rhoa2_2d)
    oz2d_diff_dat = oz2d_diff.data
    for l in np.arange(12):
        for j in np.arange(nlat):
            counter = np.where(hz[:, j] > th_dat[l, j])[0]
            counter = counter[0]
            for i in np.arange(counter, 85):
                strat_oz2d[l] = strat_oz2d[l] + \
                    oz2d_diff_dat[l, i, j]*coslat[j]*2.*np.pi*dlat[j]*dz2d[i, j]

    # Multiply stratospheric ozone by (S+dT)/S

    strat_oz2d = (strat_oz2d + glob_dt) / strat_oz2d

    for j in np.arange(nlat):
        counter = np.where(hz[:, j] > th_dat[l, j])[0]
        counter = counter[0]
        for i in np.arange(counter, 85):
            oz_redist[:, i, j] = oz_redist[:, i, j]*strat_oz2d

    # Apply redistribution to 3D ozone field

    oz_diff = oz_redist - oz2d_dat

    for k in np.arange(nlon):
        oz.data[:, :, :, k] = oz.data[:, :, :, k] + oz_diff

    oz.data = oz.data
    # ** Write oz to new ancillary **
    if oz.coord('time').bounds is None:
        oz.coord('time').guess_bounds()
    ants.save(oz, args.output, saver='ancil')

    # ** Transfer this ancillary to HPC **
    # ** Store this ancillary on MASS **


def get_arg_parser(docs=None):
    """CLI argument parser for input and output files."""
    parser = argparse.ArgumentParser(
        conflict_handler='resolve',
        description=docs,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    required = parser.add_argument_group('required arguments')

    required.add_argument(
        '-o',
        '--output',
        required=True,
        type=str,
        help="Filename to write the result to.",
    )

    required.add_argument(
        '-t',
        '--tropopause',
        required=True,
        nargs='+',
        type=str,
        help="File names for tropopause altitude files",
    )

    required.add_argument(
        '-r',  # -o already used for output
        '--orography',
        required=True,
        type=str,
        help="File name for orography file",
    )

    required.add_argument(
        '-d',
        '--density',
        required=True,
        nargs='+',
        type=str,
        help="File names for density files",
    )

    required.add_argument(
        '-z',  # -o already used for output
        '--ozone',
        required=True,
        type=str,
        help="File name for ozone file",
    )

    required.add_argument(
        '-y',
        '--year',
        required=True,
        type=int,
        help="Year to use from the ozone file",
    )

    parser.add_argument(
        '--strict_year',
        dest='strict_year',
        action='store_true',
        help='Enforce strict checking of year constraint'
    )

    return parser


if __name__ == '__main__':
    arg_parser = get_arg_parser(__doc__)
    args = arg_parser.parse_args()
    process(args)
