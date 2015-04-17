import os
import nibabel as nib
import numpy as np
import scipy
from scipy import ndimage
import sys

NR_TEMP = 10;
NR_BEG = int(sys.argv[1]);
NR_SEG = int(sys.argv[2]);

DEBUG = 1

long_AD_baseline_filenames = ['AD_' + str(i) + '_baseline.nii' for i in range(NR_BEG,NR_SEG)]
long_AD_followup_filenames = ['AD_' + str(i) + '_followup.nii' for i in range(NR_BEG, NR_SEG)]
long_CTL_baseline_filenames = ['CTL_' + str(i) + '_baseline.nii' for i in range(NR_BEG, NR_SEG)]
long_CTL_followup_filenames = ['CTL_' + str(i) + '_followup.nii' for i in range(NR_BEG, NR_SEG)]

baseline_filenames = long_AD_baseline_filenames + long_CTL_baseline_filenames 
followup_filenames = long_AD_followup_filenames + long_CTL_followup_filenames

aff_reg_AD_filenames = ['AD_' + str(i) + '_aff.nii' for i in range(NR_BEG, NR_SEG)]
aff_reg_CTL_filenames = ['CTL_' + str(i) + '_aff.nii' for i in range(NR_BEG, NR_SEG)]
aff_mat_AD_filenames = ['AD_' + str(i) + '_aff_mat.txt' for i in range(NR_BEG, NR_SEG)]
aff_mat_CTL_filenames = ['CTL_' + str(i) + '_aff_mat.txt' for i in range(NR_BEG, NR_SEG)]

aff_reg_filenames = aff_reg_AD_filenames + aff_reg_CTL_filenames
aff_mat_filenames = aff_mat_AD_filenames + aff_mat_CTL_filenames
aff_halfAF_mat_filenames = [f.split(".")[0] + '_halfAF.txt' for f in aff_mat_filenames]
aff_halfFA_mat_filenames = [f.split(".")[0] + '_halfFA.txt' for f in aff_mat_filenames]

seg_baseline_filenames = [name.split(".")[0] + "_brain.nii" for name in baseline_filenames]
seg_followup_filenames = [name.split(".")[0] + "_brain.nii" for name in followup_filenames]
dil_seg_baseline_filenames = [name.split(".")[0] + "_brain_dil.nii" for name in baseline_filenames]
dil_seg_followup_filenames = [name.split(".")[0] + "_brain_dil.nii" for name in followup_filenames]

mid_baseline_filenames = [name.split(".")[0] + "_midspace.nii" for name in baseline_filenames]
mid_followup_filenames = [name.split(".")[0] + "_midspace.nii" for name in followup_filenames]
seg_mid_baseline_filenames = [name.split(".")[0] + "_midspace_brain.nii" for name in baseline_filenames]
seg_mid_followup_filenames = [name.split(".")[0] + "_midspace_brain.nii" for name in followup_filenames]

aladin_options = "-speeeeed ";

EXEC_CMD = 1;

NR_FILES = len(baseline_filenames)


def dilate_img(i):
  # baseline image
  seg_img = nib.load(seg_baseline_filenames[i])
  seg_data = np.array(seg_img.get_data())

  dil_data = ndimage.binary_dilation(seg_data, iterations=2).astype(seg_data.dtype)
  nib_dil_image = nib.Nifti1Image(dil_data, seg_img.affine)
  nib.save(nib_dil_image, dil_seg_baseline_filenames[i])

  # followup image
  seg_img = nib.load(seg_followup_filenames[i])
  seg_data = np.array(seg_img.get_data())

  dil_data = ndimage.binary_dilation(seg_data, iterations=2).astype(seg_data.dtype)
  nib_dil_image = nib.Nifti1Image(dil_data, seg_img.affine)
  nib.save(nib_dil_image, dil_seg_followup_filenames[i])


#os.system("cd longitudinal_images/")
for i in range(NR_FILES):
  dilate_img(i)

  reg_cmd = 'reg_aladin -ref %s -flo %s -rmask %s -fmask %s -res %s -aff %s' % (baseline_filenames[i], followup_filenames[i], dil_seg_baseline_filenames[i], dil_seg_followup_filenames[i],aff_reg_filenames[i], aff_mat_filenames[i])

  if DEBUG:
    print reg_cmd
  if EXEC_CMD:
    os.system(reg_cmd)

  reg_trans_cmd1 = 'reg_transform -half %s %s' % (aff_mat_filenames[i], aff_halfAF_mat_filenames[i])
  reg_trans_cmd2 = 'reg_transform -invAff %s %s' % (aff_halfAF_mat_filenames[i], aff_halfFA_mat_filenames[i])
 
  if DEBUG:
    print reg_trans_cmd1
    print reg_trans_cmd2
  if EXEC_CMD:
    os.system(reg_trans_cmd1)
    os.system(reg_trans_cmd2)

  resample_img_cmd1 = 'reg_resample -ref %s -flo %s -trans %s -res %s' % (baseline_filenames[i], baseline_filenames[i], aff_halfFA_mat_filenames[i], mid_baseline_filenames[i])
  resample_img_cmd2 = 'reg_resample -ref %s -flo %s -trans %s -res %s' % (baseline_filenames[i], followup_filenames[i], aff_halfAF_mat_filenames[i], mid_followup_filenames[i])

  if DEBUG:
    print resample_img_cmd1
    print resample_img_cmd2
  if EXEC_CMD:
    os.system(resample_img_cmd1)
    os.system(resample_img_cmd2)

  resample_seg_cmd1 = 'reg_resample -ref %s -flo %s -trans %s -res %s -inter 0' % (baseline_filenames[i], seg_baseline_filenames[i], aff_halfFA_mat_filenames[i], seg_mid_baseline_filenames[i])
  resample_seg_cmd2 = 'reg_resample -ref %s -flo %s -trans %s -res %s -inter 0' % (baseline_filenames[i], seg_followup_filenames[i], aff_halfAF_mat_filenames[i], seg_mid_followup_filenames[i])

  if DEBUG:
    print resample_seg_cmd1
    print resample_seg_cmd2
  if EXEC_CMD:
    os.system(resample_seg_cmd1)
    os.system(resample_seg_cmd2)


