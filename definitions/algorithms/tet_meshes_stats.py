#!/usr/bin/env python

# parse `input_folder` / 'MAMBO' / <'step' data folders> / 'Gmsh_0.1' or 'Gmsh_0.15'
# as well as `input_folder` / 'OctreeMeshing' / 'cad' / <'tet-mesh' data folders>
# and print min & max number of tetrahedra

from dds import *

GMSH_OUPUT_FOLDER_NAME = 'Gmsh_0.15' # 'Gmsh_0.1' or 'Gmsh_0.15'

def main(input_folder: Path, arguments: list):

    # check `arguments`
    if len(arguments) != 0:
        logging.fatal(f'tet_meshes_stats does not need other arguments than the input folder, but {arguments} were provided')
        exit(1)

    console = Console(theme=Theme(inherit=False))

    console.print(f"Parsing [cyan]{collapseuser(input_folder)}/MAMBO/<'step' data folders>/{GMSH_OUPUT_FOLDER_NAME}[/]")
    console.print(f"and [cyan]{collapseuser(input_folder)}/OctreeMeshing/cad/<'tet-mesh' data folders>[/]")
    console.rule(characters='·')

    min_nb_tetrahedra: Optional[int] = None
    min_nb_tetrahedra_location = Path()
    max_nb_tetrahedra: Optional[int] = None
    max_nb_tetrahedra_location = Path()

    for tet_mesh_path in [(x / GMSH_OUPUT_FOLDER_NAME) for x in get_subfolders_of_type(input_folder / 'MAMBO', 'step') if (x / GMSH_OUPUT_FOLDER_NAME).exists()] \
    + get_subfolders_of_type(input_folder / 'OctreeMeshing' / 'cad', 'tet-mesh'):

        tet_folder: DataFolder = DataFolder(tet_mesh_path)
        assert(tet_folder.type == 'tet-mesh')
        nb_tetrahedra = tet_folder.get_tet_mesh_stats_dict()['cells']['nb'] # type: ignore | see ../data_folder_types/tet-mesh.accessors.py

        if nb_tetrahedra >= 300000:
            console.print(f'[cyan]{collapseuser(tet_folder.path)}[/] has 300k or more tetrahedra ({nb_tetrahedra})')

        if min_nb_tetrahedra is None or nb_tetrahedra < min_nb_tetrahedra:
            min_nb_tetrahedra = nb_tetrahedra
            min_nb_tetrahedra_location = tet_folder.path

        if max_nb_tetrahedra is None or nb_tetrahedra > max_nb_tetrahedra:
            max_nb_tetrahedra = nb_tetrahedra
            max_nb_tetrahedra_location = tet_folder.path

    console.rule(characters='·')
    console.print(f'min = [green]{min_nb_tetrahedra}[/] tetrahedra at [cyan]{collapseuser(min_nb_tetrahedra_location)}[/]')
    console.print(f'max = [green]{max_nb_tetrahedra}[/] tetrahedra at [cyan]{collapseuser(max_nb_tetrahedra_location)}[/]')