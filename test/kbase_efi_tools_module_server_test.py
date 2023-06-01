# -*- coding: utf-8 -*-
import os
import time
import unittest
import collections.abc
import re
import shutil
import logging
from configparser import ConfigParser
from parameterized import parameterized, parameterized_class

from kbase_efi_tools_module.kbase_efi_tools_moduleImpl import kbase_efi_tools_module
from kbase_efi_tools_module.kbase_efi_tools_moduleServer import MethodContext
from kbase_efi_tools_module.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace

# From the lib/kbase_efi_tools_module directory
from kbase_efi_tools_module.utils.test_utils import EfiTestUtils


class kbase_efi_tools_moduleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        token = os.environ.get("KB_AUTH_TOKEN", None)
        config_file = os.environ.get("KB_DEPLOYMENT_CONFIG", None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items("kbase_efi_tools_module"):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg["auth-service-url"]
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update(
            {
                "token": token,
                "user_id": user_id,
                "provenance": [
                    {
                        "service": "kbase_efi_tools_module",
                        "method": "please_never_use_it_in_production",
                        "method_params": [],
                    }
                ],
                "authenticated": 1,
            }
        )
        cls.wsURL = cls.cfg["workspace-url"]
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = kbase_efi_tools_module(cls.cfg)
        cls.scratch = cls.cfg["scratch"]
        cls.callback_url = os.environ["SDK_CALLBACK_URL"]
        suffix = int(time.time() * 1000)
        cls.wsName = "kbase_efi_tools_module_" + str(suffix)
        ret = cls.wsClient.create_workspace({"workspace": cls.wsName})  # noqa

        cls.tu = EfiTestUtils(cls)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "wsName"):
            cls.wsClient.delete_workspace({"workspace": cls.wsName})
            print("Test workspace was deleted")

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    # @unittest.skip("Skip test for debugging")
    @parameterized.expand([
                           ("blast,ex_frag,use_file", True, True),
                           ("blast,ex_frag,no_file", True, False),
                           ("blast,frag,use_file", False, True),
                           ("blast,frag,no_file", False, False)
                           ])
    def test_est_generate_blast(self, name, exclude_fragments, use_file):

        option = "blast"
        test_opts = [exclude_fragments, use_file, option]
        test_params = self.get_blast_test_params(test_opts)
        expected = self.get_expected(test_opts)
        logging.info("RUNNING TEST " + name)
        self.run_test("option_" + option, test_params, expected)
        return True

    @parameterized.expand([
                           ("family,ex_frag", True),
                           ("family,frag", False)
                           ])
    def test_est_generate_family(self, name, exclude_fragments):

        option = "family"
        test_opts = [exclude_fragments, option]
        test_params = self.get_family_test_params(test_opts)
        expected = self.get_expected(test_opts)
        logging.info("RUNNING TEST " + name)
        self.run_test("option_" + option, test_params, expected)
        return True

    def get_expected(self, test_opts):
        res_type = test_opts[len(test_opts) - 1]
        exclude_fragments = test_opts[0]
        expected = self.excl_frag_num_seq_data[res_type] if exclude_fragments else self.with_frag_num_seq_data[res_type]
        return expected

    #def test_est_generate_with_fragments(self):

    #    print("### TESTING EST GENERATE WITH FRAGMENTS\n")
    #    test_params = {"exclude_fragments": False}
    #    self.run_est_job_types(test_params)


    ## This function will eventually take in all of the parameters that we will use as input to the
    ## various options.  It is provided so that the same code can be run with options toggled
    ## to different values for testing of functionality.
    ## All of the code inside here will call it's own asserts to check if the various tests were successful.
    #def run_est_job_types(self, test_params):

    #    exclude_fragments = test_params["exclude_fragments"]

    #    ##################################################
    #    # Test BLAST option
    #    print("RUNNING BLAST TEST\n")

    #    self.tu.prep_job_dir()
    #    print("    RUNNING BLAST TEST FOR INPUT FILE PARAMETER\n")
    #    self.run_est_BLAST(test_params, num_seq_data["blast"], use_seq_file = True)

    #    self.tu.prep_job_dir()
    #    print("    RUNNING BLAST TEST FOR INPUT SEQUENCE ARG\n")
    #    self.run_est_BLAST(test_params, num_seq_data["blast"], use_seq_file = False)

    #    print("... SUCCESS\n\n")

    #    ##################################################
    #    # Test FAMILY option
    #    print("RUNNING FAMILY TEST\n")
    #    self.run_est_FAMILY(test_params, num_seq_data["family"])
    #    print("... SUCCESS\n\n")

    #    ##################################################
    #    # Test FASTA option
    #    print("RUNNING FASTA TEST\n")
    #    self.run_est_FAMILY(test_params, num_seq_data["fasta"])
    #    print("... SUCCESS\n\n")

    #    ##################################################
    #    # Test ACCESSION option
    #    print("RUNNING ACCESSION TEST\n")
    #    self.run_est_ACCESSION(test_params, num_seq_data["accession"])
    #    print("... SUCCESS\n\n")

    #    return True

    #def run_est_BLAST(self, test_params, num_seq_data):
    #    test_blast_seq_file = self.tu.get_test_data_file("blast")
    #    blast_seq = self.read_data_from_file(test_blast_seq_file) # Read the test file data
    #    blast_file_path = self.tu.get_job_output_dir() + "/query.fa"
    #    self.tu.save_data_to_file(">INPUT_ID\n"+blast_seq+"\n", blast_file_path) # Write the test file data to a location that can be read by the job (even though the unit test job can read the test files, we test this to ensure that the scripts are reading from the job locations)

    #    blast_data = {"blast_exclude_fragments": test_params["exclude_fragments"]}
    #    if test_params.get("use_seq_file") != None and test_params["use_seq_file"]:
    #        blast_data["sequence_file"] = seq_file
    #    else:
    #        blast_data["blast_sequence"] = blast_seq

    #    self.run_test("option_blast", blast_data, num_seq_data)

    #def run_est_FAMILY(self, test_params, num_seq_data):
    #    fam_name = "PF05544"
    #    fam_data = {"fam_family_name": fam_name, "fam_use_uniref": "none", "fam_exclude_fragments": test_params["exclude_fragments"]}
    #    self.run_test("option_family", fam_data, num_seq_data)

    #def run_est_FASTA(self, test_params, num_seq_data):
    #    fasta_file = self.tu.get_test_data_file("fasta")
    #    fasta_file_job_path = self.tu.get_job_output_dir() + "/input.fa"
    #    fasta_data = {"fasta_file": fasta_file_job_path, "fasta_exclude_fragments": test_params["exclude_fragments"]}
    #    self.run_test("option_fasta", fasta_data, num_seq_data)

    #def run_est_ACCESSION(self, test_params, num_seq_data):
    #    acc_file = self.tu.get_test_data_file("accession")
    #    acc_file_job_path = self.tu.get_job_output_dir() + "/id_list.txt"
    #    acc_data = {"acc_input_file": acc_file_job_path, "acc_exclude_fragments": test_params["exclude_fragments"]}
    #    self.run_test("option_accession", acc_data, num_seq_data)


    def get_blast_test_params(self, test_opts):
        test_blast_seq_file = self.tu.get_test_data_file("blast")
        blast_seq = self.tu.read_data_from_file(test_blast_seq_file) # Read the test file data
        blast_file_path = self.tu.get_job_output_dir() + "/query.fa"
        self.tu.save_data_to_file(">INPUT_ID\n"+blast_seq+"\n", blast_file_path) # Write the test file data to a location that can be read by the job (even though the unit test job can read the test files, we test this to ensure that the scripts are reading from the job locations)

        blast_data = {"blast_exclude_fragments": test_opts[0]}
        if test_opts[1]:
            blast_data["sequence_file"] = blast_file_path
        else:
            blast_data["blast_sequence"] = blast_seq

        return blast_data

    def get_family_test_params(self, test_opts):
        fam_name = "PF05544"
        fam_data = {"fam_family_name": fam_name, "fam_use_uniref": "none", "fam_exclude_fragments": test_opts[0]}
        return fam_data

    def get_fasta_test_params(self, test_opts):
        fasta_file = self.tu.get_test_data_file("fasta")
        fasta_file_job_path = self.tu.get_job_output_dir() + "/input.fa"
        fasta_data = {"fasta_file": fasta_file_job_path, "fasta_exclude_fragments": test_opts[0]}
        return fasta_data

    def get_accession_test_params(self, test_opts):
        acc_file = self.tu.get_test_data_file("accession")
        acc_file_job_path = self.tu.get_job_output_dir() + "/id_list.txt"
        acc_data = {"acc_input_file": acc_file_job_path, "acc_exclude_fragments": test_opts[0]}
        return acc_data


    def run_test(self, option_key, option_data, num_expected):

        db_conf = "/apps/EFIShared/testing_db_conf.sh"
        efi_est_config = "/apps/EST/testing_env_conf.sh"

        run_data = {
                "workspace_name": self.wsName,
                "reads_ref": "70257/2/1",
                "output_name": "EstGenerateApp",
                "efi_db_config": db_conf,
                "efi_est_config": efi_est_config,
            }
        run_data[option_key] = option_data

        ret = self.serviceImpl.run_est_generate_app(
            self.ctx,
            run_data,
        )

        self.assertTrue(ret != None, "No report returned")
        self.assertTrue(isinstance(ret, list), "Report should be a list")
        self.assertTrue(len(ret) > 0, "Report must have at least one element")

        shared_dir = ret[0]["shared_folder"]
        print("OUTPUT DIR IS: " + shared_dir + "\n")
        self.assertTrue(os.path.exists(shared_dir), "Shared directory " + shared_dir + " does not exist.")

        job_dir = os.path.join(shared_dir, "job_temp", "output")
        report_dir = os.path.join(shared_dir, "reports")
        comp_results_file = os.path.join(job_dir, "1.out")
        output_image = os.path.join(report_dir, "length_histogram_uniprot.png")
        if not os.path.isfile(output_image):
            output_image = os.path.join(report_dir, "length_histogram.png")

        self.assertTrue(os.path.exists(job_dir), "Job output directory " + job_dir + " does not exist.")
        self.assertTrue(os.path.exists(report_dir), "Report output directory " + job_dir + " does not exist.")
        self.assertTrue(os.path.isfile(comp_results_file), "Computation failed; results file " + comp_results_file + " does not exist.")
        self.assertTrue(os.path.isfile(output_image), "No output image " + output_image + " was found in report dir")

        num_lines = self.tu.count_lines(comp_results_file)
        num_lines = int(num_lines)
        num_expected = int(num_expected)
        print("Found " + str(num_lines) + " results\n")
        self.assertEqual(num_expected, num_lines, "Number of expected results is not equal to returned results: expected=" + str(num_expected) + " is not equal to computed=" + str(num_lines))

