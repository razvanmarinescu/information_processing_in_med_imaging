import os
import nibabel as nib
import numpy as np
import scipy
from scipy import ndimage

NR_TEMP = 10;
NR_SEG = 15;

DEBUG = 0

long_AD_baseline_filenames = ['AD_' + str(i) + '_baseline.nii' for i in range(NR_SEG)]
long_AD_followup_filenames = ['AD_' + str(i) + '_followup.nii' for i in range(NR_SEG)]
long_CTL_baseline_filenames = ['CTL_' + str(i) + '_baseline.nii' for i in range(NR_SEG)]
long_CTL_followup_filenames = ['CTL_' + str(i) + '_followup.nii' for i in range(NR_SEG)]

baseline_filenames = long_AD_baseline_filenames + long_CTL_baseline_filenames 
followup_filenames = long_AD_followup_filenames + long_CTL_followup_filenames

if DEBUG:
  long_filenames = [long_filenames[0]]
#template_filenames = template_filenames[0]

#aff_reg_filenames = [name.split(".")[0] + "_aff.nii" for name in long_filenames]
#aff_mat_filenames = [name.split(".")[0] + "_aff_matrix.txt" for name in long_filenames]
#nonlin_reg_filenames = [name.split(".")[0] + "_nonlin.nii" for name in long_filenames]
#nonlin_cpp_filenames = [name.split(".")[0] + "_nonlin_cpp.nii" for name in long_filenames]
seg_baseline_filenames = [name.split(".")[0] + "_brain.nii" for name in baseline_filenames]
seg_followup_filenames = [name.split(".")[0] + "_brain.nii" for name in followup_filenames]
dil_seg_baseline_filenames = [name.split(".")[0] + "_brain_dil.nii" for name in baseline_filenames]
dil_seg_followup_filenames = [name.split(".")[0] + "_brain_dil.nii" for name in followup_filenames]

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


def dilate_img(i):
  # baseline image
  seg_img = nib.load(seg_baseline_filenames[i])
  seg_data = np.array(seg_img.get_data())

  dil_data = ndimage.binary_dilation(seg_data, iterations=2).astype(seg_data.dtype)
  nib_dil_image = nib.Nifti1Image(dil_data, np.eye(4))
  nib.save(nib_dil_image, dil_seg_baseline_filenames[i])

  # followup image
  seg_img = nib.load(seg_followup_filenames[i])
  seg_data = np.array(seg_img.get_data())

  dil_data = ndimage.binary_dilation(seg_data, iterations=2).astype(seg_data.dtype)
  nib_dil_image = nib.Nifti1Image(dil_data, np.eye(4))
  nib.save(nib_dil_image, dil_seg_followup_filenames[i])


#os.system("cd longitudinal_images/")
for i in [0]:#range(NR_FILES):
  dilate_img(i)

  reg_cmd = 'reg_aladin -ref %s -flo %s -rmask dil_%s -fmask dil_%d -res %s -aff %s' % (baseline_filenames[i], followup_filenames[i], )


  
 
