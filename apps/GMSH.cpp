#include <iostream>
#include <fstream>
#include <cxxopts.hpp>
#include <regex>
#include <cstdlib>
#include <ultimaille/all.h>
#include <filesystem>

#include "paths.h"
#include "collections.h"
#include "parameters.h"
#include "trace.h"
#include "date_time.h"
#include "cxxopts_ParseResult_custom.h"
#include "graphite_script.h"
#include "info_file.h"
#include "mesh_stats.h"
#include "user_confirmation.h"

int main(int argc, char *argv[]) {

    //TODO add an option to skip the surface mesh extraction

    cxxopts::Options options(argv[0], "Tetrahedral meshing of a .step geometry file with GMSH algorithm");
    options
        .set_width(80)
        .positional_help("<input> <size> [output]")
        .show_positional_help()
        .add_options()
            ("c,comments", "Comments about the aim of this execution", cxxopts::value<std::string>()->default_value(""),"TEXT")
            ("h,help", "Print help")
            ("i,input", "Path to the input collection/folder", cxxopts::value<std::string>(),"PATH")
            ("n,no-output-collections", "The program will not write output collections for success/error cases")
            ("o,output", "Name of the output folder(s) to create. \%s is replaced by 'size' and \%d by the date and time", cxxopts::value<std::string>()->default_value("GMSH_\%s"),"NAME")
            ("s,size", "Size factor in ]0,1]", cxxopts::value<std::string>(),"VALUE")
            ("v,version", "Print the version (date of last modification) of the underlying executables");
    options.parse_positional({"input", "size", "output"});

    PathList path_list;//read paths.json
    path_list.require(WORKING_DATA_FOLDER);
    path_list.require(GENOMESH);//to extract the surface after

    //parse results
    cxxopts::ParseResult_custom result(options,argc, argv, { "../python-scripts/step2mesh_GMSH.py", path_list[GENOMESH] / "tris_to_tets" });
    result.require({"input", "size"});
    result.require_not_empty({"output"});
    std::filesystem::path input_as_path = normalized_trimed(result["input"]);
    std::string output_folder_name = result["output"];

    DateTimeStr global_beginning;//get current time

    //format the output folder name
    output_folder_name = std::regex_replace(output_folder_name, std::regex("\%s"), result["size"]);
    output_folder_name = std::regex_replace(output_folder_name, std::regex("\%d"), global_beginning.filename_string());

    std::set<std::filesystem::path> input_folders, subcollections;
    if(expand_collection(input_as_path,path_list[WORKING_DATA_FOLDER],DEPTH_1_CAD,input_folders,subcollections)) {
        return 1;
    }
    std::cout << "Found " << input_folders.size() << " input folder(s)" << std::endl;

    //create output collections
    std::string basename = (input_as_path.extension() == ".txt") ? 
                            input_as_path.stem().string() + "_GMSH_" + global_beginning.filename_string() : //if the input is a collection
                            "GMSH"; //if the input is a single folder
    OutputCollections output_collections(basename,path_list,result.is_specified("no-output-collections"));
    output_collections.set_header("GMSH",global_beginning.pretty_string(),result["comments"]);

    std::string cmd;
    int returncode = 0;
    special_case_policy overwrite_policy = ask;
    for(auto& input_folder : input_folders) {
        std::cout << std::filesystem::relative(input_folder,path_list[WORKING_DATA_FOLDER]).string() << "..." << std::flush;
        
        //check if all the input files exist
        if(missing_files_among({
            input_folder / STEP_FILE
        },path_list[WORKING_DATA_FOLDER])) {
            returncode = 1;//do not open Graphite in case of single input
            std::cout << "Missing files" << std::endl;
            output_collections.error_cases->new_comments("missing input files");
            output_collections.error_cases->new_entry(input_folder / output_folder_name);
            continue;
        }
        
        //check if the output files already exist. if so, ask for confirmation
        bool additional_printing = (overwrite_policy==ask);
        if(existing_files_among({
            input_folder / output_folder_name / TETRA_MESH_FILE,
            input_folder / output_folder_name / SURFACE_OBJ_FILE,
            input_folder / output_folder_name / TRIANGLE_TO_TETRA_FILE,
            input_folder / output_folder_name / INFO_JSON_FILE
            //other files (logs.txt, lua script) are not important
        },path_list[WORKING_DATA_FOLDER],additional_printing)) {
            bool user_wants_to_overwrite = ask_for_confirmation("\t-> Are you sure you want to overwrite these files ?",overwrite_policy);
            if(additional_printing) std::cout << std::filesystem::relative(input_folder,path_list[WORKING_DATA_FOLDER]).string() << "..." << std::flush;//re-print the input name
            if(user_wants_to_overwrite==false) {
                returncode = 1;//do not open Graphite in case of single input
                std::cout << "Canceled" << std::endl;
                continue;
            }
            else {
                //because tris_to_tets has not the same behaviour if SURFACE_OBJ_FILE exists,
                //make sure it does not exists
                std::filesystem::remove(input_folder / output_folder_name / SURFACE_OBJ_FILE);
            }
        }
        
        std::filesystem::create_directory(input_folder / output_folder_name);//create the output folder

        std::ofstream txt_logs(input_folder / output_folder_name / STD_PRINTINGS_FILE,std::ios_base::out);
        if(!txt_logs.is_open()) {
            std::cerr << "Error : Failed to open " << (input_folder / output_folder_name / STD_PRINTINGS_FILE).string() << std::endl;
            return 1;
        }

        DateTimeStr current_input_beginning;//get current time
        txt_logs << "\n+-----------------------+";
        txt_logs << "\n|         GMSH          |";
        txt_logs << "\n|  " << current_input_beginning.pretty_string() << "  |";
        txt_logs << "\n+-----------------------+\n\n";
        txt_logs.close();

        cmd = "../python-scripts/step2mesh_GMSH.py " +
              (input_folder / STEP_FILE).string() + " " +
              (input_folder / output_folder_name / TETRA_MESH_FILE).string() + " " +
              result["size"] +
              " &>> " + (input_folder / output_folder_name / STD_PRINTINGS_FILE).string();//redirect stdout and stderr to file (append to the previous logs)
        returncode = system(cmd.c_str());

        if(returncode!=0) {
            std::cout << "Error" << std::endl;
            output_collections.error_cases->new_entry(input_folder / output_folder_name);
            continue;
        }

        //also extract the surface
        cmd = (path_list[GENOMESH] / "tris_to_tets").string() + " " +
              (input_folder / output_folder_name / TETRA_MESH_FILE).string() + " " +
              (input_folder / output_folder_name / SURFACE_OBJ_FILE).string() + " " +
              (input_folder / output_folder_name / TRIANGLE_TO_TETRA_FILE).string() +
              " &>> " + (input_folder / output_folder_name / STD_PRINTINGS_FILE).string();//redirect stdout and stderr to file (append to the previous logs)
        returncode = system(cmd.c_str());
        if(returncode!=0) {
            std::cout << "Error" << std::endl;
            output_collections.error_cases->new_entry(input_folder / output_folder_name);
            continue;
        }
        else {
            std::cout << "Done" << std::endl;
            output_collections.success_cases->new_entry(input_folder / output_folder_name);

            //compute mesh stats
            TetraMeshStats mesh_stats(input_folder / output_folder_name / TETRA_MESH_FILE,
                                      input_folder / output_folder_name / SURFACE_OBJ_FILE);

            // write info.json
            TetraMeshInfo info(input_folder / output_folder_name / INFO_JSON_FILE);
            info.generated_by("GMSH");
            info.comments(result["comments"]);
            info.date(current_input_beginning.pretty_string());
            info.fill_from(mesh_stats);
            info.size_factor_of("GMSH",std::stof(result["size"]));//no need to check if an exception is raised, step2mesh_GMSH would fail before

            //then create a Lua script for Graphite
            GraphiteScript graphite_script(input_folder / output_folder_name / TETRA_MESH_LUA_SCRIPT,path_list);
            graphite_script.add_comments("generated by the GMSH wrapper of shared-polycube-pipeline");
            graphite_script.add_comments(current_input_beginning.pretty_string());
            graphite_script.hide_text_editor();
            graphite_script.load_object(TETRA_MESH_FILE);
            graphite_script.set_mesh_style(true,0,0,0,1);//black wireframe
            graphite_script.set_surface_style(false,0.5,0.5,0.5);//hide surface
            graphite_script.set_visible(false);//hide the tetra mesh. else overlaying the surface mesh
            graphite_script.load_object(SURFACE_OBJ_FILE);
            graphite_script.set_mesh_style(true,0,0,0,1);//black wireframe
        }
    }

    //in case of a single input folder, open the tetra mesh and the surface mesh with Graphite
#ifdef OPEN_GRAPHITE_AT_THE_END
    if(input_folders.size()==1 && returncode==0) { //TODO if returncode!=0, open the logs
        // TODO check if TETRA_MESH_LUA_SCRIPT and GRAPHITE_BASH_SCRIPT were successfully created
        cmd = "cd " + (*input_folders.begin() / output_folder_name).string() + " && ./" + GRAPHITE_BASH_SCRIPT + " > /dev/null";//silent output
        system(cmd.c_str());
    }
#endif

    return 0;
}