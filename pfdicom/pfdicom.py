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
import      threading

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
        self.str_outputLeafDir          = ''

        # pftree dictionary
        self.pf_tree                    = None
        self.numThreads                 = 1

        self.str_stdout                 = ''
        self.str_stderr                 = ''
        self.exitCode                   = 0

        self.b_json                     = False

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
        self.verbosityLevel             = 1

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
            if key == 'inputDir':           self.str_inputDir           = value
            if key == 'inputFile':          self.str_inputFile          = value
            if key == 'outputDir':          self.str_outputDir          = value
            if key == 'outputFileStem':     self.str_outputFileStem     = value
            if key == 'outputLeafDir':      self.str_outputLeafDir      = value
            if key == 'extension':          self.str_extension          = value
            if key == 'threads':            self.numThreads             = int(value)
            if key == 'extension':          self.str_extension          = value
            if key == 'verbosity':          self.verbosityLevel         = int(value)
            if key == 'json':               self.b_json                 = bool(value)

        # Declare pf_tree
        self.pf_tree    = pftree.pftree(
                            inputDir                = self.str_inputDir,
                            inputFile               = self.str_inputFile,
                            outputDir               = self.str_outputDir,
                            outputLeafDir           = self.str_outputLeafDir,
                            threads                 = self.numThreads,
                            verbosity               = self.verbosityLevel,
                            relativeDir             = True
        )

        # Set logging
        self.dp                        = pfmisc.debug(    
                                            verbosity   = self.verbosityLevel,
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

    def tagsInString_process(self, d_DICOM, astr, *args, **kwargs):
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

            %PatientAge-%_md5|4_PatientID-output.txt

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
            # Find which tags (mangled) in string match actual tags
            l_tagsToSub     = [i for i in d_DICOM['l_tagRaw'] if any(i in b for b in l_tags)]
            # Need to arrange l_tagsToSub in same order as l_tags
            l_tagsToSubSort =  sorted(
                l_tagsToSub, 
                key = lambda x: [i for i, s in enumerate(l_tags) if x in s][0]
            )
            for tag, func in zip(l_tagsToSubSort, l_tags):
                b_tagsFound     = True
                str_replace     = d_DICOM['d_dicomSimple'][tag]
                if 'md5' in func:
                    str_replace = hashlib.md5(str_replace.encode('utf-8')).hexdigest()
                    l_funcTag   = func.split('_')[1:]
                    func        = l_funcTag[0]
                    l_args      = func.split('|')
                    if len(l_args) > 1:
                        chars   = l_args[1]
                        str_replace     = str_replace[0:int(chars)]
                    astr = astr.replace('_%s_' % func, '')
                if 'strmsk' in func:
                    l_funcTag   = func.split('_')[1:]
                    func        = l_funcTag[0]
                    str_msk     = func.split('|')[1]
                    l_n = []
                    for i, j in zip(list(str_replace), list(str_msk)):
                        if j == '*':    l_n.append(i)
                        else:           l_n.append(j)
                    str_replace = ''.join(l_n)
                    astr = astr.replace('_%s_' % func, '')
                astr  = astr.replace('%' + tag, str_replace)
        
        return {
            'status':       True,
            'b_tagsFound':  b_tagsFound,
            'str_result':   astr
        }


    def DICOMfile_read(self, *args, **kwargs):
        """
        Read a DICOM file and perform some initial
        parsing of tags.

        NB!
        For thread safety, class member variables
        should not be assigned since other threads
        might override/change these variables in mid-
        flight!

        """
        b_status        = False
        l_tags          = []
        l_tagsToUse     = []
        d_tagsInString  = {}
        str_file        = ""

        d_DICOM           = {
            'dcm':              None,
            'd_dcm':            {},
            'strRaw':           '',
            'l_tagRaw':         [],
            'd_json':           {},
            'd_dicom':          {},
            'd_dicomSimple':    {}
        }

        for k, v in kwargs.items():
            if k == 'file':             str_file    = v
            if k == 'l_tagsToUse':      l_tags      = v

        if len(args):
            l_file          = args[0]
            str_file        = l_file[0]

        str_localFile   = os.path.basename(str_file)
        str_path        = os.path.dirname(str_file)
        # self.dp.qprint("%s: In input base directory:      %s" % (threading.currentThread().getName(), self.str_inputDir))
        # self.dp.qprint("%s: Reading DICOM file in path:   %s" % (threading.currentThread().getName(),str_path))
        # self.dp.qprint("%s: Analysing tags on DICOM file: %s" % (threading.currentThread().getName(),str_localFile))      
        # self.dp.qprint("%s: Loading:                      %s" % (threading.currentThread().getName(),str_file))

        try:
            # self.dcm    = dicom.read_file(str_file)
            d_DICOM['dcm']  = dicom.read_file(str_file)
            b_status    = True
        except:
            self.dp.qprint('In directory: %s' % os.getcwd(),    comms = 'error')
            self.dp.qprint('Failed to read %s' % str_file,      comms = 'error')
            b_status    = False
        d_DICOM['d_dcm']    = dict(d_DICOM['dcm'])
        d_DICOM['strRaw']   = str(d_DICOM['dcm'])
        d_DICOM['l_tagRaw'] = d_DICOM['dcm'].dir()

        if len(l_tags):
            l_tagsToUse     = l_tags
        else:
            l_tagsToUse     = d_DICOM['l_tagRaw']

        if 'PixelData' in l_tagsToUse:
            l_tagsToUse.remove('PixelData')

        for key in l_tagsToUse:
            d_DICOM['d_dicom'][key]       = d_DICOM['dcm'].data_element(key)
            try:
                d_DICOM['d_dicomSimple'][key] = getattr(d_DICOM['dcm'], key)
            except:
                d_DICOM['d_dicomSimple'][key] = "no attribute"
            d_DICOM['d_json'][key]        = str(d_DICOM['d_dicomSimple'][key])

        # pudb.set_trace()
        d_tagsInString  = self.tagsInString_process(d_DICOM, self.str_outputFileStem)
        str_outputFile  = d_tagsInString['str_result']

        return {
            'status':           b_status,
            'inputPath':        str_path,
            'inputFilename':    str_localFile,
            'outputFileStem':   str_outputFile,
            'd_DICOM':          d_DICOM,
            'l_tagsToUse':      l_tagsToUse
        }

    def filelist_prune(self, at_data, *args, **kwargs):
        """
        Given a list of files, possibly prune list by 
        extension.
        """
        al_file = at_data[1]
        if len(self.str_extension):
            al_file = [x for x in al_file if self.str_extension in x]
        return {
            'status':   True,
            'l_file':   al_file
        }

    def ret_dump(self, d_ret, **kwargs):
        """
        JSON print results to console (or caller)
        """
        b_print     = True
        for k, v in kwargs.items():
            if k == 'JSONprint':    b_print     = bool(v)
        if b_print:
            print(
                json.dumps(   
                    d_ret, 
                    indent      = 4,
                    sort_keys   = True
                )
        )

    def run(self, *args, **kwargs):
        """
        The run method is merely a thin shim down to the 
        embedded pftree run method.
        """
        b_status            = True
        d_pftreeRun         = {}
        d_inputAnalysis     = {}
        d_env               = self.env_check()
        b_timerStart        = False

        self.dp.qprint(
                "\tStarting pfdicom run... (please be patient while running)", 
                level = 1
                )

        for k, v in kwargs.items():
            if k == 'timerStart':   b_timerStart    = bool(v)

        if b_timerStart:
            other.tic()

        if d_env['status']:
            d_pftreeRun = self.pf_tree.run(timerStart = False)
        else:
            b_status    = False 

        str_startDir    = os.getcwd()
        os.chdir(self.str_inputDir)
        if b_status:
            if len(self.str_extension):
                d_inputAnalysis = self.pf_tree.tree_process(
                                inputReadCallback       = None,
                                analysisCallback        = self.filelist_prune,
                                outputWriteCallback     = None,
                                applyResultsTo          = 'inputTree',
                                applyKey                = 'l_file',
                                persistAnalysisResults  = True
                )
        os.chdir(str_startDir)

        d_ret = {
            'status':           b_status and d_pftreeRun['status'],
            'd_env':            d_env,
            'd_pftreeRun':      d_pftreeRun,
            'd_inputAnalysis':  d_inputAnalysis,
            'runTime':          other.toc()
        }

        if self.b_json:
            self.ret_dump(d_ret, **kwargs)

        self.dp.qprint('\tReturning from pfdicom run...', level = 1)

        return d_ret
        
