#! /bin/csh -f

set echo on
#setenv DEBUG   yes       # set to yes for debug

### Change these to your own site and user directory! 
### You will need to create a Makefile Macro in bld
### Platform and its architecture ($HOST = xe)
setenv ARCH raijin

# Set AusCOM home:
# setenv ice_root $CYLC_SUITE_SHARE_DIR/cice

mkdir $ICE_ROOT/compile_${CICE_COL}x${CICE_ROW}
cd $ICE_ROOT/compile_${CICE_COL}x${CICE_ROW}
#----------------------------------------------------------------------

### Specialty code
setenv CAM_ICE  no        # set to yes for CAM runs (single column)
setenv SHRDIR   csm_share # location of CCSM shared code
setenv IO_TYPE  netcdf    # set to none if netcdf library is unavailable
                          # set to pio for parallel netcdf
setenv DITTO    no        # reproducible diagnostics
setenv THRD     no        # set to yes for OpenMP threading
if ( $THRD == 'yes') setenv OMP_NUM_THREADS 2 # positive integer 

setenv ACCESS   yes       # set to yes for ACCESS
setenv AusCOM   yes       # set to yes for AusCOM
setenv OASIS3_MCT yes	  # oasis3-mct version
setenv CHAN     MPI1	  # MPI1 or MPI2 (always MPI1!)
setenv NICELYR    4       # number of vertical layers in the ice
setenv NSNWLYR    1       # number of vertical layers in the snow
setenv NICECAT    5       # number of ice thickness categories

### Location of ACCESS system

### Location of this model (source)
setenv SRCDIR $cwd:h  #$SYSTEMDIR/submodels/cice5.0.4
echo SRCDIR: $SRCDIR
 
### For multi-Layer ice (standard) configuration
setenv N_ILYR 4                 #4 for standard multi-layer ice (ktherm=1)
#setenv N_ILYR 1 		#1 for ktherm=0, zero-layer thermodynamics

### Location and name of the generated exectuable
setenv DATESTR `date +%Y%m%d`
setenv BINDIR $ICE_ROOT/bin
if !(-d $BINDIR) mkdir -p $BINDIR
#setenv EXE cice5.0-185.${DATESTR}_${nproc}p_${N_ILYR}lyr
setenv EXE cice5.exe

### Where this model is compiled
setenv OBJDIR $SRCDIR/compile_${CICE_COL}x${CICE_ROW}/build_${CHAN}_{$ICE_NPROCS}p-mct
if !(-d $OBJDIR) mkdir -p $OBJDIR
#/bin/rm $OBJDIR/*
#

### Grid resolution
#setenv GRID gx3 ; setenv RES 100x116
#setenv GRID gx1 ; setenv RES 320x384
#setenv GRID tx1 ; setenv RES 360x240
#setenv GRID tp1 ; setenv RES 360x300
setenv GRID tp1 ; # setenv RES $2 #1440x1080
                                                                                
###########################################
# ars599: 24032014
#	copy from /short/p66/ars599/CICE.v5.0/accice.v504_csiro
#	solo_ice_comp
###########################################
### Tracers               # match ice_in tracer_nml to conserve memory
setenv TRAGE   1          # set to 1 for ice age tracer
setenv TRFY    1          # set to 1 for first-year ice area tracer
setenv TRLVL   1          # set to 1 for level and deformed ice tracers
setenv TRPND   1          # set to 1 for melt pond tracers
setenv NTRAERO 0          # number of aerosol tracers 
                          # (up to max_aero in ice_domain_size.F90) 
                          # CESM uses 3 aerosol tracers
setenv TRBRI   0          # set to 1 for brine height tracer
setenv NBGCLYR 0          # number of zbgc layers
setenv TRBGCS  0          # number of skeletal layer bgc tracers 
                          # TRBGCS=0 or 2<=TRBGCS<=9)

### File unit numbers
setenv NUMIN 11           # minimum file unit number
setenv NUMAX 199           # maximum file unit number

if ($IO_TYPE == 'netcdf') then
  setenv IODIR io_netcdf
else if ($IO_TYPE == 'pio') then
  setenv IODIR io_pio
else
  setenv IODIR io_binary
endif

###########################################
                                                                                
setenv CBLD   $SRCDIR/bld
                                                                                
cp -f $CBLD/Makefile.std $CBLD/Makefile

if ($ICE_NPROCS == 1) then
   setenv COMMDIR serial
else
   setenv COMMDIR mpi
endif
echo COMMDIR: $COMMDIR
                                                                                
if ($ACCESS == 'yes') then
  setenv DRVDIR access
else  
  setenv DRVDIR cice
endif
echo DRVDIR: $DRVDIR
                                                                                
cd $OBJDIR
                                                                                
### List of source code directories (in order of importance).
cat >! Filepath << EOF
$SRCDIR/drivers/$DRVDIR
$SRCDIR/source
$SRCDIR/$COMMDIR
$SRCDIR/$IODIR
$SRCDIR/$SHRDIR
EOF
                                                                                
cc -o makdep $CBLD/makdep.c                      || exit 2

setenv MACFILE $ICE_ROOT/Macros.Linux.${ARCH}

gmake VPFILE=Filepath EXEC=$BINDIR/$EXE \
           NXGLOB=$CICE_COL NYGLOB=$CICE_ROW \
           BLCKX=$CICE_BLKX BLCKY=$CICE_BLKY MXBLCKS=$CICE_MAXBK \
      -f  $CBLD/Makefile MACFILE=$MACFILE || exit 2
                                                                                
cd ..
pwd
echo NTASK = $ICE_NPROCS
echo "global N, block_size" 
echo "x    $CICE_COL,    $CICE_BLKX"
echo "y    $CICE_ROW,    $CICE_BLKY"
echo max_blocks = $CICE_MAXBK
echo $TRAGE   = TRAGE,   iage tracer
echo $TRFY    = TRFY,    first-year ice tracer
echo $TRLVL   = TRLVL,   level-ice tracers
echo $TRPND   = TRPND,   melt pond tracers
echo $NTRAERO = NTRAERO, number of aerosol tracers
echo $TRBRI   = TRBRI,   brine height tracer
echo $NBGCLYR = NBGCLYR, number of bio grid layers
echo $TRBGCS  = TRBGCS,  number of BGC tracers
