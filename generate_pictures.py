import os
import cv2
import cv
import numpy as np
import os.path as osp
import sys
from PIL import Image, ImageDraw
import sys
import argparse
import os, tempfile, glob, shutil
import random
import shutil
import time
from datetime import datetime

random.seed(datetime.now())

object_file_dict = {'crayola_24_ct':1, 'expo_dry_erase_board_eraser':2, 'folgers_classic_roast_coffee':3,
                    'scotch_duct_tape':4, 'dasani_water_bottle':5, 'jane_eyre_dvd':6,
                    'up_glucose_bottle':7, 'laugh_out_loud_joke_book':8, 'soft_white_lightbulb':9,
                    'kleenex_tissue_box':10, 'ticonderoga_12_pencils':11, 'dove_beauty_bar':12,
                    'dr_browns_bottle_brush':13, 'elmers_washable_no_run_school_glue':14, 'rawlings_baseball':15}

def draw_bboxes(syn_images_folder, num_of_images):
    end = len(glob.glob1("rendered_images", "image_*.png"))
    for i in range(end - num_of_images, end):
        # Read an image
        img_filepath = osp.join(syn_images_folder, 'image_%05d.png' % i)
        print (img_filepath)
        im = Image.open(img_filepath)
        draw = ImageDraw.Draw(im)

        # Open a bounding box file, read all entry and sort in x-direction distance
        bbox_filepath = osp.join(syn_images_folder, 'raw_bbox_%05d.txt' % i)
        bbox_list = []
        with open(bbox_filepath, "r") as file:
            lines = file.readlines()
            for line in lines:
                name, x, y, width, height, postr = line.split(',')
                bbox_list.append([name, float(x), float(y), float(width), float(height), float(postr[:-1])])
                x = float(x)
                y = float(y)
                width = float(width)
                height = float(height)
                draw.rectangle([(x, y), (x + width, y + height)])
                draw.text((x, y), name)
        file.close()
        bbox_list.sort(key=lambda obj: obj[5])

        #Find occlusions and fix bounding boxes
        covered_area = np.zeros((im.size[1],im.size[0],1), np.uint8)
        after_occlusion_boxes = osp.join(syn_images_folder, 'bbox_%05d.txt' % i)
        after_occlusion_file = open(after_occlusion_boxes,'a')

        for k in range(len(bbox_list)-1,-1,-1):
            mask_image = np.zeros((im.size[1],im.size[0],1), np.uint8)
            mask_image[bbox_list[k][2]:bbox_list[k][2]+bbox_list[k][4], bbox_list[k][1]:bbox_list[k][1]+bbox_list[k][3]] = 1
            
            visible_area = cv2.bitwise_and(mask_image, cv2.bitwise_not(covered_area))
            covered_area = cv2.bitwise_or(covered_area, mask_image)
            
            contours, hierarchy = cv2.findContours(visible_area, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            maxcontourarea = 0
            for c in range(0,len(contours)):
                if (cv2.contourArea(contours[c]) > maxcontourarea):
                    maxcontourarea = cv2.contourArea(contours[c])
                    x1,y1,w1,h1 = cv2.boundingRect(contours[c])

            if maxcontourarea > 50:
                after_occlusion_file.write("%s, %i, %i, %i, %i\n" % (object_file_dict[bbox_list[k][0]], int(x1), int(y1), int(x1)+int(w1), int(y1)+int(h1)))
                draw.rectangle([(x1, y1), (x1 + w1, y1 + h1)], outline=(255,0,0,255))
        after_occlusion_file.close()

        # save debug image showing bounding box correction
        del draw
        new_img_filepath = osp.join(syn_images_folder, 'dbg_img_%05d.png' % i)
        im.save(new_img_filepath)


if os.environ.get('BLENDER_PATH') == None:
    print("Please set BLENDER_PATH in bashrc!")
    sys.exit()

g_blender_executable_path = os.environ['BLENDER_PATH']

g_blank_blend_file_path = 'blank.blend'

# call blender to render images
blank_file = osp.join(g_blank_blend_file_path)
render_code = osp.join('simulate_and_render.py')
temp_dirname = tempfile.mkdtemp()

syn_images_folder = 'rendered_images'
if not os.path.exists(syn_images_folder):
    os.mkdir(syn_images_folder)

num_of_images = 15000
start = time.time()

try:
    render_cmd = '%s %s -b --python %s -- %d %s %s' % \
    (g_blender_executable_path, blank_file, render_code, num_of_images, 'shelf', temp_dirname)

    os.system(render_cmd)
except:
    print('render failed. render_cmd: %s' % (render_cmd))

# draw bbox on image
draw_bboxes(syn_images_folder, num_of_images)

end = time.time()
print ("%d images generated in %f seconds!" % (num_of_images, end - start))
