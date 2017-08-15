import cv2
from PIL import Image, ImageDraw
import os.path as osp
import numpy as np

class Label:
    def draw_bboxes(self, syn_images_folder, num_of_images):
        for i in range(0, num_of_images):
            img_filepath = osp.join(syn_images_folder, 'image_%05d.png' % i)
            im = Image.open(img_filepath)
            draw = ImageDraw.Draw(im)

            # Open a bounding box file, read all entry and sort in x-direction distance
            bbox_filepath = osp.join(syn_images_folder, 'debug/raw_bbox_%05d.txt' % i)
            bbox_list = []
            with open(bbox_filepath, "r") as file:
                lines = file.readlines()
                for line in lines:
                    classid, x, y, width, height, postr = line.split(',')
                    bbox_list.append([int(classid), float(x), float(y), float(width), float(height), float(postr[:-1])])
                    x = float(x)
                    y = float(y)
                    width = float(width)
                    height = float(height)
                    draw.rectangle([(x, y), (x + width, y + height)])
            file.close()
            bbox_list.sort(key=lambda obj: obj[5])

            #Find occlusions and fix bounding boxes
            covered_area = np.zeros((im.size[1],im.size[0],1), np.uint8)
            after_occlusion_boxes = osp.join(syn_images_folder, 'bbox_%05d.txt' % i)
            after_occlusion_file = open(after_occlusion_boxes,'a')

            for k in range(len(bbox_list)-1,-1,-1):
                mask_image = np.zeros((im.size[1],im.size[0],1), np.uint8)
                mask_image[int(bbox_list[k][2]):int(bbox_list[k][2]+bbox_list[k][4]), int(bbox_list[k][1]):int(bbox_list[k][1]+bbox_list[k][3])] = 1
                
                visible_area = cv2.bitwise_and(mask_image, cv2.bitwise_not(covered_area))
                covered_area = cv2.bitwise_or(covered_area, mask_image)
                
                contours, hierarchy = cv2.findContours(visible_area, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                maxcontourarea = 0
                for c in range(0,len(contours)):
                    if (cv2.contourArea(contours[c]) > maxcontourarea):
                        maxcontourarea = cv2.contourArea(contours[c])
                        x1,y1,w1,h1 = cv2.boundingRect(contours[c])

                if maxcontourarea > 50:
                    after_occlusion_file.write("%i, %i, %i, %i, %i\n" % (int(bbox_list[k][0] + 1), int(x1), int(y1), int(x1)+int(w1), int(y1)+int(h1)))
                    draw.rectangle([(x1, y1), (x1 + w1, y1 + h1)], outline=(255,0,0,255))
            after_occlusion_file.close()

            # save debug image showing bounding box correction
            del draw
            new_img_filepath = osp.join(syn_images_folder, 'debug/dbg_img_%05d.png' % i)
            im.save(new_img_filepath)