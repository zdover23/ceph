======================
 Adding/Removing OSDs
======================

When you have a cluster up and running, you may add OSDs or remove OSDs
from the cluster at runtime.

Adding OSDs
===========

When you want to expand a cluster, you may add an OSD at runtime. With Ceph, an
OSD is generally one Ceph ``ceph-osd`` daemon for one storage drive within a
host machine. If your host has multiple storage drives, you may map one
``ceph-osd`` daemon for each drive.

Generally, it's a good idea to check the capacity of your cluster to see if you
are reaching the upper end of its capacity. As your cluster reaches its ``near
full`` ratio, you should add one or more OSDs to expand your cluster's capacity.

.. warning:: Do not let your cluster reach its ``full ratio`` before
   adding an OSD. OSD failures that occur after the cluster reaches
   its ``near full`` ratio may cause the cluster to exceed its
   ``full ratio``.

Deploy your Hardware
--------------------

If you are adding a new host when adding a new OSD,  see `Hardware
Recommendations`_ for details on minimum recommendations for OSD hardware. To
add an OSD host to your cluster, first make sure you have an up-to-date version
of Linux installed, and you have made some initial preparations for your
storage drives.  See `Filesystem Recommendations`_ for details.

Add your OSD host to a rack in your cluster, connect it to the network
and ensure that it has network connectivity. See the `Network Configuration
Reference`_ for details.

.. _Hardware Recommendations: ../../../start/hardware-recommendations
.. _Filesystem Recommendations: ../../configuration/filesystem-recommendations
.. _Network Configuration Reference: ../../configuration/network-config-ref

Install the Required Software
-----------------------------

For manually deployed clusters, you must install Ceph packages
manually. See `Installing Ceph (Manual)`_ for details.
You should configure SSH to a user with password-less authentication
and root permissions.

.. _Installing Ceph (Manual): ../../../install


Adding an OSD (Manual)
----------------------

This procedure sets up a ``ceph-osd`` daemon, configures it to use one drive,
and configures the cluster to distribute data to the OSD. If your host has
multiple drives, you may add an OSD for each drive by repeating this procedure.

To add an OSD, create a data directory for it, mount a drive to that directory,
add the OSD to the cluster, and then add it to the CRUSH map.

When you add the OSD to the CRUSH map, consider the weight you give to the new
OSD. Hard drive capacity grows 40% per year, so newer OSD hosts may have larger
hard drives than older hosts in the cluster (i.e., they may have greater
weight).

.. tip:: Ceph prefers uniform hardware across pools. If you are adding drives
   of dissimilar size, you can adjust their weights. However, for best
   performance, consider a CRUSH hierarchy with drives of the same type/size.

#. Create the OSD. If no UUID is given, it will be set automatically when the
   OSD starts up. The following command will output the OSD number, which you
   will need for subsequent steps:

   .. prompt:: bash $

      ceph osd create [{uuid} [{id}]]

   If the optional parameter {id} is given it will be used as the OSD id.
   Note, in this case the command may fail if the number is already in use.

   .. warning:: In general, explicitly specifying {id} is not recommended.
      IDs are allocated as an array, and skipping entries consumes some extra
      memory. This can become significant if there are large gaps and/or
      clusters are large. If {id} is not specified, the smallest available is
      used.

#. Create the default directory on your new OSD:

   .. prompt:: bash $

      ssh {new-osd-host}
      sudo mkdir /var/lib/ceph/osd/ceph-{osd-number}

#. If the OSD is for a drive other than the OS drive, prepare it
   for use with Ceph, and mount it to the directory you just created:

   .. prompt:: bash $

      ssh {new-osd-host}
      sudo mkfs -t {fstype} /dev/{drive}
      sudo mount -o user_xattr /dev/{hdd} /var/lib/ceph/osd/ceph-{osd-number}

#. Initialize the OSD data directory:

   .. prompt:: bash $

      ssh {new-osd-host}
      ceph-osd -i {osd-num} --mkfs --mkkey

   The directory must be empty before you can run ``ceph-osd``.

#. Register the OSD authentication key. The value of ``ceph`` for
   ``ceph-{osd-num}`` in the path is the ``$cluster-$id``.  If your
   cluster name differs from ``ceph``, use your cluster name instead:

   .. prompt:: bash $

      ceph auth add osd.{osd-num} osd 'allow *' mon 'allow rwx' -i /var/lib/ceph/osd/ceph-{osd-num}/keyring

#. Add the OSD to the CRUSH map so that the OSD can begin receiving data. The
   ``ceph osd crush add`` command allows you to add OSDs to the CRUSH hierarchy
   wherever you wish. If you specify at least one bucket, the command
   will place the OSD into the most specific bucket you specify, *and* it will
   move that bucket underneath any other buckets you specify. **Important:** If
   you specify only the root bucket, the command will attach the OSD directly
   to the root, but CRUSH rules expect OSDs to be inside of hosts.

   Execute the following:

   .. prompt:: bash $

      ceph osd crush add {id-or-name} {weight}  [{bucket-type}={bucket-name} ...]

   You may also decompile the CRUSH map, add the OSD to the device list, add the
   host as a bucket (if it's not already in the CRUSH map), add the device as an
   item in the host, assign it a weight, recompile it and set it. See
   `Add/Move an OSD`_ for details.


.. _rados-replacing-an-osd:

Replacing an OSD
----------------

.. note:: If the instructions in this section do not work for you, try the
   instructions in the cephadm documentation: :ref:`cephadm-replacing-an-osd`.

When disks fail, or if an administrator wants to reprovision OSDs with a new
backend, for instance, for switching from FileStore to BlueStore, OSDs need to
be replaced. Unlike `Removing the OSD`_, replaced OSD's id and CRUSH map entry
need to be keep intact after the OSD is destroyed for replacement.

#. Make sure it is safe to destroy the OSD:

   .. prompt:: bash $

      while ! ceph osd safe-to-destroy osd.{id} ; do sleep 10 ; done

#. Destroy the OSD first:

   .. prompt:: bash $

      ceph osd destroy {id} --yes-i-really-mean-it

#. Zap a disk for the new OSD, if the disk was used before for other purposes.
   It's not necessary for a new disk:

   .. prompt:: bash $

      ceph-volume lvm zap /dev/sdX

#. Prepare the disk for replacement by using the previously destroyed OSD id:

   .. prompt:: bash $

      ceph-volume lvm prepare --osd-id {id} --data /dev/sdX

#. And activate the OSD:

   .. prompt:: bash $

      ceph-volume lvm activate {id} {fsid}

Alternatively, instead of preparing and activating, the device can be recreated
in one call, like:

   .. prompt:: bash $

      ceph-volume lvm create --osd-id {id} --data /dev/sdX


Starting the OSD
----------------

After an OSD is added to Ceph, the OSD is in the cluster. However, until it is
started, the OSD is considered ``down`` and ``in``. The OSD is not running and
will be unable to receive data. To start an OSD, either run ``service ceph``
from your admin host or run a command of the following form to start the OSD
from its host machine:

   .. prompt:: bash $

      sudo systemctl start ceph-osd@{osd-num}

After the OSD is started, it is considered ``up`` and ``in``.

Observing the Data Migration
----------------------------

After the new OSD has been added to the CRUSH map, Ceph begins rebalancing the
cluster by migrating placement groups (PGs) to the new OSD. To observe this
process by using the `ceph`_ tool, run the following command:

   .. prompt:: bash $

      ceph -w

Or:

   .. prompt:: bash $

      watch ceph status

The PG states will first change from ``active+clean`` to ``active, some
degraded objects`` and then return to ``active+clean`` when migration
completes. When you are finished observing, press Ctrl-C to exit.

.. _Add/Move an OSD: ../crush-map#addosd
.. _ceph: ../monitoring


Removing OSDs (Manual)
======================

It is possible to remove an OSD manually while the cluster is running: you
might want to do this in order to reduce the size of the cluster or when
replacing hardware. Typically, an OSD is a Ceph ``ceph-osd`` daemon running on
one storage drive within a host machine. Alternatively, if your host machine
has multiple storage drives, you might need to remove multiple ``ceph-osd``
daemons: one daemon for each drive on the machine. 

.. warning:: Before you begin the process of removing an OSD, make sure that
   your cluster is not near its ``full ratio``. Otherwise the act of removing
   OSDs might cause the cluster to reach or exceed its ``full ratio``.


Taking the OSD ``out`` of the Cluster
-------------------------------------

OSDs are typically ``up`` and ``in`` before they are removed from the cluster.
Before the OSD can be removed from the cluster, the OSD must be taken ``out``
of the cluster so that Ceph can begin rebalancing and copying its data to other
OSDs. To take an OSD ``out`` of the cluster, run a command of the following
form:

   .. prompt:: bash $

      ceph osd out {osd-num}


Observing the Data Migration
----------------------------

After the OSD has been taken ``out`` of the cluster, Ceph begins rebalancing
the cluster by migrating placement groups out of the OSD that was removed. To
observe this process by using the `ceph`_ tool, run the following command:

   .. prompt:: bash $

      ceph -w

The PG states will change from ``active+clean`` to ``active, some degraded
objects`` and will then return to ``active+clean`` when migration completes.
When you are finished observing, press Ctrl-C to exit.

.. note:: Under certain conditions, the action of taking ``out`` an OSD
   might lead CRUSH to encounter a corner case in which some PGs remain stuck
   in the ``active+remapped`` state. This problem sometimes occurs in small
   clusters with few hosts (for example, in a small testing cluster). To
   address this problem, mark the OSD ``in`` by running a command of the
   following form:

   .. prompt:: bash $

      ceph osd in {osd-num}

   After the OSD has come back to its initial state, do not mark the OSD
   ``out`` again. Instead, set the OSD's weight to ``0`` by running a command
   of the following form:

   .. prompt:: bash $

      ceph osd crush reweight osd.{osd-num} 0

   After the OSD has been reweighted, observe the data migration and confirm
   that it has completed successfully. The difference between marking an OSD
   ``out`` and reweighting the OSD to ``0`` has to do with the bucket that
   contains the OSD. When an OSD is marked ``out``, the weight of the bucket is
   not changed. But when an OSD is reweighted to ``0``, the weight of the
   bucket is updated (namely, the weight of the OSD is subtracted from the
   overall weight of the bucket). When operating small clusters, it can
   sometimes be preferable to use the above reweight command.


Stopping the OSD
----------------

After you take an OSD ``out`` of the cluster, the OSD might still be running.
In such a case, the OSD is ``up`` and ``out``. Before it is removed from the
cluster, the OSD must be stopped by running commands of the following form:

   .. prompt:: bash $

      ssh {osd-host}
      sudo systemctl stop ceph-osd@{osd-num}

After the OSD has been stopped, it is ``down``.


Removing the OSD
----------------

The following procedure removes an OSD from the cluster map, removes the OSD's
authentication key, removes the OSD from the OSD map, and removes the OSD from
the ``ceph.conf`` file. If your host has multiple drives, it might be necessary
to remove an OSD from each drive by repeating this procedure.

#. Begin by having the cluster forget the OSD. This step removes the OSD from
   the CRUSH map, removes the OSD's authentication key, and removes the OSD
   from the OSD map. (The :ref:`purge subcommand <ceph-admin-osd>` was
   introduced in Luminous. For older releases, see :ref:`the procedure linked
   here <ceph_osd_purge_procedure_pre_luminous>`.):

   .. prompt:: bash $

      ceph osd purge {id} --yes-i-really-mean-it


#. Navigate to the host where the master copy of the cluster's
   ``ceph.conf`` file is kept:

   .. prompt:: bash $

      ssh {admin-host}
      cd /etc/ceph
      vim ceph.conf

#. Remove the OSD entry from your ``ceph.conf`` file (if such an entry
   exists)::

    [osd.1]
        host = {hostname}

#. Copy the updated ``ceph.conf`` file from the location on the host where the
   master copy of the cluster's ``ceph.conf`` is kept to the ``/etc/ceph``
   directory of the other hosts in your cluster.

.. _ceph_osd_purge_procedure_pre_luminous:

If your Ceph cluster is older than Luminous, you will be unable to use the
``ceph osd purge`` command. Instead, carry out the following procedure:

#. Remove the OSD from the CRUSH map so that it no longer receives data (for
   more details, see `Remove an OSD`_):

   .. prompt:: bash $

      ceph osd crush remove {name}

   Instead of removing the OSD from the CRUSH map, you might opt for one of two
   alternatives: (1) decompile the CRUSH map, remove the OSD from the device
   list, and remove the device from the host bucket; (2) remove the host bucket
   from the CRUSH map (provided that it is in the CRUSH map and that you intend
   to remove the host), recompile the map, and set it:


#. Remove the OSD authentication key:

   .. prompt:: bash $

      ceph auth del osd.{osd-num}

#. Remove the OSD:

   .. prompt:: bash $

      ceph osd rm {osd-num}

   For example:

   .. prompt:: bash $

      ceph osd rm 1

.. _Remove an OSD: ../crush-map#removeosd
