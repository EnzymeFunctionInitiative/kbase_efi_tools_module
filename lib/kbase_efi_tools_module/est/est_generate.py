
import io
import logging
import os
import subprocess
import uuid
import json
import shutil
import re
import random
from pathlib import Path
from os.path import exists

# This is the SFA base package which provides the Core app class.
from base import Core
#from installed_clients.DataFileUtilClient import DataFileUtil
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

        self.shared_folder = shared_folder
        self.output_dir = os.path.join(self.shared_folder, 'job_temp')
        utils.mkdir_p(self.output_dir)

        self.script_file = ''
        self.est_dir = est_home
        self.wsclient = clients.Workspace
        self.dfu = clients.DataFileUtil
        #We need to keep track of the workspace objects use or create
        self.input_objects = []
        self.output_objects = []

        #TODO: make a more robust way of doing this
        self.est_env = [self.efi_est_config, '/apps/EFIShared/env_conf.sh', '/apps/env.sh', '/apps/blast_legacy.sh', self.efi_db_config]


    #TODO: implement this
    def validate_params(kb_params):
        return True


    def create_job(self, kb_params):
        self.input_objects = []
        self.output_objects = []

        create_job_pl = os.path.join(self.est_dir, 'create_job.pl')

        process_args = [create_job_pl, '--job-dir', self.output_dir]
        if kb_params.get('job_id') != None:
            process_args.extend(['--job-id', kb_params['job_id']])

        print(kb_params)

        process_params = {'type': '', 'exclude_fragments': 0}
        job_name_blast = self.get_blast_params(kb_params, process_params)
        job_name_family = self.get_family_params(kb_params, process_params)
        job_name_fasta = self.get_fasta_params(kb_params, process_params)
        job_name_acc = self.get_accession_params(kb_params, process_params)

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
        self.job_name = ""
        if job_name_blast: self.job_name = job_name_blast
        if job_name_family: self.job_name = job_name_family
        if job_name_fasta: self.job_name = job_name_fasta
        if job_name_acc: self.job_name = job_name_acc

        self.script_file = script_file

        self.process_params = process_params
        self.kb_params = kb_params

        return script_file


    def get_blast_params(self, kb_params, process_params):
        job_name = ''
        if kb_params.get('option_blast') != None:
            process_params['type'] = 'blast'
            job_name = 'BLAST'
            seq = kb_params['option_blast'].get('blast_sequence')
            seq = re.sub('[ \t\r\n]', '', seq)
            process_params['input_seq'] = seq
            if seq != None:
                process_params['seq'] = seq
            else:
                process_params['seq_file'] = kb_params['option_blast']['sequence_file']
            if kb_params['option_blast'].get('blast_exclude_fragments') and kb_params['option_blast']['blast_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
                job_name += ' [no fragments]'
        return job_name
    def get_family_params(self, kb_params, process_params):
        job_name = ''
        if kb_params.get('option_family') != None:
            job_name = 'Family'
            process_params['type'] = 'family'
            process_params['family'] = kb_params['option_family']['fam_family_name']
            job_name += ' (' + process_params['family'] + ')'
            process_params['uniref'] = kb_params['option_family']['fam_use_uniref']
            if kb_params['option_family'].get('fam_exclude_fragments') and kb_params['option_family']['fam_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
                job_name += ' [no fragments]'
        return job_name
    def get_fasta_params(self, kb_params, process_params):
        job_name = ''
        if kb_params.get('option_fasta') != None:
            process_params['type'] = 'fasta'
            job_name = 'FASTA'
            fasta_file_path = None
            if kb_params['option_fasta'].get('fasta_file') == None and kb_params['option_fasta'].get('fasta_seq_input_text') != None:
                #TODO: write text to a file
                fasta_file_path = ''
            elif kb_params['option_fasta'].get('fasta_file') == None:
                print('Error')#TODO: make an error here

            process_params['fasta_file'] = fasta_file_path
            if kb_params['option_fasta'].get('fasta_exclude_fragments') and kb_params['option_fasta']['fasta_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
                job_name += ' [no fragments]'
        return job_name
    def get_accession_params(self, kb_params, process_params):
        job_name = ''
        if kb_params.get('option_accession') != None:
            process_params['type'] = 'acc'
            job_name = 'Accession'
            id_list_file = None
            if kb_params['option_accession'].get('acc_input_file') == None and kb_params['option_accession'].get('acc_input_list') != None:
                id_list = kb_params['option_accession'].get('acc_input_list')
                #TODO: write this to a file
                id_list_file = ''
            elif kb_params['option_accession'].get('acc_input_file') == None and kb_params['option_accession'].get('acc_input_text') != None:
                acc_id_text = kb_params['option_accession']['acc_input_text']
                #TODO: write this to a file
                id_list_file = ''
            elif kb_params['option_accession'].get('acc_input_file') == None:
                print('Error')
                #TODO: make an error here

            process_params['id_list_file'] = id_list_file
            if kb_params['option_accession'].get('acc_exclude_fragments') and kb_params['option_accession']['acc_exclude_fragments'] == 1:
                process_params['exclude_fragments'] = 1
                job_name += ' [no fragments]'
        return job_name


    def start_job(self, kb_params):
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
        print(os.listdir(self.output_dir + '/output'))
        print('### SCRIPT OUTPUT #############################################################################################\n')
        print(script_contents)
        print('### FILE OUTPUT ###############################################################################################\n')
        junk = Path(self.output_dir + '/output/blastfinal.tab').read_text()
        print(junk[0:1000] + '\n')
        print('########\n')
        junk = Path(self.output_dir + '/output/allsequences.fa').read_text()
        print(junk[0:1000] + '\n')
        print('### OUTPUT FROM GENERATE ######################################################################################\n')
        print(str(stdout) + '\n---------\n')
        print('### ERR\n')
        print(str(stderr) + '\n\n\n\n')
        print('###############################################################################################################\n')

        kb_params["output_name"] = re.sub(r"[^a-z0-9_]+", "_", self.job_name, count=0, flags=re.IGNORECASE)

        #sequence_set = "TODO"
        #if not "sequenceset_ref" in kb_params:
        kb_params["sequenceset_ref"] = self.get_sequence_set_ref(kb_params)
        print("SEQUENCESET_REF")
        print(kb_params["sequenceset_ref"])

        if not "output_name" in kb_params:
            kb_params["output_name"] = self.job_name

        output_file = os.path.join(self.output_dir, "output", "data_transfer.zip")
        if not os.path.exists(output_file):
            return False

        dataset_vals = { "output_file": output_file }
        self.save_input_options(dataset_vals) # Save into dataset_vals
        file_status = self.save_output_values(dataset_vals)
        if not file_status:
            return False

        self.save_output(kb_params, dataset_vals)

        return True


    def get_sequence_set_ref(self, kb_params):
        if "workspace_id" in kb_params:
            workspace_id = kb_params["workspace_id"]
        else:
            workspace_id = self.dfu.ws_name_to_id(kb_params["workspace_name"])

        set_name = "DummyPSS_" + str(random.randint(100, 100000))
        ws_inputs = [
                {
                    "type": "KBaseSequences.ProteinSequenceSet",
                    "data": {"description": set_name, "id": set_name, "sequences": [], "included_types": [], "ontology_events": [], "md5": ""},
                    "name": set_name
                }]
        object_info = self.dfu.save_objects({"id": workspace_id, "objects": ws_inputs})
        ref_id = utils.object_info_to_ref(object_info)
        return ref_id

    def save_input_options(self, dataset_vals):
        #TODO: most of these are to-do
        pp = self.process_params
        dataset_vals["input_type"] = self.job_type

        if self.job_type == "family":
            dataset_vals["input_family_id"] = pp["family"]
            ur_ver = 0
            if pp.get("uniref") != None:
                if pp["uniref"].isnumeric():
                    ur_ver = int(pp["uniref"])
            dataset_vals["uniref_version"] = ur_ver
        else:
            dataset_vals["input_family_id"] = ""
            dataset_vals["uniref_version"] = 0

        dataset_vals["evalue_for_ssn_calculation"] = 5 #TODO
        dataset_vals["domain_option"] = 0 #TODO
        dataset_vals["exclude_fragments"] = pp["exclude_fragments"]
        dataset_vals["database_version"] = "InterPro XX / UniProt XXXX_XX" # TODO

    def save_output_values(self, dataset_vals):
        file_key_mapping = {
                "FullFamily": "ids_in_pfam_family", "Family": "cluster_ids_in_uniref_family", "Total": "total_sequences_in_dataset",
                "EdgeCount": "total_edges", "UniqueSeq": "unique_sequences", "ConvergenceRatio": "convergence_ratio", "User": "input_sequence_count"
                }
        counts_file = os.path.join(self.output_dir, "output", "acc_counts")
        if not os.path.exists(counts_file):
            return False
        with open(counts_file) as fh:
            line = fh.readline()
            while line:
                parts = line.split("\t")
                if parts != None and len(parts) == 2:
                    meta_key = file_key_mapping.get(parts[0])
                    if parts[0] == "ConvergenceRatio":
                        value = float(parts[1])
                    else:
                        value = int(parts[1])
                    if meta_key != None:
                        dataset_vals[meta_key] = value
                line = fh.readline()
        return True


    #Use this function to save the output object to the KBase workspace
    def save_output(self, kb_params, dataset_vals):
        #I am assuming kb_params contains the following fields:workspace, sequenceset_ref, output_name
        #I am assuming dataset_vals contains the following fields:output_file, input_sequence_count, input_type, input_family_id, evalue_for_ssn_calculation, domain_option, exlude_fragments, database_version, uniref_version, ids_in_pfam_family, cluster_ids_in_uniref_family, total_sequences_in_dataset, total_edges, unique_sequences, convergence_ratio
        
        #First saving output file to KBase S3 using data file util
        handle_info = None
        if exists(dataset_vals["output_file"]):
            print("Saving precomputed data to KBase S3")
            handle_info = self.dfu.file_to_shock({'file_path': dataset_vals["output_file"],'make_handle': 1, 'pack': 'gzip'})

        #Next creating workspace object to house the output file handle
        if handle_info:
            new_object = {
                "gen_file":                         handle_info['handle']['hid'],
                "input_sequence_count":             dataset_vals["input_sequence_count"],
                "input_type":                       dataset_vals["input_type"],
                "input_family_id":                  dataset_vals["input_family_id"],
                "evalue_for_ssn_calculation":       dataset_vals["evalue_for_ssn_calculation"],
                "domain_option":                    dataset_vals["domain_option"],
                #TODO: fix the typo and then uncomment this line# "exclude_fragments":                dataset_vals["exclude_fragments"],
                "exlude_fragments":                 dataset_vals["exclude_fragments"],
                "database_version":                 dataset_vals["database_version"],
                "uniref_version":                   dataset_vals["uniref_version"],
                "ids_in_pfam_family":               dataset_vals["ids_in_pfam_family"],
                "cluster_ids_in_uniref_family":     dataset_vals["cluster_ids_in_uniref_family"],
                "total_sequences_in_dataset":       dataset_vals["total_sequences_in_dataset"],
                "total_edges":                      dataset_vals["total_edges"],
                "unique_sequences":                 dataset_vals["unique_sequences"],
                "convergence_ratio":                dataset_vals["convergence_ratio"]
            }
            new_object["sequenceset"] = kb_params['sequenceset_ref']
            
            dataset_ref = str(kb_params["workspace"]) + "/" + kb_params["output_name"]
            #Tracking that a new workspace object has been created so we can include this information in the report
            self.output_objects.append({"ref": dataset_ref, "description": "Precomputed similarities for generating sequence similarity networks"})
            
            #Setting up the parameters for saving the object
            save_params = {
                'objects': [{
                    'type': "SequenceSimilarityNetworks.ComputedProteinSims",
                    'name': kb_params["output_name"],
                    'data': new_object,
                    'meta': {},
                    'provenance': [{
                        'description': "EST Generate App Output",
                        'input_ws_objects': self.input_objects,
                        'method': "run_est_generate_app",
                        'script_command_line': "",
                        'method_params': [kb_params],
                        'service': "kbase_efi_tools_module",
                        'service_ver': "0.0.1",
                    }]
                }]
            }

            ##Handling if the input workspace is an ID or name
            #if isinstance(kb_params["workspace"], int):
            #    save_params["id"] = kb_params["workspace"]
            ##elif isinstance(kb_params["workspace"], str):
            #else:
            #    save_params["workspace"] = kb_params["workspace"]
            if "workspace_name" in kb_params:
                workspace_name = kb_params["workspace_name"]
            else:
                workspace_name = str(kb_params["workspace_id"])
            save_params["workspace"] = workspace_name
            print("Saving files to workspace " + workspace_name)

            #Saving the object to the workspace  
            object_info = self.wsclient.save_objects(save_params)
            ref_id = utils.object_info_to_ref(object_info)
            return ref_id
        return None


    def generate_report(self, kb_params):
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


    def get_reports_path(self):
        reports_path = os.path.join(self.shared_folder, "reports")
        return reports_path





class KbEstGenerateJob(Core):

    def __init__(self, ctx, config, clients_class=None):
        super().__init__(ctx, config, clients_class)

        # shared_folder is defined in the Core App class. It is also unique, time-stamped.
        self.job_interface = EstGenerateJob(config, self.shared_folder, self.clients)
        self.report = self.clients.KBaseReport

        #self.ws_url = config['workspace-url']
        #self.callback_url = config['callback_url']

    def validate_params(kb_params):
        return self.job_interface.validate_params(kb_params)

    def create_job(self, kb_params):
        return self.job_interface.create_job(kb_params)

    def start_job(self, kb_params):
        return self.job_interface.start_job(kb_params)

    def generate_report(self, kb_params):

        reports_path = self.job_interface.get_reports_path()
        template_variables = self.job_interface.generate_report(kb_params)

        # The KBaseReport configuration dictionary
        config = dict(
            report_name = f"EfiFamilyApp_{str(uuid.uuid4())}",
            reports_path = reports_path,
            template_variables = template_variables,
            workspace_name = kb_params["workspace_name"],
        )
        
        # Path to the Jinja template. The template can be adjusted to change
        # the report.
        template_path = os.path.join(TEMPLATES_DIR, "est_generate_report.html")

        output_report = self.create_report_from_template(template_path, config)
        output_report["shared_folder"] = self.shared_folder
        print("OUTPUT REPORT\n")
        print(str(output_report) + "\n")
        return output_report


