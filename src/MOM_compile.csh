#!/bin/csh -f
# Minimal compile script for fully coupled model CM2M experiments

set root = $CYLC_SUITE_SHARE_DIR/mom
set platform = access-cm2 
set type = ACCESS-CM
#setenv DEBUG   yes       # set to yes for debug

set echo
set unit_testing = 0
set help = 0

set code_dir      = $root/src                         # source code directory
set executable    = $root/exec/$platform/$type/fms_$type.x      # executable created after compilation
set mppnccombine  = $root/bin/mppnccombine.$platform  # path to executable mppnccombine
set mkmfTemplate  = $root/mkmf.template.access-cm2 # path to template for your platform
set mkmf          = $root/bin/mkmf                    # path to executable mkmf
set cppDefs  = ( "-Duse_netCDF -Duse_netCDF4 -Duse_libMPI -DACCESS -DACCESS_CM" )

set mkmf_lib = "$mkmf -f -m Makefile -a $code_dir -t $mkmfTemplate"
set lib_include_dirs = "$root/include $code_dir/shared/include $code_dir/shared/mpp/include"

# Build FMS.
cd $root/exp
source ./FMS_compile.csh
set includes = "-I$code_dir/shared/include -I$executable:h:h/lib_FMS -I$executable:h:h/lib_ocean"

# Build the core ocean.
cd $root/exp
source ./ocean_compile.csh
if ( $status ) exit $status


# Build the executable
set mkmf_exec = "$mkmf -f -m Makefile -a $code_dir -t $mkmfTemplate -p $executable:t"
mkdir -p $executable:h
cd $executable:h

set includes = "$includes -I$executable:h:h/$type/lib_ocean" 
set libs = "$executable:h:h/$type/lib_ocean/lib_ocean.a $executable:h:h/lib_FMS/lib_FMS.a"

$mkmf_exec -o "$includes" -c "$cppDefs" -l "$libs"  $srcList
make
if( $status ) then
    echo "Make failed to create the $type executable"
    exit 1
endif    

exit
