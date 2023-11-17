
import io
import logging
import os
import subprocess
import uuid
import json
import shutil
import collections.abc
import re
from pathlib import Path

# This is the SFA base package which provides the Core app class.
from base import Core
from installed_clients.DataFileUtilClient import DataFileUtil
from ..utils.utils import EfiUtils
from ..utils.data_utils import DataUtils

MODULE_DIR = '/kb/module'
TEMPLATES_DIR = os.path.join(MODULE_DIR, 'lib/templates')


def get_streams(process):
    """
    Returns decoded stdout,stderr after loading the entire thing into memory
    """
    stdout, stderr = process.communicate()
    return (stdout.decode('utf-8', 'ignore'), stderr.decode('utf-8', 'ignore'))


class EstAnalysisJob:

    def _log(self, message):
        if self.is_debug:
            print(message)

    def __init__(self, config, shared_folder, clients):
        #TODO: make this a config variable
        est_home = '/apps/EST'
        db_conf = config.get('efi_db_config')
        if db_conf != None:
            self.efi_db_config = db_conf
        else:
            self.efi_db_config = '/apps/EFIShared/db_conf.sh'

        est_conf = config.get('efi_est_config')
        if est_conf != None:
            self.efi_est_config = est_conf
        else:
            self.efi_est_config = '/apps/EST/env_conf.sh'

        self.is_debug = config.get('debug', True) or ('PYTEST_CURRENT_TEST' in os.environ)

        self.shared_folder = shared_folder
        self.output_dir = EfiUtils.get_unique_dir(shared_folder, 'analysis_')
        #self.output_dir = '/kb/module/work'
        EfiUtils.mkdir_p(self.output_dir)
        self._log('Creating ' + self.output_dir)

        self.wsclient = clients.Workspace
        self.dfu = clients.DataFileUtil

        self.script_file = ''
        self.est_dir = est_home
        self.est_env = [self.efi_est_config, '/apps/EFIShared/env_conf.sh', '/apps/env.sh', '/apps/blast_legacy.sh', self.efi_db_config]


    def create_job(self, params):
        input_dataset = self.get_input_dataset(params)
        if input_dataset == None:
            raise ValueError('Unable to find input dataset from params ' + str(params))
        input_name = input_dataset[0]
        input_data = input_dataset[1]
        input_dataset_zip = input_dataset[2]

        create_job_pl = os.path.join(self.est_dir, 'create_job.pl')

        # The input and output directories for the analysis job are the same, because we copy the transfer file in and unzip it.
        process_args = [create_job_pl, '--job-dir', self.output_dir]
        if params.get('job_id') != None:
            process_args.extend(['--job-id', params['job_id']])

        if params.get('ascore') == None:
            raise ValueError('Ascore parameter is necessary in order to create EST analysis job')

        self._log(params)

        process_params = {'type': 'analysis'}
        process_params['a_job_dir'] = self.output_dir
        process_params['zip_transfer'] = input_dataset_zip
        process_params['filter'] = params.get('filter', 'eval')
        process_params['minval'] = params.get('ascore')
        if params.get('minlen') != None:
            process_params['minlen'] = params['min_len']
        if params.get('maxlen') != None:
            process_params['maxlen'] = params['max_len']
        if params.get('uniref_version') != None:
            process_params['uniref_version'] = params['uniref_version']

        json_str = json.dumps(process_params)

        self._log("### JSON INPUT PARAMETERS TO create_job.pl ####################################################################\n")
        self._log(json_str + "\n\n\n\n")

        process_args.extend(['--params', "'"+json_str+"'"])
        process_args.extend(['--env-scripts', ','.join(self.est_env)])

        process = subprocess.Popen(
            process_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = get_streams(process)
        if stdout != None:
            script_file = stdout.strip()
        else:
            raise ValueError('Unable to create EST analysis job: unable to obtain output streams')

        self._log("### OUTPUT FROM CREATE JOB ####################################################################################\n")
        self._log(str(stdout) + "\n---------\n")
        self._log("### ERR\n")
        self._log(str(stderr) + "\n\n\n\n")
        self._log(os.listdir(self.output_dir))
        self._log("END ERR")

        self.script_file = script_file

        return True


    def start_job(self):
        if not os.path.exists(self.script_file):
            raise ValueError('Unable to run EST analysis job: the script does not exist')

        start_job_pl = os.path.join('/bin/bash')

        process_args = [start_job_pl, self.script_file]
        process = subprocess.Popen(
            process_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = get_streams(process)
        if stdout == None:
            raise ValueError('Unable to run EST analysis job: unable to obtain output streams')

        self._log("### OUTPUT FROM GENERATE ######################################################################################\n")
        self._log(str(stdout) + "\n---------\n")
        self._log("### ERR\n")
        self._log(str(stderr) + "\n\n\n\n")

        ssn_ref = self.save_output()

        if ssn_ref != None:
            return True
        else:
            raise ValueError('Unable to run EST analysis job: unable to save output')


    def get_input_dataset(self, params):
        # Direct input, do not get from KBase shock API
        if params.get('data_transfer_zip'):
            data_transfer_zip = params['data_transfer_zip']
            data = params.get('data_transfer_meta', {})
            input_name = params.get('data_transfer_name', 'Direct')
            return input_name, data, data_transfer_zip

        objects = self.wsclient.get_objects2({'objects': [{'ref': params['compute_dataset_ref']}]})
        if not isinstance(objects, dict) or len(objects) == 0:
            raise ValueError('Unable to find input dataset ' + params['compute_dataset_ref'])
            #return None

        objects = objects['data']
        if len(objects) == 0:
            raise ValueError('No objects in input dataset')
            #return None
        the_object = objects[0]
        data = the_object['data']

        (input_name, obj_type) = DataUtils.get_obj_name_and_type_from_obj_info(the_object['info'])
        if obj_type != 'ComputedProteinSims':
            raise ValueError('Invalid type in input dataset')
            #return None

        data_transfer_zip = os.path.join(self.output_dir, 'data_transfer.zip')

        if not os.path.exists(self.output_dir):
            raise ValueError('Output dir ' + self.output_dir + ' does not exist')
        gen_file_hid = data['gen_file']
        ret_info = self.dfu.shock_to_file({'handle_id': gen_file_hid, 'file_path': data_transfer_zip, 'unpack': None})
        self._log(str(ret_info))

        self._log(os.listdir(self.output_dir))
        self._log('Got ' + input_name + ' ' + str(data) + ' ' + gen_file_hid + ' ' + data_transfer_zip)
        
        return input_name, data, data_transfer_zip


    def save_output(self):
        #TODO
        aaa = 1
        return True


    def get_reports_path(self):
        reports_path = os.path.join(self.shared_folder, 'reports')
        return reports_path

    def generate_report(self, params):

        """
        This method is where to define the variables to pass to the report.
        """
        # This path is required to properly use the template.
        reports_path = self.get_reports_path()
        EfiUtils.mkdir_p(reports_path)
        #output_dir = os.path.join(self.output_dir, 'output')
        output_dir = self.output_dir

        self._log(os.listdir(output_dir))

        ssn_data = self.load_stats_file(output_dir)
        if ssn_data.get('full_ssn_file') == None:
            raise ValueError('Unable to parse stats file')

        ssn_file             = 'ssn.zip'
        ssn_file_out         = os.path.join(reports_path, ssn_file)
        ssn_file_src         = os.path.join(output_dir, ssn_data['full_ssn_file'])
        ssn_file_rel         = ssn_file

        #TODO: add the images into the EFI code.
        # Actually, we probably don't want to do this.
        #length_histogram     = 'length_histogram_uniprot.png'
        #length_histogram_src = os.path.join(output_dir, length_histogram)
        #length_histogram_out = os.path.join(reports_path, length_histogram)
        #length_histogram_rel = length_histogram
        #alignment_length     = 'alignment_length.png'
        #alignment_length_out = os.path.join(reports_path, alignment_length)
        #alignment_length_src = os.path.join(output_dir, alignment_length)
        #alignment_length_rel = alignment_length
        #percent_identity     = 'percent_identity.png'
        #percent_identity_out = os.path.join(reports_path, percent_identity)
        #percent_identity_src = os.path.join(output_dir, percent_identity)
        #percent_identity_rel = percent_identity

        #shutil.copyfile(length_histogram_src, length_histogram_out)
        #shutil.copyfile(alignment_length_src, alignment_length_out)
        #shutil.copyfile(percent_identity_src, percent_identity_out)
        shutil.copyfile(ssn_file_src, ssn_file_out)

        generate_summary = []
        analysis_summary = []

        template_variables = ssn_data
        template_variables['generate_summary'] = generate_summary
        template_variables['analysis_summary'] = analysis_summary

        #template_variables['length_histogram_file'] = length_histogram_rel
        #template_variables['alignment_length_file'] = alignment_length_rel
        #template_variables['percent_identity_file'] = percent_identity_rel

        return template_variables

    def load_stats_file(self, output_dir):
        stats_file = os.path.join(output_dir, "stats.tab")
        repnode_ssns = []
        data = {}
        if os.path.isfile(stats_file):
            with open(stats_file) as fh:
                line = fh.readline() #header
                line = fh.readline()
                while line:
                    parts = re.split(r"\t", line)
                    mx = re.search(r"full_ssn", parts[0])
                    if mx != None and data.get('full_ssn_file') == None:
                        data['full_ssn_file'] = parts[0] + '.zip'
                        data['full_num_nodes'] = parts[1]
                        data['full_num_edges'] = parts[2]
                    else:
                        mx = re.search(r"repnode-([0-9\.]+)_ssn", line)
                        if mx != None:
                            rep_id = float(mx.group(1)) * 100
                            repnode_ssns.append([parts[0] + '.zip', rep_id, parts[1], parts[2]])
                    line = fh.readline()
        data['repnode_ssns'] = repnode_ssns
        return data



class KbEstAnalysisJob(Core):

    def __init__(self, ctx, config, clients_class=None):
        super().__init__(ctx, config, clients_class)

        # self.shared_folder is defined in the Core App class.
        self.job_interface = EstAnalysisJob(config, self.shared_folder, self.clients)
        self.report = self.clients.KBaseReport

    def validate_params(params):
        return EstAnalysisJob.validate_params(params)

    def create_job(self, params):
        return self.job_interface.create_job(params)

    def start_job(self):
        return self.job_interface.start_job()

    def generate_report(self, params):

        reports_path = self.job_interface.get_reports_path()
        template_variables = self.job_interface.generate_report(params)

        # The KBaseReport configuration dictionary
        config = dict(
            report_name = f"EfiFamilyApp_{str(uuid.uuid4())}",
            reports_path = reports_path,
            template_variables = template_variables,
            workspace_name = params['workspace_name'],
        )
        
        # Path to the Jinja template. The template can be adjusted to change
        # the report.
        template_path = os.path.join(TEMPLATES_DIR, 'est_analysis_report.html')

        output_report = self.create_report_from_template(template_path, config)
        output_report['shared_folder'] = self.shared_folder
        return output_report



