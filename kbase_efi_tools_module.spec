/*
A KBase module: kbase_efi_tools_module
*/

module kbase_efi_tools_module {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    typedef structure {
        string path;
        string shock_id;
        string name;
        string label;
        string description;
    } File;

    typedef structure {
        string workspace_name;
        int workspace_id;
        string job_name;
        mapping<string, UnspecifiedObject> option_blast;
        mapping<string, UnspecifiedObject> option_family;
        mapping<string, UnspecifiedObject> option_fasta;
        mapping<string, UnspecifiedObject> option_accession;
    } EfiEstAppParams;

    /*
     * The output of the first step in creating an SSN (i.e. "generate").
     * Contains a File and a job label. Also serves as input to the
     * Analysis module.
     * Returned data:
     *     File gen_file - A File object (can be defined multiple ways)
     *     string label - Label of job name
     */
    typedef structure {
        File gen_file;
        string label;
    } GenerateResults;


    /*mapping<string,UnspecifiedObject> params*/
    funcdef run_est_generate_app(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_est_analysis_app(GenerateResults results) returns (ReportResults output) authentication required;
};
