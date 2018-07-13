pfdicom
=======

Quick Overview
--------------

-  pfdicom is primarily a base module for other, more specialized classes. It typically is never used on its own.

Overview
--------

pfdicom in and of itself provides minimal end value. This module/class is intended to be a building block for deeper functionality. Its purpose is to probe a given directory filesystem for DICOM files and construct a tree representation (using pftree), and then, for each directory provide the means to read in a given DICOM file (using pydicom) to provide some minimal tag extraction and output file templating.

Most importantly, derived classes of this parent class can provide detailed and powerful methods to process the directories containing DICOM files, saving results to an output file tree.


Dependencies
------------

The following dependencies are installed on your host system/python3 virtual env (they will also be automatically installed if pulled from pypi):

-  pfmisc (various misc modules and classes for the pf* family of objects)
-  pftree (create a dictionary representation of a filesystem hierarchy)

Installation
~~~~~~~~~~~~

The best method of installing this script and all of its dependencies is
by fetching it from PyPI

.. code:: bash

        pip3 install pfdciom



Command line arguments
----------------------

.. code:: html

        -I|--inputDir <inputDir>
        Input DICOM directory to examine. By default, the first file in this
        directory is examined for its tag information. There is an implicit
        assumption that each <inputDir> contains a single DICOM series.

        -i|--inputFile <inputFile>
        An optional <inputFile> specified relative to the <inputDir>. If 
        specified, then do not perform a directory walk, but convert only 
        this file.

        [-O|--outputDir <outputDir>]
        The directory to contain all output files.

        -e|--extension <DICOMextension>
        An optional extension to filter the DICOM files of interest from the 
        <inputDir>.

        [-x|--man]
        Show full help.

        [-y|--synopsis]
        Show brief help.

        -v|--verbosity <level>
        Set the app verbosity level. 

             -1: No internal output.
              0: All internal output.


Examples
~~~~~~~~

Run on a target tree and output some detail and stats

.. code:: bash

        pfdicom         -I /var/www/html                \
                        -O /tmp                         \
                        -o %PatientID-%PatientAge       \
                        --printElapsedTime              

