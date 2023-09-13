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

# From the lib/kbase_efi_tools_module directory
from kbase_efi_tools_module.utils.test_utils import EfiTestUtils
from kbase_efi_tools_module.est.est_generate import EstGenerateJob



def get_streams(process):
    """
    Returns decoded stdout,stderr after loading the entire thing into memory
    """
    stdout, stderr = process.communicate()
    return (stdout.decode("utf-8", "ignore"), stderr.decode("utf-8", "ignore"))


class est_standaloneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tu = EfiTestUtils(cls)
        #TODO: make this a config variable
        est_home = '/apps/EST'
        cls.est_dir = est_home

    @classmethod
    def tearDownClass(cls):
        return

#    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
#    # @unittest.skip("Skip test for debugging")
#    @parameterized.expand([
##                           ("blast,ex_frag,use_file", True, True),
##                           ("blast,ex_frag,no_file", True, False),
##                           ("blast,frag,use_file", False, True),
#                           ("blast,frag,no_file", False, False)
#                           ])
#    def test_est_generate_blast(self, name, exclude_fragments, use_file):
#
#        option = "blast"
#        test_opts = [exclude_fragments, use_file, option]
#        test_params = self.tu.get_blast_test_params(test_opts)
#        expected = self.tu.get_expected(test_opts)
#        logging.info("RUNNING TEST " + name)
#        self.run_test("option_" + option, test_params, expected)
#        return True

    @parameterized.expand([
                           ("family,ex_frag", True),
                           ("family,frag", False)
                           ])
    def test_est_generate_family(self, name, exclude_fragments):

        option = "family"
        test_opts = [exclude_fragments, option]
        test_params = self.tu.get_family_test_params(test_opts)
        expected = self.tu.get_expected(test_opts)
        logging.info("RUNNING TEST " + name)
        self.run_test("option_" + option, test_params, expected)
        return True

    def run_test(self, option_key, option_data, num_expected):

        db_conf = "/apps/EFIShared/testing_db_conf.sh"
        efi_est_config = "/apps/EST/testing_env_conf.sh"

        process_params = {'type': '', 'exclude_fragments': False}
        #self.tu.get_blast_params(params, process_params)
        self.tu.get_family_params(params, process_params)
        #self.tu.get_fasta_params(params, process_params)
        #self.tu.get_accession_params(params, process_params)

        run_data = {
                "efi_db_config": db_conf,
                "efi_est_config": efi_est_config,
                "output_dir": output_dir,
            }
        run_data[option_key] = option_data

        script_file = self.create_job(run_data, process_params)

#        self.assertTrue(script_file != None, "No report returned")
#        self.assertTrue(isinstance(ret, list), "Report should be a list")
#        self.assertTrue(len(ret) > 0, "Report must have at least one element")
#
#        output_dir = ret[0]["shared_folder"]
#        print("OUTPUT DIR IS: " + output_dir + "\n")
#        self.assertTrue(os.path.exists(output_dir), "Shared directory " + output_dir + " does not exist.")

        job_dir = os.path.join(output_dir, "job_temp", "output")
        report_dir = os.path.join(output_dir, "reports")
        comp_results_file = os.path.join(job_dir, "1.out")
        output_image = os.path.join(report_dir, "length_histogram_uniprot.png")
        if not os.path.isfile(output_image):
            output_image = os.path.join(report_dir, "length_histogram.png")

        self.assertTrue(os.path.exists(job_dir), "Job output directory " + job_dir + " does not exist.")
        self.assertTrue(os.path.exists(report_dir), "Report output directory " + job_dir + " does not exist.")
        self.assertTrue(os.path.isfile(comp_results_file), "Computation failed; results file " + comp_results_file + " does not exist.")
        self.assertTrue(os.path.isfile(output_image), "No output image " + output_image + " was found in report dir")

        num_lines = self.count_lines(comp_results_file)
        num_lines = int(num_lines)
        num_expected = int(num_expected)
        print("Found " + str(num_lines) + " results\n")
        self.assertEqual(num_expected, num_lines, "Number of expected results is not equal to returned results: expected=" + str(num_expected) + " is not equal to computed=" + str(num_lines))

    def create_job(self, params, process_params):

        #TODO: est_dir
        create_job_pl = os.path.join(self.est_dir, 'create_job.pl')

        self.est_env = [params['efi_est_config'], '/apps/EFIShared/env_conf.sh', '/apps/env.sh', '/apps/blast_legacy.sh', params['efi_db_config']]
        process_args = ['--job-dir', self.output_dir]

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

