# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import base64
import hashlib
import datetime
import random

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.ReadsUtilsClient import ReadsUtils
from base import Core

from .est.est_generate import EstGenerateJob
from .est.est_analysis import EstAnalysisJob

#END_HEADER


class kbase_efi_tools_module:
    '''
    Module Name:
    kbase_efi_tools_module

    Module Description:
    A KBase module: kbase_efi_tools_module
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/nilsoberg2@EnzymeFunctionInitiative/kbase_efi_tools_module.git"
    GIT_COMMIT_HASH = "2a282d55578c53b51df8fd7c9868cfa6d8eb475c"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch'] + "/job"
        #now = datetime.datetime.now()
        #suffix = now.strftime("%Y%m%dT%H.%M.%S.r") + str(random.randrange(1000))
        #self.shared_folder = config['scratch'] + "/job_" + suffix
        if not os.path.isdir(self.shared_folder):
            os.mkdir(self.shared_folder)
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s', level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_est_generate_app(self, ctx, params):
        """
        mapping<string,UnspecifiedObject> params
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_est_generate_app

        is_valid = EstGenerateJob.validate_params(params)

        config = dict(
            callback_url=self.callback_url,
            shared_folder=self.shared_folder,
            clients=dict(
                KBaseReport=KBaseReport,
            ),
        )

        db_conf = params.get('efi_db_config')
        if db_conf != None:
            config['efi_db_config'] = db_conf
        est_conf = params.get('efi_est_config')
        if est_conf != None:
            config['efi_est_config'] = est_conf

        job = EstGenerateJob(ctx, config)

        job.create_job(params)

        job.start_job()

        output = job.generate_report(params)

        #END run_est_generate_app

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_est_generate_app return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_est_analysis_app(self, ctx, results):
        """
        :param results: instance of type "GenerateResults" (* The output of
           the first step in creating an SSN (i.e. "generate"). * Contains a
           File and a job label. Also serves as input to the * Analysis
           module. * Returned data: *     File gen_file - A File object (can
           be defined multiple ways) *     string label - Label of job name)
           -> structure: parameter "gen_file" of type "File" -> structure:
           parameter "path" of String, parameter "shock_id" of String,
           parameter "name" of String, parameter "label" of String, parameter
           "description" of String, parameter "label" of String
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_est_analysis_app

        

        #END run_est_analysis_app

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_est_analysis_app return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
