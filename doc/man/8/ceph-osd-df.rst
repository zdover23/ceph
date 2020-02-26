:orphan:

=================================================
 ceph osd df -- df for ceph object storage daemon
=================================================

.. program:: ceph osd df

Synopsis
========

| **ceph osd df** 

Description
===========

**ceph osd df** displays storage statistics for the object storage daemon 
for the Ceph distributed file system. 



ID CLASS WEIGHT  REWEIGHT SIZE    RAW USE DATA  OMAP META  AVAIL   %USE VAR  PGS STATUS 
 0   hdd 0.09859  1.00000 101 GiB 2.0 GiB 3 MiB  0 B 1 GiB  99 GiB 1.98 1.00  64     up 
 1   hdd 0.09859  1.00000 101 GiB 2.0 GiB 3 MiB  0 B 1 GiB  99 GiB 1.98 1.00  64     up 
 2   hdd 0.09859  1.00000 101 GiB 2.0 GiB 3 MiB  0 B 1 GiB  99 GiB 1.98 1.00  64     up 
                    TOTAL 303 GiB 6.0 GiB 9 MiB  0 B 3 GiB 297 GiB 1.98                 

ID - the unique OSD identifier
CLASS - The type of devices the OSD uses.
WEIGHT - the CRUSH weight of the OSD. This is equal to the size of your disk.
REWEIGHT - an adjustment factor applied to the CRUSH weight of the OSD that determines the final weight of the OSD. The default is 1.0.
SIZE - the size of the disk in bytes
RAW USE - The capacity of your disk that has already been used to store data
DATA - The amount of data capacity that is used by user data
OMAP - An estimate value of the 'bluefs' storage that is being used to store object map ('omap') data (key value pairs stored in 'rocksdb')
META - The 'bluefs' space allocated, or the value set in the 'bluestore_bluefs_min' parameter, whichever is larger, for internal metadata which is calculated as the total space allocated in 'bluefs' minus the estimated 'omap' data size.
AVAIL - the unused capacity of the disk in bytes
%USE - the percentage of the disk that is used
VAR - the variance of the data distribution relative to the mean. 
PGS - the count of PGs located on the OSD.
STATUS - up/down/destroyed

Options
=======

.. option:: -f, --foreground

   Foreground: do not daemonize after startup (run in foreground). Do
   not generate a pid file. Useful when run via :doc:`ceph-run <ceph-run>`\(8).

.. option:: -d

   Debug mode: like ``-f``, but also send all log output to stderr.



Availability
============

**ceph osd df** is part of Ceph, a massively scalable, open-source, distributed storage system. Please refer to
the Ceph documentation at http://ceph.com/docs for more information.

See also
========

:doc:`ceph <ceph>`\(8),
:doc:`ceph-mds <ceph-mds>`\(8),
:doc:`ceph-mon <ceph-mon>`\(8),
:doc:`ceph-authtool <ceph-authtool>`\(8)
