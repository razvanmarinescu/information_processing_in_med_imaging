import os
import nibabel as nib
import numpy as np
import scipy
from scipy import ndimage
import pdb
import csv

NR_TEMP = 10;
NR_SEG = 15;

DEBUG = 1

long_AD_baseline_filenames = ['AD_' + str(i) + '_baseline.nii' for i in range(NR_SEG)]
long_AD_followup_filenames = ['AD_' + str(i) + '_followup.nii' for i in range(NR_SEG)]
long_CTL_baseline_filenames = ['CTL_' + str(i) + '_baseline.nii' for i in range(NR_SEG)]
long_CTL_followup_filenames = ['CTL_' + str(i) + '_followup.nii' for i in range(NR_SEG)]

baseline_filenames = long_AD_baseline_filenames + long_CTL_baseline_filenames 
followup_filenames = long_AD_followup_filenames + long_CTL_followup_filenames

mid_baseline_filenames = [name.split(".")[0] + "_midspace.nii" for name in baseline_filenames]
mid_followup_filenames = [name.split(".")[0] + "_midspace.nii" for name in followup_filenames]
seg_mid_baseline_filenames = [name.split(".")[0] + "_midspace_brain.nii" for name in baseline_filenames]
seg_mid_followup_filenames = [name.split(".")[0] + "_midspace_brain.nii" for name in followup_filenames]

seg_AD_boundary_filenames = ['AD_' + str(i) + '_BSIboundary.nii' for i in range(NR_SEG)]
seg_CTL_boundary_filenames = ['AD_' + str(i) + '_BSIboundary.nii' for i in range(NR_SEG)]

seg_boundary_filenames = seg_AD_boundary_filenames + seg_CTL_boundary_filenames

aladin_options = "-speeeeed ";

# max 4 levels, 300 iterations each
f3d_options = "-ln 4 -maxit 200"; # I think 4 lvl x 200 it is ideal
#f3d_options = "-ln 1 -maxit 10"; # I think 4 lvl x 200 it is ideal
# 2 lvl 200 it - 1m26sec
# 3 lvl 300 it - 2m16sec
# 4 lvl 300 it - 2m18sec
# 4 lvl 200 it - 1m30sec

EXEC_CMD = 1;

NR_FILES = len(baseline_filenames)

window = [0.45, 0.65]

bsi = np.zeros(NR_FILES, float)
scaled_bsi = np.zeros(NR_FILES, float)
full_volume_diff = np.zeros(NR_FILES, float)
#os.system("cd longitudinal_images/")


struct1 = ndimage.generate_binary_structure(3, 2)

def clip_matrix(mat, i1, i2):
  assert(i2 < i1)
  i1mat = np.ones(mat.shape, mat.dtype) * i1
  i2mat = np.ones(mat.shape, mat.dtype) * i2
  return np.minimum(np.maximum(mat, i2mat), i1mat)


a = np.array([[1,2],[3,4]])
print clip_matrix(a, 3.33, 1.33)

for i in range(NR_FILES):
  
  print i
  seg_mid_base_img = nib.load(seg_mid_baseline_filenames[i])
  seg_mid_base_data = np.array(seg_mid_base_img.get_data())

  seg_mid_followup_img = nib.load(seg_mid_followup_filenames[i])
  seg_mid_followup_data = np.array(seg_mid_followup_img.get_data())

  seg_union = ((seg_mid_base_data + seg_mid_followup_data) >= 1).astype(np.uint8); 
  seg_intersection = ((seg_mid_base_data + seg_mid_followup_data) == 2).astype(np.uint8); 

  # dilate the union and erode the intersection
  dil_seg_union = ndimage.binary_dilation(seg_union, structure=struct1, iterations=1).astype(seg_union.dtype)
  ero_seg_intersection = ndimage.binary_erosion(seg_intersection, structure=struct1, iterations=1).astype(seg_intersection.dtype)

  # obtain the boundary region by XORing the dilated union and eroded segmentation
  seg_boundary = ((dil_seg_union + ero_seg_intersection ) == 1).astype(np.uint8)

  # load the actual T1 images
  mid_base_img = nib.load(mid_baseline_filenames[i])
  mid_base_data = np.array(mid_base_img.get_data())

  mid_followup_img = nib.load(mid_followup_filenames[i])
  mid_followup_data = np.array(mid_followup_img.get_data())

  # normalise the intensity by the average value in the T1-values at the intersection
  mid_base_int = mid_base_data * seg_intersection
  if np.count_nonzero(mid_base_int) > 0:
    mean_base_int = np.sum(mid_base_int).astype(float)/np.count_nonzero(mid_base_int)
    mid_base_data = mid_base_data.astype(float) / mean_base_int
  else:
    print 'mid_base_int contains only zero elements'


  mid_followup_int = mid_followup_data * seg_intersection
  if np.count_nonzero(mid_base_int) > 0:
    mean_followup_int = np.sum(mid_followup_int).astype(float)/np.count_nonzero(mid_followup_int)
    mid_followup_data = mid_followup_data.astype(float) / mean_followup_int
  else:
    print 'mid_followup_int contains only zero elements'

  # window the data to the 0.45 - 0.65 range
  windowed_base_data = mid_base_data * clip_matrix(mid_base_data, window[1], window[0])
  windowed_followup_data = mid_followup_data * clip_matrix(mid_followup_data, window[1], window[0])
  
  #pdb.set_trace()
  bsi[i] = np.sum((windowed_base_data - windowed_followup_data) * seg_boundary) 
  scaled_bsi[i] = bsi[i] / np.sum(seg_intersection)
  full_volume_diff[i] = np.sum(seg_mid_base_data - seg_mid_followup_data)
  
  diff_image = (mid_base_data - mid_followup_data) * seg_boundary
  print 'diff: %f       bsi %f' % (np.sum(diff_image), bsi[i])
  nib_seg_boundary_image = nib.Nifti1Image(diff_image, seg_mid_base_img.affine)
  nib.save(nib_seg_boundary_image, seg_boundary_filenames[i])

with open("../bsi.csv",'w') as f:
  csvwriter = csv.writer(f, delimiter=',')
  csvwriter.writerow(bsi)
  csvwriter.writerow(full_volume_diff)


