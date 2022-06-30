#include <iostream>
#include <fstream>
#include <cxxopts.hpp>
#include <ultimaille/all.h>

#include "collections.h"
#include "paths.h"
#include "parameters.h"
#include "date_time.h"
#include "cxxopts_ParseResult_custom.h"
#include "graphite_script.h"

int main(int argc, char *argv[]) {

    cxxopts::Options options(argv[0], "Compute a naive labeling based on the per-triangle closest direction");
    options
        .set_width(80)
        .positional_help("<input> [output]")
        .show_positional_help()
        .add_options()
            ("c,comments", "Comments about the aim of this execution", cxxopts::value<std::string>()->default_value(""),"TEXT")
            ("h,help", "Print help")
            ("i,input", "Path to the input collection", cxxopts::value<std::string>(),"PATH")
            ("n,no-output-collections", "The program will not write output collections for success/error cases")
            ("o,output", "Name of the output folder(s) to create. \%d is replaced by the date and time", cxxopts::value<std::string>()->default_value("naive"),"NAME");
    options.parse_positional({"input","output"});

    //parse results
    cxxopts::ParseResult_custom result(options,argc, argv);
    result.require({"input"});
    result.require_not_empty({"output"});
    std::filesystem::path input_as_path(result["input"]);
    std::string output_folder_name = result["output"];
    bool write_output_collections = !result.is_specified("no-output-collections");

    PathList path_list;//read paths.json
    path_list.require(GENOMESH);

    std::set<std::filesystem::path> input_folders, subcollections;
    if(expand_collection(input_as_path,input_folders,subcollections)) {
        //an error occured
        return 1;
    }
    std::cout << "Found " << input_folders.size() << " input folder(s)" << std::endl;

    DateTimeStr global_beginning;//get current time

    OutputCollection *success_cases, *error_cases;
    if(write_output_collections) {

        //create the ouput collection files
        std::string output_success_collection_filename, output_error_collection_filename;
        if(input_as_path.extension() == ".txt") {
            //create a collection '<input_collection>_naive_<date>'
            output_success_collection_filename = input_as_path.stem().string() + "_naive_" + global_beginning.filename_string();
        }
        else {
            //case of a single folder as input
            //append to collection 'naive_labeling'
            output_success_collection_filename = "naive_labeling";
        }
        output_error_collection_filename = output_success_collection_filename + "_errors";

        success_cases = new OutputCollection(output_success_collection_filename,path_list,NOTIFY);
        error_cases = new OutputCollection(output_error_collection_filename,path_list,NOTIFY);
        success_cases->new_line();
        success_cases->new_comments("Generated by naive_labeling");
        success_cases->new_comments(global_beginning.pretty_string());
        error_cases->new_line();
        error_cases->new_comments("Generated by naive_labeling");
        error_cases->new_comments(global_beginning.pretty_string());
        if(!result["comments"].empty()) {
            success_cases->new_comments(result["comments"]);
            error_cases->new_comments(result["comments"]);
        }
    }

    //format the output folder name
    output_folder_name = std::regex_replace(output_folder_name, std::regex("\%d"), global_beginning.filename_string());

    std::string cmd;
    int returncode = 0;
    for(auto& input_folder : input_folders) {
        std::cout << input_folder.string() << "..." << std::flush;
        //TODO check if the output folder already exist. if so, ask for confirmation

        std::filesystem::create_directory(input_folder / output_folder_name);//create the output folder

        std::ofstream txt_logs(input_folder / output_folder_name / STD_PRINTINGS_FILE,std::ios_base::app);//append mode
        if(!txt_logs.is_open()) {
            std::cerr << "Error : Failed to open " << (input_folder / output_folder_name / STD_PRINTINGS_FILE).string() << std::endl;
            return 1;
        }

        DateTimeStr current_input_beginning;//get current time
        txt_logs << "\n+-----------------------+";
        txt_logs << "\n|    naive_labeling     |";
        txt_logs << "\n|  " << current_input_beginning.pretty_string() << "  |";
        txt_logs << "\n+-----------------------+\n\n";
        txt_logs.close();

        cmd = (path_list[GENOMESH] / "build/naive_labeling").string() + " " +
              (input_folder / TRIANGLE_TO_TETRA_FILE).string() + " " +
              (input_folder / SURFACE_OBJ_FILE).string() + " " +
              (input_folder / output_folder_name / PER_SURFACE_TRIANGLE_LABELING_FILE).string() + " " +
              (input_folder / output_folder_name / PER_TETRA_FACES_LABELING_FILE).string() +
              " &>> " + (input_folder / output_folder_name / STD_PRINTINGS_FILE).string();//redirect stdout and stderr to file (append to the logs of step2mesh)
        returncode = system(cmd.c_str());
        
        if(returncode!=0) {
            std::cout << "Error" << std::endl;
            if(write_output_collections) {
                error_cases->new_entry(input_folder / output_folder_name);
            }
            continue;
        }

        std::cout << "Done" << std::endl;

        if(write_output_collections) {
            success_cases->new_entry(input_folder / output_folder_name);
        }

        //with Ultimaille, load the surface mesh and the just-computed labeling
        UM::Triangles surface;
        UM::read_by_extension( (input_folder / SURFACE_OBJ_FILE).string() , surface);
        UM::FacetAttribute<int> labeling(surface);
        //fill labeling
        std::ifstream ifs(input_folder / output_folder_name / PER_SURFACE_TRIANGLE_LABELING_FILE);
        if(ifs.is_open()) {
            int label, face_number = 0;
            while (ifs >> label) {
                labeling[face_number] = label;
                face_number++;
            }
            ifs.close();

            //write a .geogram file with the surface mesh + labeling, named "attr", as UM::SurfaceAttributes
            //inspired by Trace::drop_facet_scalar()
            UM::write_by_extension( (input_folder / output_folder_name / LABELED_SURFACE_GEOGRAM_FILE).string() , surface, UM::SurfaceAttributes{ {}, { { "attr", labeling.ptr } }, {} });

            //then create a Lua script for Graphite
            GraphiteScript graphite_script(input_folder / output_folder_name / LABELED_SURFACE_LUA_SCRIPT, path_list);
            graphite_script.add_comments("generated by naive_labeling");
            graphite_script.add_comments(current_input_beginning.pretty_string());
            graphite_script.load_object(LABELED_SURFACE_GEOGRAM_FILE);
            graphite_script.set_mesh_style(true,0.0f,0.0f,0.0f,1);
            graphite_script.set_painting_on_attribute("attr","french",0.0f,5.0f);
            graphite_script.set_lighting(false);
        }
        // TODO else, write that the PER_SURFACE_TRIANGLE_LABELING_FILE could not be opened in STD_PRINTINGS_FILE
    }

    // TODO in case of a single input folder, open the labeling with Graphite
#ifdef OPEN_GRAPHITE_AT_THE_END
    if(input_folders.size()==1 && returncode==0) { //TODO if returncode!=0, open the logs
        // TODO check if LABELED_SURFACE_LUA_SCRIPT and GRAPHITE_BASH_SCRIPT were successfully created
        cmd = "cd " + (*input_folders.begin() / output_folder_name).string() + " && ./" + GRAPHITE_BASH_SCRIPT + " > /dev/null";//silent output
        system(cmd.c_str());
    }
#endif

    return 0;
}