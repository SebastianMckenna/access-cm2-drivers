#! /bin/bash

# Modified version of the Met Office atmos_archive script.

# Just move files to the archive directory


     echo "\n"
     echo "*** atmos_archive.sh script ***\n"

filename=.

cd $DATAM

for file in `ls ?????a${filename}*`
do

   # Deduce variables from the file name
   stchar=`echo $file | cut -c 9`  # This is a one character string containing the stream
   ppdump=`echo $file | cut -c 8`  # This is either a d (dump) or p (stash output)
   if [ "$ppdump" = "p" ]; then
      DIR="history"
   else
      DIR="restart"
   fi
   echo "ATMOS_ARCHIVE considering", $file
   # stream=a${ppdump}${stchar}${dirend}  # This is the MASS directory the file will end up in. e.g. apy.pp
   jobid=`echo $file | cut -c 1-5`     # This is the first 5 characters of the file (was the jobid in UMUI jobs but now just 'atmos')

   # Make sure this is not the final file from this stream
   lastfile=`ls -rt ${jobid}a${filename}${ppdump}${stchar}* | tail -1`

   # Also check this is not one of the last 4 dump files
   if [ "$ppdump" = "d" ]; then
      lastfilem1=`ls -rt ${jobid}a${filename}${ppdump}${stchar}* | tail -2 | head -1`
      lastfilem2=`ls -rt ${jobid}a${filename}${ppdump}${stchar}* | tail -3 | head -1`
      lastfilem3=`ls -rt ${jobid}a${filename}${ppdump}${stchar}* | tail -4 | head -1`
   fi

   # Ignore the last files of the s and y streams (we want to archive them as soon as they are available)
   if [ "$stchar" = "s" -o "$stchar" = "y" ]; then
      lastfile="xxxx"
   fi

   # Do the test whether or not to archive this file
   if [ "$file" = "$lastfile" -o "$file" = "$lastfilem1" -o "$file" = "$lastfilem2" -o "$file" = "$lastfilem3" ]; then
      echo "$file is the final file from this stream. Skipping archiving till it is superceeded."
   else

      archive=true
      # Only archive a dump if it is the 1st of December, 1st of September or 1st of June
      # ACCESS   Jan 1
      # Assuming a name like ${RUNID}a.daYYYYMMDD where RUNID is 5 chars
      date=`echo $file | cut -c 14-17`
      if [ "$ppdump" = "d" ]; then
         archive=false
         # if [ "$date" = "0901" -o "$date" = "1201" -o "$date" = "0601" ]; then
	 echo "Considering dump file with date", $date
         if [[ "$date" = "0101" || "$date" = "0701" ]]; then
            archive=true
         fi
      fi

      # Set the conversion and file endings for pp files
      # conversion=" "
      # fileend=" "
      # if [ "$ppdump" = "p" ]; then
      #    conversion="-c=umpp"
      #    fileend=".pp"
      # fi

       # If the header does not indicate any fields then remove it
      # Note: grep/awk depends on the pumf output being in a specific format (hence vn7.5)
      # headerfile=`/projects/um1/vn8.4/ibm/utils/pumf $file | grep Header | awk -F: '{print $2}'`
      # foundfields=`grep 'Words 1-45' $headerfile`
      # if [ -z "$foundfields" ];then
      #    echo "$file does not contain any fields. Removing file."
      #    rm $file
      # else

         # Archive the file
         if [ "$archive" = "true" ];then
            # echo "moo put -f $conversion $file moose:$NAMESPACE/$CYLC_SUITE_REG_NAME/$stream/${file}${fileend}"
            # moo put -f $conversion $file moose:$NAMESPACE/$CYLC_SUITE_REG_NAME/$stream/${file}${fileend}
            mv $file $ARCHIVEDIR/$DIR/atm
            # if [ "$?" == "0" ]; then
            #    echo "$file has been archived successfully. Removing original file."
            #    rm -f $file
            # else
	    #    echo "ERROR: could not archive $file"
            # fi
         else
            echo "$file has been superceeded and is not required to be archived. Deleting file."
            rm $file
         fi
      # fi  # empty file from pumf

   fi

done
