"""
@file generate_pictures.py
@copyright Software License Agreement (BSD License).
Copyright (c) 2017, Rutgers the State University of New Jersey, New Brunswick.
All Rights Reserved. For a full description see the file named LICENSE.
Authors: Chaitanya Mitash, Kostas Bekris, Abdeslam Boularias.
"""

import os, sys, shutil
import os.path as osp
import time, random
from datetime import datetime

from ConfigParser import ConfigParser
import Label

random.seed(datetime.now())

if os.environ.get('BLENDER_PATH') == None:
    print("Please set BLENDER_PATH in bashrc!")
    sys.exit()

g_blender_executable_path = os.environ['BLENDER_PATH']

g_blank_blend_file_path = 'blank.blend'

# call blender to render images
blank_file = osp.join(g_blank_blend_file_path)
render_code = osp.join('simulate_and_render.py')

syn_images_folder = 'rendered_images'
if os.path.exists(syn_images_folder):
    shutil.rmtree(syn_images_folder)
os.mkdir(syn_images_folder)
os.mkdir(syn_images_folder + "/debug")

start = time.time()
try:
    render_cmd = '%s %s -b --python %s' % \
    (g_blender_executable_path, blank_file, render_code)

    os.system(render_cmd)
except:
    print('render failed. render_cmd: %s' % (render_cmd))

cfg = ConfigParser("config.yml", "camera_info.yml")

num_of_images = cfg.getNumTrainingImages()
pLabel = Label.Label()

frame_number = cfg.getNumSimulationSteps() - 1
if cfg.getLabelType() == 'pixel':
	pLabel.get_segmentation_labels(syn_images_folder, num_of_images, frame_number)
else:
	pLabel.draw_bboxes(syn_images_folder, num_of_images, frame_number)

end = time.time()
print ("%d images generated in %f seconds!" % (num_of_images, end - start))
