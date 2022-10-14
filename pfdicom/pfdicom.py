# System imports
import      os
import      getpass
import      argparse
import      json
import      pprint
import      re
from        faker               import  Faker
import      math
import      logging

# Project specific imports
import      pfmisc
from        pfmisc._colors      import  Colors
from        pfmisc              import  other
from        pfmisc              import  error

import      pydicom             as      dicom

from        pftree              import  pftree

try:
    from    .                   import __name__, __version__
except:
    from    __init__            import __name__, __version__


import      pudb
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

    # Turn off logging for the 'faker' module and create a class instance
    # of the object
    fakelogger              = logging.getLogger('faker')
    fakelogger.propagate    = False
    fake                    = Faker()

    def declare_selfvars(self):
        """
        A block to declare self variables
        """

        #
        # Object desc block
        #
        self.str_desc                   = ''
        self.__name__                   = __name__
        self.str_version                = __version__

        # pftree dictionary
        self.pf_tree                    = pftree.pftree(self.args)

        self.dp                         = None
        self.log                        = None
        self.tic_start                  = 0.0
        self.pp                         = pprint.PrettyPrinter(indent=4)
        self.verbosityLevel             = 1

    def __init__(self, *args, **kwargs):
        """
        A "base" class for all pfdicom objects. This class is typically never
        called/used directly; derived classes are used to provide actual end
        functionality.

        This class really only reads in a DICOM file, and populates some
        internal convenience member variables.

        Furthermore, this class does not have a concept nor concern about
        "output" relations.
        """

        def outputDir_process(str_outputDir):
            if str_outputDir == '%inputDir':
                self.str_outputDir  = self.str_inputDir
            else:
                self.str_outputDir  = str_outputDir

        # pudb.set_trace()
        # The 'self' isn't fully instantiated, so
        # we call the following method on the class
        # directly.
        pfdicom.declare_selfvars(self)
        self.args                       = args[0]
        self.str_desc                   = self.args['str_desc']
        if len(self.args):
            kwargs  = {**self.args, **kwargs}

        for key, value in kwargs.items():
            if key == 'inputDir':           self.str_inputDir           = value
            if key == 'maxDepth':           self.maxDepth               = int(value)
            if key == 'inputFile':          self.str_inputFile          = value
            if key == "outputDir":          outputDir_process(value)
            if key == 'outputFileStem':     self.str_outputFileStem     = value
            if key == 'outputLeafDir':      self.str_outputLeafDir      = value
            if key == 'extension':          self.str_extension          = value
            if key == 'threads':            self.numThreads             = int(value)
            if key == 'extension':          self.str_extension          = value
            if key == 'verbosity':          self.verbosityLevel         = int(value)
            if key == 'json':               self.b_json                 = bool(value)
            if key == 'followLinks':        self.b_followLinks          = bool(value)

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
        environment specific to this module. Note that basic env
        checks are already performed via the `pftree` delegate.
        """
        b_status    = True
        str_error   = ''

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

        def md5_process(func, str_replace):
            """
            md5 mangle the <str_replace>.
            """
            nonlocal    astr
            l_funcTag   = []        # a function/tag list
            l_args      = []        # the 'args' of the function
            chars       = ''        # the number of resultant chars from func
                                    # result to use
            str_replace = hashlib.md5(str_replace.encode('utf-8')).hexdigest()
            l_funcTag   = func.split('_')[1:]
            func        = l_funcTag[0]
            l_args      = func.split('|')
            if len(l_args) > 1:
                chars   = l_args[1]
                str_replace     = str_replace[0:int(chars)]
            astr        = astr.replace('_%s_' % func, '')
            return astr, str_replace

        def strmsk_process(func, str_replace):
            """
            string mask
            """
            nonlocal    astr
            l_funcTag   = []        # a function/tag list
            l_funcTag   = func.split('_')[1:]
            func        = l_funcTag[0]
            str_msk     = func.split('|')[1]
            l_n = []
            for i, j in zip(list(str_replace), list(str_msk)):
                if j == '*':    l_n.append(i)
                else:           l_n.append(j)
            str_replace = ''.join(l_n)
            astr        = astr.replace('_%s_' % func, '')
            return astr, str_replace

        def nospc_process(func, str_replace):
            """
            replace spaces in string
            """
            nonlocal    astr
            l_funcTag   = []        # a function/tag list
            l_args      = []        # the 'args' of the function
            l_funcTag   = func.split('_')[1:]
            func        = l_funcTag[0]
            l_args      = func.split('|')
            str_char    = ''
            if len(l_args) > 1:
                str_char = l_args[1]
            # strip out all non-alphnumeric chars and
            # replace with space
            str_replace = re.sub(r'\W+', ' ', str_replace)
            # replace all spaces with str_char
            str_replace = str_char.join(str_replace.split())
            astr        = astr.replace('_%s_' % func, '')
            return astr, str_replace

        def convertToNumber (s):
            return int.from_bytes(s.encode(), 'little')

        def convertFromNumber (n):
            return n.to_bytes(math.ceil(n.bit_length() / 8), 'little').decode()

        def name_process(func, str_replace):
            """
            replace str_replace with a name

            Note this sub-function can take as an argument a DICOM tag, which
            is then used to seed the name caller. This assures that all
            DICOM files belonging to the same series (or that have the same
            DICOM tag value passed as argument) all get the same 'name'.

            NB: If a DICOM tag is passed as an argument, the first character
            of the tag must be lower case to protect parsing of any non-arg
            DICOM tags.
            """
            # pudb.set_trace()
            nonlocal    astr, d_DICOM
            l_funcTag   = []        # a function/tag list
            l_args      = []        # the 'args' of the function
            l_funcTag   = func.split('_')[1:]
            func        = l_funcTag[0]
            l_args      = func.split('|')
            if len(l_args) > 1:
                str_argTag  = l_args[1]
                str_argTag  = re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), str_argTag, 1)
                if str_argTag in d_DICOM['d_dicomSimple']:
                    str_seed    = d_DICOM['d_dicomSimple'][str_argTag]
                    randSeed    = convertToNumber(str_seed)
                    Faker.seed(randSeed)
            str_firstLast   = pfdicom.fake.name()
            l_firstLast     = str_firstLast.split()
            str_first       = l_firstLast[0]
            str_last        = l_firstLast[1]
            str_replace     = '%s^%s^ANON' % (str_last.upper(), str_first.upper())
            astr            = astr.replace('_%s_' % func, '')
            return astr, str_replace

        b_tagsFound         = False
        str_replace         = ''        # The lookup/processed tag value
        l_tags              = []        # The input string split by '%'
        l_tagsToSub         = []        # Remove any noise etc from each tag
        func                = ''        # the function to apply
        tag                 = ''        # the tag in the funcTag combo

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
                if 'md5'    in func: astr, str_replace   = md5_process(func, str_replace)
                if 'strmsk' in func: astr, str_replace   = strmsk_process(func, str_replace)
                if 'nospc'  in func: astr, str_replace   = nospc_process(func, str_replace)
                if 'name'   in func: astr, str_replace   = name_process(func, str_replace)
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

        def dcmToStr_doExplicit(d_dcm):
            """
            Perform an explicit element by element conversion on dictionary
            of dcm FileDataset
            """
            b_status = True
            self.dp.qprint('In directory: %s' % os.getcwd(),     comms = 'error')
            self.dp.qprint('Failed to str convert %s' % str_file,comms = 'error')
            self.dp.qprint('Possible source corruption or non standard tag',
                            comms = 'error')
            self.dp.qprint('Attempting explicit string conversion...',
                            comms = 'error')
            l_k         = list(d_dcm.keys())
            str_raw     = ''
            str_err     = ''
            for k in l_k:
                try:
                    str_raw += str(d_dcm[k])
                    str_raw += '\n'
                except:
                    str_err = 'Failed to string convert key "%s"' % k
                    str_raw += str_err + "\n"
                    self.dp.qprint(str_err, comms = 'error')
                    b_status = False
            return str_raw, b_status

        b_status        = False
        l_tags          = []
        l_tagsToUse     = []
        d_tagsInString  = {}
        str_file        = ""
        str_outputFile  = ""

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

        try:
            d_DICOM['dcm']  = dicom.read_file(str_file)
            b_status        = True
        except:
            self.dp.qprint('In directory: %s' % os.getcwd(),    comms = 'error')
            self.dp.qprint('Failed to read %s' % str_file,      comms = 'error')
            b_status        = False
        if b_status:
            d_DICOM['l_tagRaw'] = d_DICOM['dcm'].dir()
            d_DICOM['d_dcm']    = dict(d_DICOM['dcm'])
            try:
                d_DICOM['strRaw']   = str(d_DICOM['dcm'])
            except:
                d_DICOM['strRaw'], b_status = dcmToStr_doExplicit(d_DICOM['d_dcm'])

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

    def ret_jdump(self, d_ret, **kwargs):
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
        b_status            : bool  = True
        d_env               : dict  = {}
        b_timerStart        : bool  = False
        d_pftreeProbe       : dict  = {}
        d_pftreeRun         : dict  = {}
        b_JSONprint         : bool  = True

        self.dp.qprint(
                "\tStarting pfdicom run... (please be patient while running)",
                level = 1
                )

        for k, v in kwargs.items():
            if k == 'timerStart':   b_timerStart    = bool(v)
            if k == 'JSONprint':    b_JSONprint     = bool(v)

        if b_timerStart:
            other.tic()

        d_env               = self.env_check()
        if d_env['status']:
            d_pftreeRun = self.pf_tree.run(timerStart = False)
        else:
            b_status    = False

        d_ret = {
            'status':           b_status and d_pftreeRun['status'],
            'd_env':            d_env,
            'd_pftreeRun':      d_pftreeRun,
            'runTime':          other.toc()
        }

        if self.args['json'] and b_JSONprint:
            self.ret_jdump(d_ret, **kwargs)
        else:
            self.dp.qprint('\tReturning from pfdicom run...', level = 1)

        return d_ret

