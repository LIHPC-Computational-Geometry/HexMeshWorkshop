#!/usr/bin/env python

# Parse all 'step' data folders inside `input_folder` / 'MAMBO'. For each of them,
# (if not already done) generate a tet-mesh with Gmsh. For each of them,
# (if not already done) generate a labeling with automatic_polycube, and one with evocube. For each of them,
# (if not already done) generate a hex-mesh with polycube_withHexEx. For each of them,
# (if not already done) generate a hex-mesh with global_padding. For each of them,
# (if not already done) generate a hex-mesh with inner_smoothing.

# The final structure is:
# `input_folder`
# └── MAMBO
#     └── <every 'step' data folder>
#         └── Gmsh_0.1
#             ├── graphcut_labeling_1_3_1e-9_0.05         # compactness=1, fidelity=3, sensitivity=1e-9, angle of rotation=0.05
#             ├── automatic_polycube_YYYYMMDD_HHMMSS
#             │   └── polycube_withHexEx_1.3
#             │       └── global_padding
#             │           └── inner_smoothing_50
#             └── evocube_YYYYMMDD_HHMMSS
#                 └── polycube_withHexEx_1.3
#                     └── global_padding
#                         └── inner_smoothing_50

# based on :
# https://github.com/LIHPC-Computational-Geometry/HexMeshWorkshop/blob/ee4f61e239678bf9274cbc22e9d054664f01b1ec/modules/data_folder_types.py#L1318
# https://github.com/LIHPC-Computational-Geometry/HexMeshWorkshop/blob/f082a55515b2570d6a4b19dd4dfdc891641929b1/modules/data_folder_types.py#L1289

# Note: the code rely on hard-coded folder names, like 'polycube_withHexEx_1.3'
# but we should leave the user free to rename all folders,
# use DataFolder.get_subfolders_generated_by() and check parameters value in the info.json

from rich.prompt import Confirm

from dds import *

# Per algo policy when an output is missing
# 'ask', 'run' or 'pass'
GMSH_OUTPUT_MISSING_POLICY               = 'pass'
GRAPHCUT_LABELING_OUTPUT_MISSING_POLICY  = 'pass'
AUTOMATIC_POLYCUBE_OUTPUT_MISSING_POLICY = 'pass'
EVOCUBE_OUTPUT_MISSING_POLICY            = 'pass'
POLYCUBE_WITHHEXEX_OUTPUT_MISSING_POLICY = 'pass'
GLOBAL_PADDING_OUTPUT_MISSING_POLICY     = 'pass'
INNER_SMOOTHING_OUTPUT_MISSING_POLICY    = 'pass'

RUNNING_ALGO_LINE_TEMPLATE            = "Running [green]{algo}[/] on [cyan]{path}[/]"
EXISTING_OUTPUT_LINE_TEMPLATE         = "\[[bright_black]-[/]] [green]{algo}[/] on [cyan]{path}[/]"
NEW_OUTPUT_LINE_TEMPLATE              = "\[[green]✓[/]] [green]{algo}[/] on [cyan]{path}[/]"
MISSING_OUTPUT_LINE_TEMPLATE          = "No [green]{algo}[/] output inside [cyan]{path}[/]. Run {algo}?"
IGNORING_MISSING_OUTPUT_LINE_TEMPLATE = "\[[dark_orange]●[/]] Ignoring missing [green]{algo}[/] output inside [cyan]{path}[/]"

def user_confirmed_or_choose_autorun(policy: str, confirmation_question: str) -> bool:
    if policy == 'run':
        return True
    elif policy == 'pass':
        return False
    elif policy == 'ask':
        return Confirm.ask(confirmation_question)
    else:
        raise RuntimeError(f"in user_confirmed_or_choose_autorun(), '{policy}' is not a valid policy")

def main(input_folder: Path, arguments: list):
    # check `arguments`
    if len(arguments) != 0:
        logging.fatal(f'batch_processing does not need other arguments than the input folder, but {arguments} were provided')
        exit(1)
    console = Console(theme=Theme(inherit=False)) # better to create a global variable in dds.py ??
    assert((input_folder / 'MAMBO').exists())
    for step_subfolder in sorted(get_subfolders_of_type(input_folder / 'MAMBO','step')):
        step_object: DataFolder = DataFolder(step_subfolder)
        # tetrahedrization if not already done
        if not (step_subfolder / 'Gmsh_0.1').exists():
            if user_confirmed_or_choose_autorun(GMSH_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='Gmsh', path=collapseuser(step_subfolder))):
                step_object.run('Gmsh', {'characteristic_length_factor': 0.1}, silent_output=True)
                # here we assume Gmsh succeeded
            else:
                console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='Gmsh', path=collapseuser(step_subfolder)))
                continue # ignore this 'step_subfolder'
        else:
            # Gmsh was already executed
            console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='Gmsh', path=collapseuser(step_subfolder)))
        # instantiate the tet mesh folder
        tet_mesh_object: DataFolder = DataFolder(step_subfolder / 'Gmsh_0.1')
        assert(tet_mesh_object.type == 'tet-mesh')
        # generate a labeling with graphcut_labeling if not already done
        if not (tet_mesh_object.path / 'graphcut_labeling_1_3_1e-09_0.05').exists():
            if user_confirmed_or_choose_autorun(GRAPHCUT_LABELING_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='graphcut_labeling', path=collapseuser(tet_mesh_object.path))):
                with console.status(RUNNING_ALGO_LINE_TEMPLATE.format(algo='graphcut_labeling', path=collapseuser(tet_mesh_object.path))) as status:
                    tet_mesh_object.run('graphcut_labeling', {'compactness': 1, 'fidelity': 3, 'sensitivity': 1e-9, 'angle_of_rotation': 0.05}, silent_output=True)
                # here we assume graphcut_labeling succeeded
                console.print(NEW_OUTPUT_LINE_TEMPLATE.format(algo='graphcut_labeling', path=collapseuser(tet_mesh_object.path)))
            else:
                console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='graphcut_labeling', path=collapseuser(tet_mesh_object.path)))
                pass # go to the automatic_polycube & evocube section
        else:
            # graphcut_labeling was already executed
            console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='graphcut_labeling', path=collapseuser(tet_mesh_object.path)))
        # get all labeling generated by 'automatic_polycube'
        labeling_subfolders_generated_by_automatic_polycube: list[Path] = tet_mesh_object.get_subfolders_generated_by('automatic_polycube')
        assert(len(labeling_subfolders_generated_by_automatic_polycube) <= 1) # expecting 0 or 1 labeling generated by this algo, not more
        labeling_subfolders_to_look_into: list[Path] = list()
        if len(labeling_subfolders_generated_by_automatic_polycube)==0:
            if user_confirmed_or_choose_autorun(AUTOMATIC_POLYCUBE_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='automatic_polycube', path=collapseuser(tet_mesh_object.path))):
                tet_mesh_object.run('automatic_polycube', silent_output=True)
                # here we assume automatic_polycube succeeded
                # TODO retrieve the path to the created folder, and append it to labeling_subfolders_to_look_into
            else:
                console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='automatic_polycube', path=collapseuser(tet_mesh_object.path)))
                # don't append anything to labeling_subfolders_to_look_into
        else:
            # automatic_polycube was already executed
            console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='automatic_polycube', path=collapseuser(tet_mesh_object.path)))
            labeling_subfolders_to_look_into.append(labeling_subfolders_generated_by_automatic_polycube[0])
        # get all labeling generated by 'evocube'
        labeling_subfolders_generated_by_evocube: list[Path] = tet_mesh_object.get_subfolders_generated_by('evocube')
        assert(len(labeling_subfolders_generated_by_evocube) <= 1) # expecting 0 or 1 labeling generated by this algo, not more
        if len(labeling_subfolders_generated_by_evocube)==0:
            if user_confirmed_or_choose_autorun(EVOCUBE_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='evocube', path=collapseuser(tet_mesh_object.path))):
                tet_mesh_object.run('evocube', silent_output=True)
                # here we assume evocube succeeded
                # TODO retrieve the path to the created folder, and append it to labeling_subfolders_to_look_into
            else:
                console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='evocube', path=collapseuser(tet_mesh_object.path)))
                # don't append anything to labeling_subfolders_to_look_into
        else:
            # evocube was already executed
            console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='evocube', path=collapseuser(tet_mesh_object.path)))
            labeling_subfolders_to_look_into.append(labeling_subfolders_generated_by_evocube[0])
        # loop with 2 iterations: 1 for the automatic_polycube labeling, 1 for the evocube labeling
        for labeling_subfolder in labeling_subfolders_to_look_into:
            # instantiate the labeling data folder
            labeling_object: DataFolder = DataFolder(labeling_subfolder)
            assert(labeling_object.type == 'labeling')
            # hex-mesh extraction if not already done
            if not (labeling_subfolder / 'polycube_withHexEx_1.3').exists():
                if user_confirmed_or_choose_autorun(POLYCUBE_WITHHEXEX_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='polycube_withHexEx', path=collapseuser(labeling_object.path))):
                    labeling_object.run('polycube_withHexEx', {'scale': 1.3}, silent_output=True)
                    # here we assume polycube_withHexEx succeeded
                else:
                    console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='polycube_withHexEx', path=collapseuser(labeling_object.path)))
                    continue
            else:
                # polycube_withHexEx was already executed
                console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='polycube_withHexEx', path=collapseuser(labeling_object.path)))
            # instantiate the hex-mesh folder
            init_hex_mesh_object: DataFolder = DataFolder(labeling_subfolder / 'polycube_withHexEx_1.3')
            assert(init_hex_mesh_object.type == 'hex-mesh')
            if(init_hex_mesh_object.get_mesh_stats_dict()['cells']['nb'] == 0):
                continue # polycube_withHexEx created an empty hex-mesh, skip post-processing
            if not (init_hex_mesh_object.path / 'global_padding').exists():
                if user_confirmed_or_choose_autorun(GLOBAL_PADDING_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='global_padding', path=collapseuser(init_hex_mesh_object.path))):
                    with console.status(RUNNING_ALGO_LINE_TEMPLATE.format(algo='global_padding', path=collapseuser(init_hex_mesh_object.path))) as status:
                        init_hex_mesh_object.run('global_padding', silent_output=True)
                    # here we assume global_padding succeeded
                    console.print(NEW_OUTPUT_LINE_TEMPLATE.format(algo='global_padding', path=collapseuser(init_hex_mesh_object.path)))
                else:
                    console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='global_padding', path=collapseuser(init_hex_mesh_object.path)))
                    continue
            else:
                # global_padding was already executed
                console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='global_padding', path=collapseuser(init_hex_mesh_object.path)))
            # instantiate the hex-mesh post-processed with global padding
            global_padded_hex_mesh_object = DataFolder(init_hex_mesh_object.path / 'global_padding')
            assert(global_padded_hex_mesh_object.type == 'hex-mesh')
            if not (global_padded_hex_mesh_object.path / 'inner_smoothing_50').exists():
                if user_confirmed_or_choose_autorun(INNER_SMOOTHING_OUTPUT_MISSING_POLICY,MISSING_OUTPUT_LINE_TEMPLATE.format(algo='inner_smoothing', path=collapseuser(global_padded_hex_mesh_object.path))):
                    with console.status(RUNNING_ALGO_LINE_TEMPLATE.format(algo='inner_smoothing', path=collapseuser(global_padded_hex_mesh_object.path))) as status:
                        global_padded_hex_mesh_object.run('inner_smoothing', silent_output=True) # default nb step is 50
                    # here we assume inner_smoothing succeeded
                    console.print(NEW_OUTPUT_LINE_TEMPLATE.format(algo='inner_smoothing', path=collapseuser(global_padded_hex_mesh_object.path)))
                else:
                    console.print(IGNORING_MISSING_OUTPUT_LINE_TEMPLATE.format(algo='inner_smoothing', path=collapseuser(global_padded_hex_mesh_object.path)))
                    continue
            else:
                # inner smoothing was already executed
                console.print(EXISTING_OUTPUT_LINE_TEMPLATE.format(algo='inner_smoothing', path=collapseuser(global_padded_hex_mesh_object.path)))
            # instantiate the hex-mesh post-processed with smoothing
            smoothed_hex_mesh_object = DataFolder(global_padded_hex_mesh_object.path / 'inner_smoothing_50')
            assert(smoothed_hex_mesh_object.type == 'hex-mesh')
