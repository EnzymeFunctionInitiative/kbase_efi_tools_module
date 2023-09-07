/*
@author chenry
*/
module SequenceSimilarityNetworks {
	typedef int bool;

	/*
		Reference to a handle to the GFF file on shock
		@id handle
	*/
	typedef string handle_ref;

	/*
		Reference to a model template
		@id ws KBaseSequences.ProteinSequenceSet KBaseSequences.DNASequenceSet
	*/
	typedef string sequenceset_ref;
	
	/*
		Reference to a model template
		@id ws SequenceSimilarityNetworks.Network
	*/
	typedef string network_ref;
	
	/*
		Reference to a model template
		@id ws SequenceSimilarityNetworks.ComputedProteinSims
	*/
	typedef string similarity_ref;


	/*
		* The output of the first step in creating an SSN (i.e. "generate").
		* Contains a File and a job label. Also serves as input to the
		* Analysis module.
		* Returned data:
		*     File gen_file - A File object (can be defined multiple ways)
		*     string label - Label of job name
	
		@metadata ws input_type as Input type
		@optional  ids_in_pfam_family ids_in_pfam_family
	*/
	typedef structure {
		handle_ref gen_file;
		sequenceset_ref sequenceset;
		int input_sequence_count;
	
		string input_type;
		string input_family_id;
		float evalue_for_ssh_calculation;
		bool domain_option;
		bool exlude_fragments;
	
		string database_version;
		int uniref_version;
	
		int ids_in_pfam_family;
		int cluster_ids_in_uniref_family;
		int total_sequences_in_dataset;
		int total_edges;
		int unique_sequences;
	
		float convergence_ratio;
	} ComputedProteinSims;
	
	
	
	/*
		* An SSN. Each SsnFile contains a single file. A list of these are
		* the output of the ("analysis" step).
		* Returned data:
		*     int repnode_val - A value that represents the factor that was
		*                       used by CD-HIT to group nodes by similarity
		*     File file - A File object that represents an SSN
	
		@metadata ws node_count as Node count
		@metadata ws edge_count as Edge count
		@metadata ws repnode_identity as Identity
	*/
	typedef structure {
		int repnode_identity;
		similarity_ref precomputed_similarities;
		handle_ref file;
		int node_count;
		int edge_count;
		network_ref network;
	} SequenceSimilarityNetwork;
	
	typedef structure {
		string id;
		string type;/*GENE|SPECIES|COMPOUND*/
		list<string> aliases;
		mapping<string ontology,list<tuple<string id,string name>>> annotations;
		mapping<string score_type,float score> scores;
	} Node;

	typedef structure {
		string id;
		string type;/*SIM|FLUX|INT*/
		string start_id;
		string end_id;
		bool bidirectional;
		mapping<string ontology,list<tuple<string id,string name>>> annotations;
		mapping<string score_type,float score> scores;
	} Edge;

	typedef structure {
		string default_node_type;
		string default_edge_type;
		list<Node> nodes;
		list<Edge> edges;
	} NetworkData;

	/*	
		Network datatype
		
		@metadata ws name as Name
		@metadata ws type as Type
		@metadata ws node_count as Node count
		@metadata ws edge_count as Edge count
		@optional full_data
	*/
	typedef structure {
		string name;
		string type;/*SSN|IGN|MGN|SSN*/
		int node_count;
		int edge_count;
		list<string> node_ontologies;
		list<string> edge_ontologies;
		list<string> node_types;
		list<string> edge_types;
		NetworkData default_data;
		handle_ref full_data;
		string default_node;
	} Network;

	/*	
		Network View datatype design to save state on network views
	*/
	typedef structure {
		network_ref network_ref;
		NetworkData overlay_data;
	} NetworkView;

};
