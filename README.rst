pfdicom
=======

.. image:: https://badge.fury.io/py/pfdicom.svg
    :target: https://badge.fury.io/py/pfdicom

.. image:: https://travis-ci.org/FNNDSC/pfdicom.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/pfdicom

.. image:: https://img.shields.io/badge/python-3.5%2B-blue.svg
    :target: https://badge.fury.io/py/pfdicom

.. contents:: Table of Contents

Quick Overview
--------------

-  ``pfdicom`` is primarily a base module for other, more specialized classes. It typically is never used on its own.

Overview
--------

``pfdicom`` in and of itself provides minimal end value. This module/class is intended to be a building block for deeper functionality. Its purpose is to probe a given directory filesystem for DICOM files and construct a tree representation (using pftree), and then, for each directory provide the means to read in a given DICOM file (using pydicom) to provide some minimal tag extraction and output file templating.

Most importantly, derived classes of this parent class can provide detailed and powerful methods to process the directories containing DICOM files, saving results to an output file tree. For example, various modules are built off this chassis, including ``pfdicom_tagExtract`` and ``pfdicom_tagSub``.

Installation
------------

Dependencies
~~~~~~~~~~~~

The following dependencies are installed on your host system/python3 virtual env (they will also be automatically installed if pulled from pypi):

-  ``pfmisc`` (various misc modules and classes for the pf* family of objects)
-  ``pftree`` (create a dictionary representation of a filesystem hierarchy)

Using ``PyPI``
~~~~~~~~~~~~~~

The best method of installing this script and all of its dependencies is
by fetching it from PyPI

.. code:: bash

        pip3 install pfdicom

Command line arguments
----------------------

.. code:: html

        --inputDir <inputDir>
        Input directory to examine. The downstream nested structure of this
        directory is examined and recreated in the <outputDir>.

        [--outputDir <outputDir>]
        The directory to contain a tree structure identical to the input
        tree structure, and which contains all output files from the
        per-input-dir processing.

        [--outputFileStem <stem>]
        An output file stem pattern to use


        [--maxdepth <dirDepth>]
        The maximum depth to descend relative to the <inputDir>. Note, that
        this counts from zero! Default of '-1' implies transverse the entire
        directory tree.

        [--relativeDir]
        A flag argument. If passed (i.e. True), then the dictionary key values
        are taken to be relative to the <inputDir>, i.e. the key values
        will not contain the <inputDir>; otherwise the key values will
        contain the <inputDir>.

        [--inputFile <inputFile>]
        An optional <inputFile> specified relative to the <inputDir>. If
        specified, then do not perform a directory walk, but target this
        specific file.

        [--fileFilter <someFilter1,someFilter2,...>]
        An optional comma-delimated string to filter out files of interest
        from the <inputDir> tree. Each token in the expression is applied in
        turn over the space of files in a directory location according to a
        logical operation, and only files that contain this token string in
        their filename are preserved.

        [--filteFilterLogic AND|OR]
        The logical operator to apply across the fileFilter operation. Default
        is OR.

        [--dirFilter <someFilter1,someFilter2,...>]
        An additional filter that will further limit any files to process to
        only those files that exist in leaf directory nodes that have some
        substring of each of the comma separated <someFilter> in their
        directory name.

        [--dirFilterLogic AND|OR]
        The logical operator to apply across the dirFilter operation. Default
        is OR.

        [--outputLeafDir <outputLeafDirFormat>]
        If specified, will apply the <outputLeafDirFormat> to the output
        directories containing data. This is useful to blanket describe
        final output directories with some descriptive text, such as
        'anon' or 'preview'.

        This is a formatting spec, so

            --outputLeafDir 'preview-%%s'

        where %%s is the original leaf directory node, will prefix each
        final directory containing output with the text 'preview-' which
        can be useful in describing some features of the output set.

        [--threads <numThreads>]
        If specified, break the innermost analysis loop into <numThreads>
        threads. Please note the following caveats:

            * Only thread if you have a high CPU analysis loop. Note that
              the input file read and output file write loops are not
              threaded -- only the analysis loop is threaded. Thus, if the
              bulk of execution time is in file IO, threading will not
              really help.

            * Threading will change the nature of the innermost looping
              across the problem domain, with the result that *all* of the
              problem data will be read into memory! That means potentially
              all the target input file data across the entire input directory
              tree.

        [--json]
        If specified, do a JSON dump of the entire return payload.

        [--followLinks]
        If specified, follow symbolic links.

        [--overwrite]
        If specified, allow for overwriting of existing files

        [--man]
        Show full help.

        [--synopsis]
        Show brief help.

        [--verbosity <level>]
        Set the app verbosity level. This ranges from 0...<N> where internal
        log messages with a level=<M> will only display if M <= N. In this
        manner increasing the level here can be used to show more and more
        debugging info, assuming that debug messages in the code have been
        tagged with a level.


String processing on tag values
-------------------------------

``pfidcom`` offers some functions on tag values -- these are typically string based. The syntax is:

.. code:: html

        %_<functionName>|<arg>_<tagName>

For example, 

.. code:: html

        %_name|patientID_PatientName


Generate a random name and replace the PatientName with this value. Since each DICOM file in a series could conceivably have a different generated random name, use the 'PatientID' tag as a seed for the name generator. Note that in order to protect the parsing of DICOM tags, if used in sub-function arguments, the tag MUST start with a lower case.

.. code:: html

        %_md5|7_PatientID

An md5 hash of the ``PatientID`` is determined. Of the resultant string, the first 7 chars are used. This is returned as the value for the ``PatientID`` tag.

.. code:: bash

        %_strmsk|******01_PatientBirthDate

The ``PatientBirthDate`` value is masked such that the first six chars are conserved, but the final two are replaced by '01'. This  has the effect of setting the ``PatientBirthDate`` to the first day of the birth month.

.. code:: html

        %_nospc|-_ProtocolName

The ``ProtocolName`` is processed to remove all white space, and using a '-' character instead of any whitespace components.

Examples
--------

Run on a target tree, creating internal representations of specific file and directory strucutres:

.. code:: bash

        pfdicom                                                                 \
                --inputDir ~/dicom                                              \
                --outputDir /tmp                                                \
                --fileFilter dcm                                                \
                --printElapsedTime

other than setting up some internal variables, this will do little more than a pftree walk down the tree. This will typically be the first call executed by downstream modules that might extract tags or anonymize DICOM contents.
