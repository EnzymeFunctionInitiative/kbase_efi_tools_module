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

/*
    typedef structure {
        string workspace_name;
        int workspace_id;
        string job_name;
        mapping<string, UnspecifiedObject> option_blast;
        mapping<string, UnspecifiedObject> option_family;
        mapping<string, UnspecifiedObject> option_fasta;
        mapping<string, UnspecifiedObject> option_accession;
    } EfiEstAppParams;
*/

    funcdef run_est_generate_app(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_est_analysis_app(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;
};
