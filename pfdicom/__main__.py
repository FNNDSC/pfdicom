#!/usr/bin/env python3
#
# (c) 2017 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#

import sys, os
# sys.path.insert(1, os.path.join(os.path.dirname(__file__), '../pfdicom'))

try:
    from    .               import pfdicom
    from    .               import __pkg, __version__
except:
    from pfdicom            import pfdicom
    from __init__           import __pkg, __version__


from    argparse            import RawTextHelpFormatter
from    argparse            import ArgumentParser
import  pudb

import  pfmisc
from    pfmisc._colors      import Colors
from    pfmisc              import other

import  pftree
from    pftree.__main__     import  package_CLIcore,        \
                                    package_IOcore,         \
                                    package_argSynopsisIO,  \
                                    package_argSynopsisCore,\
                                    parserIO,               \
                                    parserCore

str_desc = Colors.CYAN + """

        __    _ _
       / _|  | (_)
 _ __ | |_ __| |_  ___ ___  _ __ ___
| '_ \|  _/ _` | |/ __/ _ \| '_ ` _ \ 
| |_) | || (_| | | (_| (_) | | | | | |
| .__/|_| \__,_|_|\___\___/|_| |_| |_|
| |
|_|



                        Path-File DICOM Base Processor

        A common module/class for various downstream processing on DICOM
        files. This module reads a DICOM file, parses tags, and provides
        the data for additional processing.

                             -- version """ + \
             Colors.YELLOW + __version__ + Colors.CYAN + """ --


""" + Colors.NO_COLOUR

package_CLIself = '''
        [--outputFileStem <stem>]                                               \\'''

package_argSynopsisSelf = """
        [--outputFileStem <stem>]
        An output file stem pattern to use
"""

package_CLIfull             = package_IOcore + package_CLIself + package_CLIcore
package_argsSynopsisFull    = package_argSynopsisIO + package_argSynopsisSelf + package_argSynopsisCore

def synopsis(ab_shortOnly = False):
    scriptName = os.path.basename(sys.argv[0])
    print(scriptName)
    shortSynopsis =  """
    NAME

        pfdicom

    SYNOPSIS

        pfdicom \ """ + package_CLIfull + """

    BRIEF EXAMPLE

        pfdicom                                                                 \\
                --inputDir /var/www/html                                        \\
                --outputDir /tmp                                                \\
                --outputFile %PatientID-%PatientAge                             \\
                --fileFilter dcm                                                \\
                --printElapsedTime

    """
    description =  """
    DESCRIPTION

        ``pfdicom`` in and of itself provides minimal end value. This module/
        class is intended to be a building block for deeper functionality. Its
        purpose is to probe a given directory filesystem for DICOM files and
        construct a tree representation (using pftree), and then, for each
        directory provide the means to read in a given DICOM file (using
        pydicom) to provide some minimal tag extraction and output file
        templating.

        Most importantly, derived classes of this parent class can provide
        detailed and powerful methods to process the directories containing
        DICOM files, saving results to an output file tree.

    ARGS """ + package_argsSynopsisFull + """

    STRING PROCESSING ON TAG VALUES

    ``pfidcom`` offers some functions on tag values -- these are typically
    string based. The syntax is:

        %_<functionName>|<arg>_<tagName>

    For example,

        %_name|patientID_PatientName
        Generate a random name and replace the PatientName with this value.
        Since each DICOM file in a series could conceivably have a different
        generated random name, use the 'PatientID' tag as a seed for the name
        generator. Note that in order to protect the parsing of DICOM tags,
        if used in sub-function arguments, the tag MUST start with a lower
        case.

        %_md5|7_PatientID
        An md5 hash of the 'PatientID' is determined. Of the resultant string,
        the first 7 chars are used. This is returned as the value for the
        PatientID tag.

        %_strmsk|******01_PatientBirthDate
        The 'PatientBirthDate' value is masked such that the first six
        chars are conserved, but the final two are replaced by '01'. This
        has the effect of setting the PatientBirthDate to the first day of
        the birth month.

        %_nospc|-_ProtocolName
        The 'ProtocolName' is processed to remove all white space, and using
        a '-' character instead of any whitespace components.

    EXAMPLES

    Run on a target tree, creating internal representations of specific file
    and directory strucutres.


        pfdicom                                                                 \\
                --inputDir /var/www/html                                        \\
                --outputDir /tmp                                                \\
                --outputFile %PatientID-%PatientAge                             \\
                --fileFilter dcm                                                \\
                --printElapsedTime

    which will output only at script conclusion and will log a JSON
    formatted string.

    """.format(script=scriptName)

    if ab_shortOnly:
        return shortSynopsis
    else:
        return shortSynopsis + description

parserSelf  = ArgumentParser(description        = 'Self specific',
                             formatter_class    = RawTextHelpFormatter,
                             add_help           = False)

parserSelf.add_argument("--outputFileStem",
                    help    = "output file",
                    default = "",
                    dest    = 'outputFileStem')

parser  = ArgumentParser(description        = str_desc,
                         formatter_class    = RawTextHelpFormatter,
                         parents            = [parserCore, parserIO, parserSelf])


def earlyExit_check(args) -> int:
    """Perform some preliminary checks
    """
    if args.man or args.synopsis:
        print(str_desc)
        if args.man:
            str_help     = synopsis(False)
        else:
            str_help     = synopsis(True)
        print(str_help)
        return 1
    if args.b_version:
        print("Name:    %s\nVersion: %s" % (__pkg.name, __version__))
        return 1
    return 0

def main(argv=None):

    args = parser.parse_args()

    if earlyExit_check(args): return 1

    args.str_version    = __version__
    args.str_desc       = synopsis(True)


    # pudb.set_trace()

    pf_dicom            = pfdicom.pfdicom(vars(args))

    # And now run it!
    d_pfdicom = pf_dicom.run(timerStart = True)

    if args.printElapsedTime:
        pf_dicom.dp.qprint(
                            "Elapsed time = %f seconds" %
                            d_pfdicom['runTime']
                            )

    return 0

if __name__ == "__main__":
    sys.exit(main())