import os,sys
import numpy as np


def organize_result(inpath='./rendered_images/',outpath='./rendered_images_org/'):
  if os.path.exists(inpath):
    print('inpath is none!')
  
  folders=os.listdir(inpath)
  print('# folders: ',len(folders))
  src=['rgb/*', 'labels/edge_img.png', 'labels/seg_img.png', 'depth/*']
  dst=['rgb/','edge_labels/','seg_labels/','depth/']
  for item in dst:
    # if os.path.exists(outpath+item):
    os.makedirs(outpath+item)
  cnt=0
  for folder in folders:
    if 'image' not in folder:
      continue
    for i in range(len(src)):
      if 'depth' in src[i]:
        command='cp '+inpath+folder+'/'+src[i]+' '+outpath+dst[i]+ '%06d' % cnt +'.exr'
      else:
        command='cp '+inpath+folder+'/'+src[i]+' '+outpath+dst[i]+ '%06d' % cnt +'.png'
      print(command)
      res=os.system(command)
      if (res!=0) :
        print('error:\n',command)
        exit(1)
    cnt+=1

def renameDepth(inpath='./rendered_images2/depth/'):
  files = os.listdir(inpath)
  
  for file in files:
    if 'png' in file:
      name = os.path.splitext(file)[0]
      cmd = 'mv '+inpath+file+' '+inpath+name+'.exr'
      print(cmd)
      os.system(cmd)



if __name__=='__main__':
  organize_result()
  # renameDepth()