<div align="center">
  <h1><code>dds-hexmeshing</code></h1><br/>
  <p>Semantic data folders (<i>dds, Dossiers de Données Sémantiques</i>)<br/>for hexahedral mesh generation</p><br/>
  <a href="https://github.com/LIHPC-Computational-Geometry/dds-hexmeshing/blob/main/CHANGELOG.md">🔄 Changelog</a> • <a href="https://github.com/LIHPC-Computational-Geometry/dds-hexmeshing/wiki/dds%E2%80%90hexmeshing">📖 Documentation</a><br/>
  <a href="https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d"><img src="https://badgen.net/badge/Maintenance%20Level/Abandoned?color=fe7d37" alt="Maintenance Level: Abandoned"></a>
</div>

Instead of having:
- a local data folder in each code repo (and a total mess inside each of them),
- to remember the command line interface of each executable (please, don't learn them by heart),
- to include other algorithms in your repo to compare them (adding dependencies and slipping towards enormous repos),

this project make it possible to keep each algorithm small and independent, and offering to the user an object-oriented API on data folders like, for a polycube-based hexahedral mesh generation:

<!-- import_MAMBO -->

<details>
<summary>
    Auto-download the <a href="https://gitlab.com/franck.ledoux/mambo">MAMBO</a> dataset:<br/>
    &emsp;<code>./dds.py run import_MAMBO ~/data</code>
</summary>

```diff
  📂~/data
+   📁B0
+   📁B1
+   ...
+   📁S45
```

</details>

<!-- Gmsh -->

<details>
<summary>
    Tetrahedrization of M7 with <a href="http://gmsh.info/">Gmsh</a>:<br/>
    &emsp;<code>./dds.py run Gmsh ~/data/M7 characteristic_length_factor=0.2</code>
</summary>

<table>
<tr><td>

```diff
  📂~/data
    📂M7
+     📂Gmsh_0.2
+       📄tet.mesh
+       📄surface.obj
```

</td><td><img src="img/Gmsh_coarse.png" style="height: 20em" alt="coarse mesh of the M7 model"/></td></tr>
</table>

</details>

<!-- Gmsh, finer mesh -->

<details>
<summary>
    Hmm, I need a finer mesh...</a><br/>
    &emsp;<code>./dds.py run Gmsh ~/data/M7 characteristic_length_factor=0.05</code>
</summary>

<table>
<tr><td>

```diff
  📂~/data
    📂M7
      📁Gmsh_0.2
+     📂Gmsh_0.05
+       📄tet.mesh
+       📄surface.obj
```

</td><td><img src="img/Gmsh_fine.png" style="height: 20em" alt="fine mesh of the M7 model"/></td></tr>
</table>

</details>

<!-- naive_labeling -->

<details> 
<summary>
    Alright. I wonder what the naive labeling looks like.</a><br/>
    &emsp;<code>./dds.py run naive_labeling ~/data/M7/Gmsh_0.05</code>
</summary>

<table>
<tr><td>

```diff
  📂~/data
    📂M7
      📁Gmsh_0.2
      📂Gmsh_0.05
+       📂naive_labeling
+         📄surface_labeling.txt
        📄tet.mesh
        📄surface.obj
```

</td><td><img src="img/naive_labeling.png" style="height: 20em" alt="naive labeling computed on the tetrahedral mesh"/></td></tr>
</table>

</details>

<!-- labeling_painter -->

<details> 
<summary>
    Okay, it's not valid. Let me tweak the labeling by hand.</a><br/>
    &emsp;<em>Sure:</em> <code>./dds.py run labeling_painter ~/data/M7/Gmsh_0.05</code>
</summary>

<table>
<tr><td>

```diff
  📂~/data
    📂M7
      📁Gmsh_0.2
      📂Gmsh_0.05
        📁naive_labeling
+       📂labeling_painter
+         📄surface_labeling.txt
        📄tet.mesh
        📄surface.obj
```

</td><td><img src="img/labeling_painter.png" style="height: 20em" alt="a labeling obtained with labeling_painter"/></td></tr>
</table>

</details>

</details>

<!-- polycube_withHexEx -->

<details> 
<summary>
    Ho-ho! Can you extract a hex-mesh with <a href="https://www.graphics.rwth-aachen.de/software/libHexEx/">libHexEx</a>?<br/>
    &emsp;<em>Indeed I can:</em> <code>./dds.py run polycube_withHexEx ~/data/M7/Gmsh_0.05/labeling_painter</code>
</summary>

<table>
<tr><td>

```diff
  📂~/data
    📂M7
      📁Gmsh_0.2
      📂Gmsh_0.05
        📁naive_labeling
        📂labeling_painter
+         📂polycube_withHexEx_1.0
+           📄hex.mesh
          📄surface_labeling.txt
        📄tet.mesh
        📄surface.obj
```

</td><td><img src="img/polycube_withHexEx.png" style="height: 20em" alt="hexmesh obtained with polycube_withHexEx"/></td></tr>
</table>

</details>

<!-- global_padding -->

<details> 
<summary>
    Fantastic!! Can you also apply a global padding? 🥺<br/>
    &emsp;<em>You know I'm just a Python script, right?</em><br/>
    &emsp;<code>./dds.py run global_padding ~/data/M7/Gmsh_0.05/labeling_painter/polycube_withHexEx_1.0</code>
</summary>

<table>
<tr><td>

```diff
  📂~/data
    📂M7
      📁Gmsh_0.2
      📂Gmsh_0.05
        📁naive_labeling
        📂labeling_painter
          📂polycube_withHexEx_1.0
+           📂global_padding
+             📄hex.mesh
            📄hex.mesh
          📄surface_labeling.txt
        📄tet.mesh
        📄surface.obj
```

</td><td><img src="img/global_padding.png" style="height: 20em" alt="hexmesh post-processed with a global padding"/></td></tr>
</table>

</details><br/>

File format conversions required by some algorithms are automatic.

Overview of the data subfolder types (boxes) and the wrapped algorithms (arrows):

```mermaid
graph LR
    step(step)
    stl(stl)
    tet-mesh(tet-mesh)
    labeling(labeling)
    hex-mesh(hex-mesh)
    step -- Gmsh --> tet-mesh
    tet-mesh -- naive_labeling --> labeling
    tet-mesh -- labeling_painter --> labeling
    tet-mesh -- graphcut_labeling --> labeling
    tet-mesh -- evocube --> labeling
    tet-mesh -- automatic_polycube --> labeling
    tet-mesh -- HexBox --> hex-mesh
    tet-mesh -- AlgoHex --> hex-mesh
    tet-mesh -- marchinghex --> hex-mesh
    labeling -- polycube_withHexEx --> hex-mesh
    labeling -- robustPolycube --> hex-mesh
    hex-mesh -- global_padding --> hex-mesh
    hex-mesh -- inner_smoothing --> hex-mesh
    stl -- MG-Tetra --> tet-mesh
```

Repository structure:
- [`definitions/paths.yml`](definitions/paths.yml): links to external binaries
- [`definitions/data_folder_types/*`](definitions/data_folder_types/): definition of the types that data folders can have (`tet-mesh`, `labeling`, etc)
- [`definitions/algorithms/*`](definitions/algorithms/): definition of the runnable algorithms, wrapping binaries & creating/updating data folders
- [`dds.py`](dds.py): command-line arguments interpreter, definitions parser & action execution
- [`img`](img/): images displayed in the README
