#!/usr/bin/env python

# post-processing for rb_generate_quantization.yml

from shutil import move
from pathlib import Path
from os import unlink

# own module
from dds import *

def post_processing(input_subfolder: DataFolder, output_subfolder: Optional[Path], arguments: dict, data_from_pre_processing: dict, silent_output: bool):
    assert(input_subfolder.type == 'labeling')
    assert(output_subfolder is not None)

    # The executable also writes debug files
    for debug_filename in [
        'debug_volume_0.geogram',
        'debug_polycuboid_1.geogram',
        'debug_flagging_2.geogram',
        'debug_corrected_flagging_3.geogram',
        'debug_charts_dim_0__4.geogram',
        'debug_charts_dim_1__5.geogram',
        'debug_charts_dim_2__6.geogram',
        'debug_Blocks_on_mesh_7.geogram',
        'debug_Blocks_blocks_8.geogram',
        'debug_Blocks_on_polycuboid_9.geogram',
        'debug_Blocks_on_polycube_10.geogram',
        'debug_coarsehexmesh_11.geogram',
        'debug_coarsehexmesh_charts_12.geogram',
        'debug_polycubehexmesh_13.geogram',
        'debug_polycubehexmesh_charts_14.geogram',
        'debug_hexmesh_15.geogram',
        'debug_hexmesh_charts_16.geogram',
        'view.lua'
    ]:
        if Path(debug_filename).exists():
            if arguments['keep_debug_files']:
                if not silent_output:
                    print(f'Renaming {debug_filename}...')
                move(debug_filename, output_subfolder / f'rb_generate_quantization.{debug_filename}')
            else:
                if not silent_output:
                    print(f'Removing {debug_filename}...')
                unlink(debug_filename)
