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

        -I|--inputDir <inputDir>
        Input DICOM directory to examine. By default, the first file in this
        directory is examined for its tag information. There is an implicit
        assumption that each <inputDir> contains a single DICOM series.

        [--maxdepth <dirDepth>]
        The maximum depth to descend relative to the <inputDir>. Note, that
        this counts from zero! Default of '-1' implies transverse the entire
        directory tree.

        -i|--inputFile <inputFile>
        An optional <inputFile> specified relative to the <inputDir>. If 
        specified, then do not perform a directory walk, but convert only 
        this file.

        [-O|--outputDir <outputDir>]
        The directory to contain all output files.

        [-O|--outputDir <outputDir>]
        The directory to contain all output files.

        [--outputLeafDir <outputLeafDirFormat>]
        If specified, will apply the <outputLeafDirFormat> to the output
        directories containing data. This is useful to blanket describe
        final output directories with some descriptive text, such as 
        'anon' or 'preview'. 

        This is a formatting spec, so 

            --outputLeafDir 'preview-%s'

        where %s is the original leaf directory node, will prefix each
        final directory containing output with the text 'preview-' which
        can be useful in describing some features of the output set.

        -e|--extension <DICOMextension>
        An optional extension to filter the DICOM files of interest from the 
        <inputDir>.

        [-t|--threads <numThreads>]
        If specified, break the innermost analysis loop into <numThreads>
        threads. Please note the following caveats:

            * Only thread if you have a high CPU analysis loop. Since
              most of the operations of this module will entail reading
              and writing DICOM files, and since these operations are 
              the bulk of the execution time, adding threading will not
              really help.

            * Threading will change the nature of the innermost looping
              across the problem domain, with the result that *all* of the
              problem data will be read into memory! That means all of 
              DICOMs across all of the subdirs! In non-threading mode,
              only DICOMs from a single directory at a time are read
              and then discarded.

        This flag is less applicable to this base class. It is here
        to provide fall-through compatibility with derived classes.

        [-x|--man]
        Show full help.

        [-y|--synopsis]
        Show brief help.

        [--json]
        If true, dump the final return as JSON formatted string.

        [--followLinks]
        If specified, follow symbolic links.

        [--version]
        If specified, print a version string.

        -v|--verbosity <level>
        Set the app verbosity level. 

            0: No internal output;
            1: Most important internal output -- none for 'pfdicom';
            2: As with level '1' but with simpleProgress bar in 'pftree';
            3: As with level '2' but with list of input dirs/files in 'pftree';

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

Run on a target tree, creating internal representations of specific file and directory strucutres.

.. code:: bash

        pfdicom         -I /var/www/html                \
                        -O /tmp                         \
                        -o %PatientID-%PatientAge       \
                        -e .dcm                         \
                        -v 0 --json

        which will output only at script conclusion and will log a JSON formatted string.

