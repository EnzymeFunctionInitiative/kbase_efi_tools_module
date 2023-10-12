
import io
import logging
import os
import subprocess
import uuid
import json
import shutil
import re
from pathlib import Path

# This is the SFA base package which provides the Core app class.
from base import Core
from installed_clients.DataFileUtilClient import DataFileUtil
from ..utils.utils import EfiUtils as utils

MODULE_DIR = "/kb/module"
TEMPLATES_DIR = os.path.join(MODULE_DIR, "lib/templates")


def get_streams(process):
    """
    Returns decoded stdout,stderr after loading the entire thing into memory
    """
    stdout, stderr = process.communicate()
    return (stdout.decode("utf-8", "ignore"), stderr.decode("utf-8", "ignore"))


class EstGenerateJob:

    def __init__(self, config, shared_folder):

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

        self.shared_folder = shared_folder
        self.output_dir = os.path.join(self.shared_folder, 'job_temp')
        utils.mkdir_p(self.output_dir)

        self.script_file = ''
        self.est_dir = est_home
        #TODO: make a more robust way of doing this
        self.est_env = [self.efi_est_config, '/apps/EFIShared/env_conf.sh', '/apps/env.sh', '/apps/blast_legacy.sh', self.efi_db_config]

    #TODO: implement this
    def validate_params(params):
        return True

    def create_job(self, params):

        create_job_pl = os.path.join(self.est_dir, 'create_job.pl')

        process_args = [create_job_pl, '--job-dir', self.output_dir]
        if params.get('job_id') != None:
            process_args.extend(['--job-id', params['job_id']])

        print(params)

        process_params = {'type': '', 'exclude_fragments': False}
        self.get_blast_params(params, process_params)
        self.get_family_params(params, process_params)
        self.get_fasta_params(params, process_params)
        self.get_accession_params(params, process_params)

        json_str = json.dumps(process_params)

        print("### JSON INPUT PARAMETERS TO create_job.pl ####################################################################\n")
        print(json_str + "\n\n\n\n")

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
            return None

        print("### OUTPUT FROM CREATE JOB ####################################################################################\n")
        print(str(stdout) + "\n---------\n")
        print("### ERR\n")
        print(str(stderr) + "\n\n\n\n")

        self.job_type = process_params['type']
        self.process_params = process_params
        self.job_name = ""

        self.script_file = script_file

        return script_file

    def get_blast_params(self, params, process_params):
        if params.get('option_blast') != None:
            process_params['type'] = 'blast'
            seq = params['option_blast'].get('blast_sequence')
            seq = re.sub('[ \t\r\n]', '', seq)
            process_params['input_seq'] = seq
            if seq != None:
                process_params['seq'] = seq
            else:
                process_params['seq_file'] = params['option_blast']['sequence_file']
            if params['option_blast'].get('blast_exclude_fragments') and params['option_blast']['blast_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
    def get_family_params(self, params, process_params):
        if params.get('option_family') != None:
            process_params['type'] = 'family'
            process_params['family'] = params['option_family']['fam_family_name']
            process_params['uniref'] = params['option_family']['fam_use_uniref']
            if params['option_family'].get('fam_exclude_fragments') and params['option_family']['fam_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
    def get_fasta_params(self, params, process_params):
        if params.get('option_fasta') != None:
            process_params['type'] = 'fasta'
            fasta_file_path = None
            if params['option_fasta'].get('fasta_file') == None and params['option_fasta'].get('fasta_seq_input_text') != None:
                #TODO: write text to a file
                fasta_file_path = ''
            elif params['option_fasta'].get('fasta_file') == None:
                print("Error")#TODO: make an error here

            process_params['fasta_file'] = fasta_file_path
            if params['option_fasta'].get('fasta_exclude_fragments') and params['option_fasta']['fasta_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
    def get_accession_params(self, params, process_params):
        if params.get('option_accession') != None:
            process_params['type'] = 'acc'
            id_list_file = None
            if params['option_accession'].get('acc_input_file') == None and params['option_accession'].get('acc_input_list') != None:
                id_list = params['option_accession'].get('acc_input_list')
                #TODO: write this to a file
                id_list_file = ''
            elif params['option_accession'].get('acc_input_file') == None and params['option_accession'].get('acc_input_text') != None:
                acc_id_text = params['option_accession']['acc_input_text']
                #TODO: write this to a file
                id_list_file = ''
            elif params['option_accession'].get('acc_input_file') == None:
                print("Error")
                #TODO: make an error here

            process_params['id_list_file'] = id_list_file
            if params['option_accession'].get('acc_exclude_fragments') and params['option_accession']['acc_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1

    def start_job(self):
        if not os.path.exists(self.script_file):
            #TODO: throw error
            return False

        start_job_pl = os.path.join('/bin/bash')

        process_args = [start_job_pl, self.script_file]
        process = subprocess.Popen(
            process_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = get_streams(process)

        script_contents = Path(self.script_file).read_text()
        print(os.listdir(self.output_dir + "/output"))
        print("### SCRIPT OUTPUT #############################################################################################\n")
        print(script_contents)
        print("### FILE OUTPUT ###############################################################################################\n")
        junk = Path(self.output_dir + "/output/blastfinal.tab").read_text()
        print(junk[0:1000] + "\n")
        print("########\n")
        junk = Path(self.output_dir + "/output/allsequences.fa").read_text()
        print(junk[0:1000] + "\n")
        print("### OUTPUT FROM GENERATE ######################################################################################\n")
        print(str(stdout) + "\n---------\n")
        print("### ERR\n")
        print(str(stderr) + "\n\n\n\n")
        print("###############################################################################################################\n")

        return True

    def get_reports_path(self):
        reports_path = os.path.join(self.shared_folder, "reports")
        return reports_path

    def generate_report(self):
        #TODO:
        """
        This method is where to define the variables to pass to the report.
        """
        # This path is required to properly use the template.
        reports_path = self.get_reports_path()
        utils.mkdir_p(reports_path)

        length_histogram = "length_histogram.png" if self.job_type == "blast" else "length_histogram_uniprot.png"
        alignment_length = "alignment_length.png"
        percent_identity = "percent_identity.png"
        number_of_edges = "number_of_edges.png"
        length_histogram_uniref = "length_histogram_uniref.png"

        length_histogram_src = os.path.join(self.output_dir, "output", length_histogram)
        alignment_length_src = os.path.join(self.output_dir, "output", alignment_length)
        percent_identity_src = os.path.join(self.output_dir, "output", percent_identity)
        number_of_edges_src = os.path.join(self.output_dir, "output", number_of_edges)
        length_histogram_uniref_src = os.path.join(self.output_dir, "output", length_histogram_uniref)

        length_histogram_out = os.path.join(reports_path, length_histogram)
        alignment_length_out = os.path.join(reports_path, alignment_length)
        percent_identity_out = os.path.join(reports_path, percent_identity)
        number_of_edges_out = os.path.join(reports_path, number_of_edges)
        length_histogram_uniref_out = os.path.join(reports_path, length_histogram_uniref)

        length_histogram_rel = length_histogram
        alignment_length_rel = alignment_length
        percent_identity_rel = percent_identity
        number_of_edges_rel = number_of_edges
        length_histogram_uniref_rel = length_histogram_uniref

        print(os.listdir(self.output_dir + "/output"))
        print(length_histogram_src + " --> " + length_histogram_out)

        shutil.copyfile(length_histogram_src, length_histogram_out)
        shutil.copyfile(alignment_length_src, alignment_length_out)
        shutil.copyfile(percent_identity_src, percent_identity_out)
        shutil.copyfile(number_of_edges_src, number_of_edges_out)
        if os.path.isfile(length_histogram_uniref_src):
            shutil.copyfile(length_histogram_uniref_src, length_histogram_uniref_out)

        tax_file = "tax.json"
        tax_file_src = os.path.join(self.output_dir, "output", tax_file)
        tax_file_out = os.path.join(reports_path, tax_file)

        out_fh = open(tax_file_out, "w")
        #out_fh.write("{% raw %}\n")
        tax_json = ""
        if os.path.isfile(tax_file_src):
            with open(tax_file_src, "r") as in_fh:
                tax_json = in_fh.read()
        else:
            tax_json = '{"data":{}}'
        out_fh.write(tax_json)
        #out_fh.write("\b{% endraw %}\n")
        out_fh.close()

        conv_ratio = 0
        #TODO

        show_uniref_len_hist = False
        use_uniref = False
        if self.process_params.get("uniref") != None and self.process_params["uniref"]:
            show_uniref_len_hist = True

        sunburst_app_primary_id_type = "UniProt"
        has_sunburst_uniref = "false"
        if self.job_type == "family" or self.job_type == "acc":
            has_sunburst_uniref = "true"
        elif self.job_type == "blast":
            sunburst_app_primary_id_type = "UniProt" #TODO: check if it is using a UniRef database for blasting

        job_type = ""
        if self.job_type == "family": job_type = "FAMILY"
        elif self.job_type == "fasta": job_type = "FASTA"
        elif self.job_type == "acc": job_type = "ACCESSION"
        elif self.job_type == "blast": job_type = "BLAST"

        input_seq = ""
        if self.job_type == "blast":
            input_seq = self.process_params["input_seq"]

        job_info = []
        job_info.append(["Job Name", self.job_name])
        job_info.append(["Input Option", job_type])
        job_info.append(["E-Value for SSN Edge Calculation", "5"])
        if self.job_type == "family":
            job_info.append(["Pfam / InterPro Family", ""])
            job_info.append(["Number of IDs in Pfam / InterPro Family", ""])
        job_info.append(["Domain Option", "off"])
        if use_uniref:
            job_info.append(["UniRef Version", use_uniref])
        if self.job_type == "family":
            job_info.append(["Number of Cluster IDs in UniRef" + str(use_uniref) + " Family", ""])
        job_info.append(["Exclude Fragments", "yes" if self.process_params["exclude_fragments"] else "no"])
        job_info.append(["Total Number of Sequences in Dataset", ""])
        job_info.append(["Total Number of Edges", ""])
        job_info.append(["Number of Unique Sequences", ""])

        template_variables = dict(
                length_histogram_file = length_histogram_rel,
                alignment_length_file = alignment_length_rel,
                percent_identity_file = percent_identity_rel,
                number_of_edges_file  = number_of_edges_rel,
                length_histogram_uniref_file = length_histogram_uniref_rel,
                conv_ratio = conv_ratio,
                job_info = job_info,
                show_uniref_len_hist = show_uniref_len_hist,
                has_sunburst_uniref = has_sunburst_uniref,
                sunburst_app_primary_id_type = sunburst_app_primary_id_type,
                tax_data = tax_json,
                input_seq = input_seq,
            )

        return template_variables






class KbEstGenerateJob(Core):

    def __init__(self, ctx, config, clients_class=None):
        super().__init__(ctx, config, clients_class)

        # shared_folder is defined in the Core App class. It is also unique, time-stamped.
        self.job_interface = EstGenerateJob(config, self.shared_folder)

        #self.ws_url = config['workspace-url']
        self.callback_url = config['callback_url']
        self.dfu = DataFileUtil(self.callback_url)
        self.report = self.clients.KBaseReport

    def validate_params(params):
        return self.job_interface.validate_params(params)

    def create_job(self, params):
        return self.job_interface.create_job(params)

    def start_job(self):
        return self.job_interface.start_job()

    def generate_report(self, params):

        reports_path = self.job_interface.get_reports_path()
        template_variables = self.job_interface.generate_report()

        # The KBaseReport configuration dictionary
        config = dict(
            report_name = f"EfiFamilyApp_{str(uuid.uuid4())}",
            reports_path = reports_path,
            template_variables = template_variables,
            workspace_name = params["workspace_name"],
        )
        
        # Path to the Jinja template. The template can be adjusted to change
        # the report.
        template_path = os.path.join(TEMPLATES_DIR, "est_generate_report.html")

        output_report = self.create_report_from_template(template_path, config)
        output_report["shared_folder"] = self.shared_folder
        print("OUTPUT REPORT\n")
        print(str(output_report) + "\n")
        return output_report


