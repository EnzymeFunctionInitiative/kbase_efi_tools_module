
import os
import re
import shutil


class EfiTestUtils:

    def __init__(self, cls):
        self.cls = cls
        self.load_test_info(cls)
        cls.test_data_dir = self.get_data_dir_path()

    def load_test_info(self, cls):
        data_dir = self.get_data_dir_path()
        num_seq_file = data_dir + "/expected_seq.txt"
        excl_frag_num_seq_data = {}
        with_frag_num_seq_data = {}
        if os.path.isfile(num_seq_file):
            with open(num_seq_file) as fh:
                line = fh.readline()
                while line:
                    mx = re.search(r"^num_expected_no_fragments\t([^\t]+)\t(\d+)\s*$", line)
                    if mx != None:
                        excl_frag_num_seq_data[mx.group(1)] = mx.group(2)
                    else:
                        mx = re.search(r"^num_expected_fragments\t([^\t]+)\t(\d+)\s*$", line)
                        if mx != None:
                            with_frag_num_seq_data[mx.group(1)] = mx.group(2)
                    line = fh.readline()

        cls.excl_frag_num_seq_data = excl_frag_num_seq_data
        cls.with_frag_num_seq_data = with_frag_num_seq_data

    ###############################################################################################
    # UTILITY/MISC METHODS

    def count_lines(self, file_path):
        lc = 0
        with open(file_path, "r") as fh:
            line = fh.readline()
            while line:
                lc = lc + 1
                line = fh.readline()
        return lc

    def read_data_from_file(self, file_path):
        with open(file_path, "r") as fh:
            contents = fh.read()
            return contents

    def save_data_to_file(self, contents, file_path):
        with open(file_path, "w") as fh:
            fh.write(contents)

    def get_test_data_file(self, file_type):
        data_dir = self.get_data_dir_path()
        if data_dir == None: return None

        if file_type == "fasta":
            file_path = data_dir + "/PF05544_sp.fasta"
        elif file_type == "accession":
            file_path = data_dir + "/PF05544_sp.id_list.txt"
        elif file_type == "blast":
            file_path = data_dir + "/blast_seq.fa"
        else:
            return None

        if os.path.isfile(file_path):
            return file_path
        else:
            return None

        return file_path

    def get_data_dir_path(self):
        conf_file = "/apps/EFIShared/testing_db_conf.sh"
        data_path = None
        with open(conf_file, "r") as fh:
            line = fh.readline()
            while line and not data_path:
                rx = re.search("^export EFI_DB=(.+)/[^/]+$", line)
                if rx != None:
                    data_path = rx.group(1)
                line = fh.readline()
        return data_path

    def prep_job_dir(self):
        output_dir = self.get_job_output_dir()
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)

    def get_job_output_dir(self):
        # This is where the EST jobs put their output data
        output_dir = self.cls.scratch + "/job"
        return output_dir


