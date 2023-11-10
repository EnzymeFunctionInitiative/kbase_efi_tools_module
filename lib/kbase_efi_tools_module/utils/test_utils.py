
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
        self.excl_frag_num_seq_data = excl_frag_num_seq_data
        self.with_frag_num_seq_data = with_frag_num_seq_data

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
            file_path = os.path.join(data_dir, "PF05544_sp.fasta")
        elif file_type == "accession":
            file_path = os.path.join(data_dir, "PF05544_sp.id_list.txt")
        elif file_type == "blast":
            file_path = os.path.join(data_dir, "blast_seq.fa")
        elif file_type == "data_transfer":
            file_path = os.path.join(data_dir, "data_transfer.zip")
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
            print(line)
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


    def get_expected(self, test_opts):
        res_type = test_opts[len(test_opts) - 1]
        exclude_fragments = test_opts[0]
        expected = self.excl_frag_num_seq_data[res_type] if exclude_fragments else self.with_frag_num_seq_data[res_type]
        return expected


    def get_blast_test_params(self, test_opts):
        test_blast_seq_file = self.get_test_data_file("blast")
        blast_seq = self.read_data_from_file(test_blast_seq_file) # Read the test file data
        blast_file_path = self.get_job_output_dir() + "/query.fa"
        self.save_data_to_file(">INPUT_ID\n"+blast_seq+"\n", blast_file_path) # Write the test file data to a location that can be read by the job (even though the unit test job can read the test files, we test this to ensure that the scripts are reading from the job locations)

        blast_data = {"blast_exclude_fragments": test_opts[0]}
        if test_opts[1]:
            blast_data["sequence_file"] = blast_file_path
        else:
            blast_data["blast_sequence"] = blast_seq

        return blast_data

    def get_blast_test_params(self, test_opts):
        test_blast_seq_file = self.get_test_data_file("blast")
        blast_seq = self.read_data_from_file(test_blast_seq_file) # Read the test file data
        blast_file_path = self.get_job_output_dir() + "/query.fa"
        self.save_data_to_file(">INPUT_ID\n"+blast_seq+"\n", blast_file_path) # Write the test file data to a location that can be read by the job (even though the unit test job can read the test files, we test this to ensure that the scripts are reading from the job locations)

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
        fasta_file = self.get_test_data_file("fasta")
        fasta_file_job_path = self.get_job_output_dir() + "/input.fa"
        fasta_data = {"fasta_file": fasta_file_job_path, "fasta_exclude_fragments": test_opts[0]}
        return fasta_data

    def get_accession_test_params(self, test_opts):
        acc_file = self.get_test_data_file("accession")
        acc_file_job_path = self.get_job_output_dir() + "/id_list.txt"
        acc_data = {"acc_input_file": acc_file_job_path, "acc_exclude_fragments": test_opts[0]}
        return acc_data


    def get_blast_test_params(self, test_opts):
        test_blast_seq_file = self.get_test_data_file("blast")
        blast_seq = self.read_data_from_file(test_blast_seq_file) # Read the test file data
        blast_file_path = self.get_job_output_dir() + "/query.fa"
        self.save_data_to_file(">INPUT_ID\n"+blast_seq+"\n", blast_file_path) # Write the test file data to a location that can be read by the job (even though the unit test job can read the test files, we test this to ensure that the scripts are reading from the job locations)

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
        fasta_file = self.get_test_data_file("fasta")
        fasta_file_job_path = self.get_job_output_dir() + "/input.fa"
        fasta_data = {"fasta_file": fasta_file_job_path, "fasta_exclude_fragments": test_opts[0]}
        return fasta_data

    def get_accession_test_params(self, test_opts):
        acc_file = self.get_test_data_file("accession")
        acc_file_job_path = self.get_job_output_dir() + "/id_list.txt"
        acc_data = {"acc_input_file": acc_file_job_path, "acc_exclude_fragments": test_opts[0]}
        return acc_data


