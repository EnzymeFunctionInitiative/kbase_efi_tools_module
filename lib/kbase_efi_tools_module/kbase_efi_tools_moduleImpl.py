# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import base64
import hashlib
import datetime
import random

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.WorkspaceClient import Workspace
from installed_clients.ReadsUtilsClient import ReadsUtils
from base import Core

from .est.est_generate import KbEstGenerateJob
from .est.est_generate import EstGenerateJob
from .est.est_analysis import KbEstAnalysisJob

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
    VERSION = "0.0.5"
    GIT_URL = "https://github.com/EnzymeFunctionInitiative/kbase_efi_tools_module.git"
    GIT_COMMIT_HASH = "2554958b45def35d796f467e015068beffb4e6b1"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch'] + "/job"
        self.token = os.environ['KB_AUTH_TOKEN']
        self.config = config
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
        typedef structure {
        string workspace_name;
        int workspace_id;
        string job_name;
        mapping<string, UnspecifiedObject> option_blast;
        mapping<string, UnspecifiedObject> option_family;
        mapping<string, UnspecifiedObject> option_fasta;
        mapping<string, UnspecifiedObject> option_accession;
        } EfiEstAppParams;
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_est_generate_app

        is_valid = EstGenerateJob.validate_params(params)

        shared_folder = params.get('output_dir', self.shared_folder)
        config = dict(
            callback_url = self.callback_url,
            shared_folder = shared_folder,
            clients = dict(
                KBaseReport = KBaseReport(self.callback_url, token = self.token),
                DataFileUtil = DataFileUtil(self.callback_url, token = self.token),
                Workspace = Workspace(self.config["workspace-url"], token=self.token)
            ),
        )

        db_conf = params.get('efi_db_config')
        if db_conf != None:
            config['efi_db_config'] = db_conf
        est_conf = params.get('efi_est_config')
        if est_conf != None:
            config['efi_est_config'] = est_conf

        job = KbEstGenerateJob(ctx, config)

        job.create_job(params)

        job.start_job(params)

        output = job.generate_report(params)

        #END run_est_generate_app

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_est_generate_app return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_est_analysis_app(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_est_analysis_app

        #is_valid = EstAnalysisJob.validate_params(params)

        shared_folder = params.get('output_dir', self.shared_folder)
        config = dict(
            callback_url = self.callback_url,
            shared_folder = shared_folder,
            clients = dict(
                KBaseReport = KBaseReport,
                DataFileUtil = DataFileUtil(self.callback_url, token = self.token),
                Workspace = Workspace(self.config["workspace-url"], token = self.token)
            ),
        )

        db_conf = params.get('efi_db_config')
        if db_conf != None:
            config['efi_db_config'] = db_conf
        est_conf = params.get('efi_est_config')
        if est_conf != None:
            config['efi_est_config'] = est_conf
        if params.get('similarity_ref') == None and params.get('data_transfer_zip') == None:
            raise ValueError('Unable to run EST analysis app: must provide similarity_ref')

        job = KbEstAnalysisJob(ctx, config)

        status = job.create_job(params)
        if not status:
            raise ValueError('Unable to create EST analysis app job')

        status = job.start_job()
        if not status:
            raise ValueError('Unable to run EST analysis app job')

        output = job.generate_report(params)

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
