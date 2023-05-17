/*
A KBase module: kbase_efi_tools_module
*/

module kbase_efi_tools_module {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_kbase_efi_tools_module(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
