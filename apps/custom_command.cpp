#include <iostream>
#include <cxxopts.hpp>
#include <filesystem>

#include "collections.h"

int main(int argc, char *argv[]) {

    if(argc < 3) {
        std::cerr << "Wrong usage, it should be:" << std::endl;
        std::cerr << "\t custom_command input_collection.txt command_to_execute [options]" << std::endl;
        std::cerr << "example:" << std::endl;
        std::cerr << "\t custom_command all_CAD_models.txt mv *.step CAD.step" << std::endl;
        return 1;
    }

    std::filesystem::path collection = argv[1];
    std::set<std::filesystem::path> input_folders, subcollections;
    if(expand_collection(collection,input_folders,subcollections)) {
        //an error occured while parsing the collection
        return 1;
    }
    std::cout << "Set of input folders (" << input_folders.size() << " elements):" << std::endl;

    //assemble the command
    std::string command = "";
    for(int i = 2; i < argc; i++) {
        command += std::string(" ") + argv[i];
    }
    
    int returncode = 0;
    for(auto& input_folder : input_folders) {
        std::cout << input_folder.string() << "...";
        //change directory then execute 'command'
        returncode = system( (std::string("cd ")+input_folder.string()+" && "+command).c_str() );
        std::cout << "Finished (returncode=" << returncode << ")" << std::endl;
    }

    return 0;
}