#!/usr/bin/env python

# ./dds.py typeof path/to/folder
# ./dds.py run algo_name path/to/folder

from pathlib import Path
import yaml
import logging
from argparse import ArgumentParser
from typing import Optional
import time
from icecream import ic
from os import mkdir

def translate_filename_keyword(filename_keyword: str) -> str:
    for YAML_filepath in [x for x in Path('data_subfolder_types').iterdir() if x.is_file() and x.suffix == '.yml' and x.stem.count('.') == 0]:
        with open(YAML_filepath) as YAML_stream:
            YAML_content = yaml.safe_load(YAML_stream)
            if filename_keyword in YAML_content['filenames']:
                return YAML_content['filenames'][filename_keyword]
    logging.error(f"None of the data subfolder types declare the '{filename_keyword}' filename keyword")
    exit(1)

def is_instance_of(path: Path, data_subfolder_type: str) -> bool:
    YAML_filepath: Path = Path('data_subfolder_types') / (data_subfolder_type + '.yml')
    if not YAML_filepath.exists():
        logging.error(f'{YAML_filepath} does not exist')
        exit(1)
    with open(YAML_filepath) as YAML_stream:
        YAML_content = yaml.safe_load(YAML_stream)
        if 'distinctive_content' not in YAML_content:
            logging.error(f"{YAML_filepath} has no 'distinctive_content' entry")
            exit(1)
        if 'filenames' not in YAML_content:
            logging.error(f"{YAML_filepath} has no 'filenames' entry")
            exit(1)
        for distinctive_content in YAML_content['distinctive_content']:
            if distinctive_content not in YAML_content['filenames']:
                logging.error(f"{YAML_filepath} has no 'filenames'/'{distinctive_content}' entry, despite being referenced in the 'distinctive_content' entry")
                exit(1)
            filename = YAML_content['filenames'][distinctive_content]
            if (path / filename).exists():
                return True # at least one of the distinctive content exist
    return False

def type_inference(path: Path) -> Optional[str]:
    recognized_types = list()
    for type_str in [x.stem for x in Path('data_subfolder_types').iterdir() if x.is_file() and x.suffix == '.yml' and x.stem.count('.') == 0]: # Path.stem is Path.name without suffix
        if is_instance_of(path,type_str):
            recognized_types.append(type_str)
    if len(recognized_types) == 0:
        return None
    if len(recognized_types) > 1:
        logging.error(f"Several data folder types recognize the folder {path}")
        exit(1)
    return recognized_types[0]

class DataFolder():

    def __init__(self,path: Path):
        self.path: Path = path
        self.type: str = type_inference(path)
        if self.type is None:
            logging.error(f'No data_subfolder_type/* recognize {self.type}')
            exit(1)
        
    def auto_generate_missing_file(self, filename_keyword: str):
        # Idea : parse all algorithms until we found one where 'filename_keyword' is an output file
        # and where
        # - the algo is transformative (it doesn't create a subfolder)
        # - there is no 'others' in 'arguments' (non-parametric algorithm)
        # if we have all the input files, just execute the algorithm
        # else exit with failure
        # Can be improve with recursive call on the input files, and dict to cache the map between output file and algorithm
        for YAML_algo_filename in [x for x in Path('data_subfolder_types').iterdir() if x.is_file() and x.suffix == '.yml']:
            with open(YAML_algo_filename) as YAML_stream:
                YAML_content = yaml.safe_load(YAML_stream)
                if self.type not in YAML_content:
                    # the input folder of this algo is of different type than self
                    continue # parse next YAML algo definition
                if 'output_folder' in YAML_content[self.type]:
                    # we found a generative algorithm (it creates a subfolder)
                    continue # parse next YAML algo definition
                if filename_keyword in YAML_content[self.type]['arguments']['output_files']:
                    # we found an algorithm whose 'filename_keyword' is one of the output file
                    # check existence of input files
                    for input_file in [self.get_file(input_filename_keyword, False) for input_filename_keyword in YAML_content[self.type]['arguments']['input_files']]:
                        if not input_file.exists():
                            logging.error(f"Cannot auto-generate missing file {filename_keyword} in {self.path}")
                            logging.error(f"Found algorithm '{YAML_algo_filename.stem}' to generate it")
                            logging.error(f"but input file '{input_file.stem}' is also missing.")
                            exit(1)
                    # all input files exist
                    # self.run(YAML_algo_filename.stem)
                else:
                    # this transformative algorithm does not create the file we need
                    continue # parse next YAML algo definition

        
    def get_file(self, filename_keyword: str, must_exist: bool = False) -> Path:
        # transform filename keyword into actual filename by reading the YAML describing the data subfolder type
        YAML_filepath: Path = Path('data_subfolder_types') / (self.type + '.yml')
        if not YAML_filepath.exists():
            logging.error(f'{YAML_filepath} does not exist')
            exit(1)
        with open(YAML_filepath) as YAML_stream:
            YAML_content = yaml.safe_load(YAML_stream)
            if 'filenames' not in YAML_content:
                logging.error(f"{YAML_filepath} has no 'filenames' entry")
                exit(1)
            if filename_keyword not in YAML_content['filenames']:
                logging.error(f"{YAML_filepath} has no 'filenames'/'{filename_keyword}' entry")
                exit(1)
            path = (self.path / YAML_content['filenames'][filename_keyword]).absolute()
            if (not must_exist) or (must_exist and path.exists()):
                return path
            self.auto_generate_missing_file(filename_keyword)
            if path.exists():
                return path # successful auto-generation
            raise Exception(f'Missing file {path}')

    def run(self,algo_name: str):
        YAML_filepath: Path = Path('algorithms') / (algo_name + '.yml')
        if not YAML_filepath.exists():
            logging.error(f"Cannot run '{algo_name}' because {YAML_filepath} does not exist")
            exit(1)
        with open(YAML_filepath) as YAML_stream:
            YAML_content = yaml.safe_load(YAML_stream)
            if self.type not in YAML_content:
                logging.error(f"Behavior of {YAML_filepath} is not specified for input data folders of type '{self.type}', like {self.path} is")
                exit(1)
            # retrieve info about underlying executable
            if 'executable' not in YAML_content[self.type]:
                logging.error(f"{YAML_filepath} has no '{self.type}/executable' entry")
                exit(1)
            if 'path' not in YAML_content[self.type]['executable']:
                logging.error(f"{YAML_filepath} has no '{self.type}/executable/path' entry")
                exit(1)
            path_keyword = YAML_content[self.type]['executable']['path']
            if 'command_line' not in YAML_content[self.type]['executable']:
                logging.error(f"{YAML_filepath} has no '{self.type}/executable/command_line' entry")
                exit(1)
            with open('paths.yml') as paths_stream:
                paths = yaml.safe_load(paths_stream)
                if path_keyword not in paths:
                    logging.error(f"'{path_keyword}' is referenced in {YAML_filepath} at '{self.type}/executable/path' but does not exist in paths.yml")
                    exit(1)
            executable_path: Path = Path(paths[path_keyword]).expanduser()
            if not executable_path.exists():
                logging.error(f"In paths.yml, '{path_keyword}' reference a non existing path, required by {YAML_filepath} algorithm")
                logging.error(f"({executable_path})")
                exit(1)
            executable_filename = None
            if 'filename' in YAML_content[self.type]['executable']:
                executable_filename = YAML_content[self.type]['executable']['filename']
                executable_path = executable_path / executable_filename
            if not executable_path.exists():
                logging.error(f"There is no {executable_filename} in {paths[path_keyword]}. Required by {YAML_filepath} algorithm")
                exit(1)
            print(f"Running '{algo_name}' -> executing {executable_path}")
            # assemble dict of 'others' arguments
            all_arguments = dict()
            if 'arguments' not in YAML_content[self.type]:
                logging.error(f"{YAML_filepath} has no '{self.type}/arguments' entry")
                exit(1)
            if 'others' in YAML_content[self.type]['arguments']:
                for other_argument in YAML_content[self.type]['arguments']['others']:
                    if other_argument in all_arguments:
                        logging.error(f"{YAML_filepath} has multiple arguments named '{input_file_argument}' in '{self.type}/arguments")
                        exit(1)
                    all_arguments[other_argument] = YAML_content[self.type]['arguments']['others'][other_argument]['default']
            # get current date and time
            start_datetime: time.struct_time = time.localtime()
            start_datetime_iso: str = time.strftime('%Y-%m-%dT%H:%M:%SZ', start_datetime) # ISO 8601
            start_datetime_filesystem: str = time.strftime('%Y%m%d_%H%M%S', start_datetime) # no ':' for the string to be used in a filename
            # find out if it's a transformative or a generative algorithm (edit a DataFolder or create a sub-DataFolder)
            output_folder_path: Optional[Path] = None
            if 'output_folder' in YAML_content[self.type]:
                output_folder = YAML_content[self.type]['output_folder']
                output_folder = output_folder.format(**all_arguments).replace('%d',start_datetime_filesystem)
                output_folder_path = self.path / output_folder
                if output_folder_path.exists():
                    logging.error(f"The output folder to create ({output_folder_path}) already exists")
                    exit(1)
                mkdir(output_folder_path)
            # add 'input_files' and 'output_files' arguments to the 'all_arguments' dict
            if 'input_files' not in YAML_content[self.type]['arguments']:
                logging.error(f"{YAML_filepath} has no '{self.type}/arguments/input_files' entry")
                exit(1)
            if 'output_files' not in YAML_content[self.type]['arguments']:
                logging.error(f"{YAML_filepath} has no '{self.type}/arguments/output_files' entry")
                exit(1)
            for input_file_argument in YAML_content[self.type]['arguments']['input_files']:
                if input_file_argument in all_arguments:
                    logging.error(f"{YAML_filepath} has multiple arguments named '{input_file_argument}' in '{self.type}/arguments")
                    exit(1)
                input_file_path = self.get_file(YAML_content[self.type]['arguments']['input_files'][input_file_argument], True)
                all_arguments[input_file_argument] = input_file_path
            for output_file_argument in YAML_content[self.type]['arguments']['output_files']:
                if output_file_argument in all_arguments:
                    logging.error(f"{YAML_filepath} has multiple arguments named '{output_file_argument}' in '{self.type}/arguments")
                    exit(1)
                output_file_path = None
                if output_folder_path is None: # case transformative algorithm, no output folder created
                   output_file_path = self.get_file(YAML_content[self.type]['arguments']['output_files'][output_file_argument], False)
                else: # case generative algorithm
                   output_file_path = output_folder_path / translate_filename_keyword(YAML_content[self.type]['arguments']['output_files'][output_file_argument])
                all_arguments[output_file_argument] = output_file_path
            ic(all_arguments)
            
            

if __name__ == "__main__":
    
    parser = ArgumentParser(
        prog='dds',
        description='Semantic data folders'
    )
    
    parser.add_argument(
        'action',
        choices = ['typeof', 'run']
    )
    
    parser.add_argument(
        'supp_args',
        nargs='*'
    )

    args = parser.parse_args()

    if args.action == 'typeof':
        assert(len(args.supp_args)==1)
        print(type_inference(Path(args.supp_args[0])))
    elif args.action == 'run':
        assert(len(args.supp_args)==2)
        algo = args.supp_args[0]
        path = Path(args.supp_args[1])
        data_folder = DataFolder(path)
        data_folder.run(algo)

