# PHYSIM-DATASET-GENERATOR
This repository implements a software tool for synthesizing images of physically realistic cluttered scenes 
using 3D CAD models as described in our paper:
### A Self-supervised Learning System for Object Detection using Physics Simulation and Multi-view Pose Estimation [pdf](https://arxiv.org/pdf/1703.03347.pdf)
By Chaitanya Mitash, Kostas Bekris, Abdeslam Boularias (Rutgers University).
To appear at the IEEE International Conference on Intelligent Robots and Systems (IROS), Vancouver, Canada, 2017.

#### Citing
To cite the work:

```shell
@article{physim,
  title={A Self-supervised Learning System for Object Detection using Physics Simulation and Multi-view Pose Estimation},
  author={Mitash, Chaitanya and Bekris, Kostas and Boularias, Abdeslam},
  journal={arXiv:1703.03347},
  year={2017}
}
```
### Setup

[1] Download and extract Blender (https://www.blender.org/features/releases/2-78/)
[2] in bashrc add line 'export $BLENDER_PATH=/path-to-blender-folder/blender'
[4] install the 'yaml' package in the python packaged with blender
'''Shell
get the 'get-pip.py' file from the pip documentation(https://pip.pypa.io/en/stable/installing/)
$ /path/to/blender/blender-path/2.xx/python/bin/python3 ~/get-pip.py
$ /blender-path/2.xx/python/bin/python /blender-version/2.xx/python/local/lib/python3.5/dist-packages/pip install yaml
'''

### Demo
[1] 'git clone https://github.com/cmitash/physim-dataset-generator.git'
[2] in bashrc add line 'export PHYSIM_GENDATA=/path-to-repository'
[3] rename 'config.yml.table' or 'config.yml.shelf' to 'config.yml'
[4] run 'python generate_pictures.py'
[5] the generated data can be found in the folder 'rendered_images'.

### Output
[1] images of scenes.
[2] labeled bounding box files for each scene <label, tl_x, tl_y, br_x, br_y>.
[3] debug images indicating the bounding-boxes over the objects.
[4] '.blend' files to debug the simulation parameters.

### Parameters
the example cfg files contain the parameters of simulation.
'''Shell
camera:
  num_poses: <number of views to render from>
  camera_poses: [[pos_x, pos_y, pos_z, quat_w, quat_x, quat_y, quat_z], ...]
  camera_intrinsics: [[f_x, 0.0, c_x],[0.0, f_y, c_y],[0.0, 0.0, 1.0]]

rest_surface:
  type: shelf
  surface_pose: [pos_x, pos_y, pos_z, quat_w, quat_x, quat_y, quat_z]

Models: [model_1, model_2, ...]

params:
  num_images: <number of training images>
  minimum_objects_in_scene: <minimum object per scene>
  maximum_objects_in_scene: <minimum object per scene>
  range_x: [<min_x>, <max_x>]
  range_y: [<min_y>, <max_y>]
  range_z: [<min_z>, <max_z>]
  num_simulation_steps: <number os simulation steps to run>
  light_position_range_x: [<min_x>, <max_x>]
  light_position_range_y: [<min_y>, <max_y>]
  light_position_range_z: [<min_z>, <max_z>]
```
#### Citing
To cite the work:

```shell
@article{physim,
  title={A Self-supervised Learning System for Object Detection using Physics Simulation and Multi-view Pose Estimation},
  author={Mitash, Chaitanya and Bekris, Kostas and Boularias, Abdeslam},
  journal={arXiv:1703.03347},
  year={2017}
}
```
### Setup

[1] Download and extract Blender (https://www.blender.org/features/releases/2-78/)
[2] in bashrc add line 'export $BLENDER_PATH=/path-to-blender-folder/blender'
[4] install the 'yaml' package in the python packaged with blender
'''Shell
get the 'get-pip.py' file from the pip documentation(https://pip.pypa.io/en/stable/installing/)
$ /path/to/blender/blender-path/2.xx/python/bin/python3 ~/get-pip.py
$ /blender-path/2.xx/python/bin/python /blender-version/2.xx/python/local/lib/python3.5/dist-packages/pip install yaml
'''

### Demo
[1] 'git clone https://github.com/cmitash/physim-dataset-generator.git'
[2] in bashrc add line 'export PHYSIM_GENDATA=/path-to-repository'
[3] rename 'config.yml.table' or 'config.yml.shelf' to 'config.yml'
[4] run 'python generate_pictures.py'
[5] the generated data can be found in the folder 'rendered_images'.

### Output
[1] images of scenes.
[2] labeled bounding box files for each scene <label, tl_x, tl_y, br_x, br_y>.
[3] debug images indicating the bounding-boxes over the objects.
[4] '.blend' files to debug the simulation parameters.

### Parameters
the example cfg files contain the parameters of simulation.
'''Shell
camera:
  num_poses: <number of views to render from>
  camera_poses: [[pos_x, pos_y, pos_z, quat_w, quat_x, quat_y, quat_z], ...]
  camera_intrinsics: [[f_x, 0.0, c_x],[0.0, f_y, c_y],[0.0, 0.0, 1.0]]

rest_surface:
  type: shelf
  surface_pose: [pos_x, pos_y, pos_z, quat_w, quat_x, quat_y, quat_z]

Models: [model_1, model_2, ...]

params:
  num_images: <number of training images>
  minimum_objects_in_scene: <minimum object per scene>
  maximum_objects_in_scene: <minimum object per scene>
  range_x: [<min_x>, <max_x>]
  range_y: [<min_y>, <max_y>]
  range_z: [<min_z>, <max_z>]
  num_simulation_steps: <number os simulation steps to run>
  light_position_range_x: [<min_x>, <max_x>]
  light_position_range_y: [<min_y>, <max_y>]
  light_position_range_z: [<min_z>, <max_z>]
```