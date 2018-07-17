# System imports
import      os
import      getpass
import      argparse
import      json
import      pprint

# Project specific imports
import      pfmisc
from        pfmisc._colors      import  Colors
from        pfmisc              import  other
from        pfmisc              import  error

import      pydicom             as      dicom

import      pudb
import      pftree
import      hashlib

class pfdicom(object):
    """
    The 'pfdicom' class essentially just wraps around a pydicom
    object instance and provides access to some member variables.
    This class really only reads in a DICOM file, and populates some
    internal convenience member variables.

    It is simply a common "base" class for all pfdicom objects. 
    and is typically never called/used directly; derived classes
    are used to provide actual end functionality.

    Furthermore, this class does not have a concept nor concern about 
    "output" relations.

    """

    _dictErr = {
        'outputDirFail'   : {
            'action'        : 'trying to check on the output directory, ',
            'error'         : 'directory not specified. This is a *required* input',
            'exitCode'      : 1}
        }


    def declare_selfvars(self):
        """
        A block to declare self variables
        """

        #
        # Object desc block
        #
        self.str_desc                   = ''
        self.__name__                   = "pfdicom"

        # Directory and filenames
        self.str_workingDir             = ''
        self.str_inputDir               = ''
        self.str_inputFile              = ''
        self.str_extension              = ''
        self.str_outputFileStem         = ''
        self.str_ouptutDir              = ''

        # pftree dictionary
        self.pf_tree                    = None

        self.str_stdout                 = ''
        self.str_stderr                 = ''
        self.exitCode                   = 0

        # The actual data volume and slice
        # are numpy ndarrays
        self.dcm                        = None
        self.d_dcm                      = {}     # dict convert of raw dcm
        self.strRaw                     = ""
        self.l_tagRaw                   = []

        # Simpler dictionary representations of DICOM tags
        # NB -- the pixel data is not read into the dictionary
        # by default
        self.d_dicom                   = {}     # values directly from dcm ojbect
        self.d_dicomSimple             = {}     # formatted dict convert

        # Convenience vars
        self.tic_start                  = None

        self.dp                         = None
        self.log                        = None
        self.tic_start                  = 0.0
        self.pp                         = pprint.PrettyPrinter(indent=4)
        self.verbosityLevel             = -1

    def __init__(self, **kwargs):
        """
        A "base" class for all pfdicom objects. This class is typically never 
        called/used directly; derived classes are used to provide actual end
        functionality.

        This class really only reads in a DICOM file, and populates some
        internal convenience member variables.

        Furthermore, this class does not have a concept nor concern about 
        "output" relations.
        """

        # pudb.set_trace()
        self.declare_selfvars()

        for key, value in kwargs.items():
            if key == "inputDir":           self.str_inputDir          = value
            if key == "inputFile":          self.str_inputFile         = value
            if key == "outputDir":          self.str_outputDir         = value
            if key == "outputFileStem":     self.str_outputFileStem    = value
            if key == "extension":          self.str_extension         = value
            if key == 'verbosity':          self.verbosityLevel         = int(value)

        # Declare pf_tree
        self.pf_tree    = pftree.pftree(
                            inputDir                = self.str_inputDir,
                            inputFile               = self.str_inputFile,
                            outputDir               = self.str_outputDir,
                            verbosity               = self.verbosityLevel,
                            relativeDir             = True
        )

        # Set logging
        self.dp                        = pfmisc.debug(    
                                            verbosity   = self.verbosityLevel,
                                            level       = 0,
                                            within      = self.__name__
                                            )
        self.log                       = pfmisc.Message()
        self.log.syslog(True)

    def env_check(self, *args, **kwargs):
        """
        This method provides a common entry for any checks on the 
        environment (input / output dirs, etc)
        """
        b_status    = True
        str_error   = ''
        if not len(self.str_outputDir): 
            b_status = False
            str_error   = 'output directory not specified.'
            self.dp.qprint(str_error, comms = 'error')
            error.warn(self, 'outputDirFail', drawBox = True)
        return {
            'status':       b_status,
            'str_error':    str_error
        }

    def tagsInString_process(self, astr, *args, **kwargs):
        """
        This method substitutes DICOM tags that are '%'-tagged
        in a string template with the actual tag lookup.

        For example, an output filename that is specified as the
        following string:

            %PatientAge-%PatientID-output.txt

        will be parsed to

            006Y-4412364-ouptut.txt

        It is also possible to apply certain permutations/functions
        to a tag. For example, a function is identified by an underscore
        prefixed and suffixed string as part of the DICOM tag. If
        found, this function is applied to the tag value. For example,

            %PatientAge-%_md5.4_PatientID-output.txt

        will apply an md5 hash to the PatientID and use the first 4
        characters:

            006Y-7f38-output.txt

        """
        b_tagsFound         = False
        str_replace         = ''        # The lookup/processed tag value
        l_tags              = []        # The input string split by '%'
        l_tagsToSub         = []        # Remove any noise etc from each tag
        l_funcTag           = []        # a function/tag list
        l_args              = []        # the 'args' of the function
        func                = ''        # the function to apply
        tag                 = ''        # the tag in the funcTag combo
        chars               = ''        # the number of resultant chars from func
                                        # result to use

        if '%' in astr:
            l_tags          = astr.split('%')[1:]
            l_tagsToSub     = [i for i in self.l_tagRaw if any(i in b for b in l_tags)]
            for tag, func in zip(l_tagsToSub, l_tags):
                b_tagsFound     = True
                str_replace     = self.d_dicomSimple[tag]
                if 'md5' in func:
                    str_replace = hashlib.md5(str_replace.encode('utf-8')).hexdigest()
                    l_funcTag   = func.split('_')[1:]
                    func        = l_funcTag[0]
                    l_args      = func.split('.')
                    if len(l_args) > 1:
                        chars   = l_args[1]
                        str_replace     = str_replace[0:int(chars)]
                    astr = astr.replace('_%s_' % func, '')
                astr  = astr.replace('%' + tag, str_replace)
        
        return {
            'status':       True,
            'b_tagsFound':  b_tagsFound,
            'str_result':   astr
        }


    def DICOMfile_read(self, *args, **kwargs):
        b_status        = False
        l_tags          = []
        l_tagsToUse     = []
        d_tagsInString  = {}
        str_file        = ""

        for k, v in kwargs.items():
            if k == 'file':             str_file    = v
            if k == 'l_tagsToUse':      l_tags      = v

        if len(args):
            l_file          = args[0]
            str_file        = l_file[0]

        str_localFile   = os.path.basename(str_file)
        str_path        = os.path.dirname(str_file)
        # self.dp.qprint("In input base directory:      %s" % self.str_inputDir)
        # self.dp.qprint("Reading DICOM file in path:   %s" % str_path)
        # self.dp.qprint("Analysing tags on DICOM file: %s" % str_localFile)      
        try:
            self.dcm    = dicom.read_file(str_file)
            b_status    = True
        except:
            b_status    = False
        self.d_dcm      = dict(self.dcm)
        self.strRaw     = str(self.dcm)
        self.l_tagRaw   = self.dcm.dir()

        if len(l_tags):
            l_tagsToUse     = l_tags
        else:
            l_tagsToUse     = self.l_tagRaw

        if 'PixelData' in l_tagsToUse:
            l_tagsToUse.remove('PixelData')

        d_dicomJSON     = {}
        for key in l_tagsToUse:
            self.d_dicom[key]       = self.dcm.data_element(key)
            try:
                self.d_dicomSimple[key] = getattr(self.dcm, key)
            except:
                self.d_dicomSimple[key] = "no attribute"
            d_dicomJSON[key]        = str(self.d_dicomSimple[key])

        # pudb.set_trace()
        d_tagsInString  = self.tagsInString_process(self.str_outputFileStem)
        str_outputFile  = d_tagsInString['str_result']

        return {
            'status':           b_status,
            'inputPath':        str_path,
            'inputFilename':    str_localFile,
            'outputFileStem':   str_outputFile,
            'd_dicomJSON':      d_dicomJSON,
            'l_tagsToUse':      l_tagsToUse
        }

    def run(self, *args, **kwargs):
        """
        The run method is merely a thin shim down to the 
        embedded pftree run method.
        """
        b_status    = True
        d_pftreeRun = {}

        d_env       = self.env_check()
        if d_env['status']:
            d_pftreeRun = self.pf_tree.run()
        else:
            b_status    = False 

        return {
            'status':       b_status and d_pftreeRun['status'],
            'd_env':        d_env,
            'd_pftreeRun':  d_pftreeRun
        }
        