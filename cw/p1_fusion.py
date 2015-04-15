import os
import nibabel as nib
import numpy as np

NR_TEMP = 10;
NR_SEG = 5;

DEBUG = 0

template_filenames_stubs = ['../template_database/template_' + str(i) for i in range(NR_TEMP)]
long_AD_baseline_filenames = ['AD_' + str(i) + '_baseline.nii' for i in range(10,10+NR_SEG)]
long_AD_followup_filenames = ['AD_' + str(i) + '_followup.nii' for i in range(10,10+NR_SEG)]
long_CTL_baseline_filenames = ['CTL_' + str(i) + '_baseline.nii' for i in range(10,10+NR_SEG)]
long_CTL_followup_filenames = ['CTL_' + str(i) + '_followup.nii' for i in range(10,10+NR_SEG)]

template_filenames = [x + ".nii" for x in template_filenames_stubs]
long_filenames = long_AD_baseline_filenames + long_AD_followup_filenames + long_CTL_baseline_filenames + long_CTL_followup_filenames

if DEBUG:
  long_filenames = [long_filenames[0]]
#template_filenames = template_filenames[0]

aff_reg_filenames = [name.split(".")[0] + "_aff.nii" for name in long_filenames]
aff_mat_filenames = [name.split(".")[0] + "_aff_matrix.txt" for name in long_filenames]
nonlin_reg_filenames = [name.split(".")[0] + "_nonlin.nii" for name in long_filenames]
nonlin_cpp_filenames = [name.split(".")[0] + "_nonlin_cpp.nii" for name in long_filenames]
segmented_filenames = [name.split(".")[0] + "_brain.nii" for name in long_filenames]
labeled_temp_filenames = [name + "_brain.nii" for name in template_filenames_stubs]

aladin_options = "-speeeeed ";

# max 4 levels, 300 iterations each
f3d_options = "-ln 4 -maxit 200"; # I think 4 lvl x 200 it is ideal
#f3d_options = "-ln 1 -maxit 10"; # I think 4 lvl x 200 it is ideal
# 2 lvl 200 it - 1m26sec
# 3 lvl 300 it - 2m16sec
# 4 lvl 300 it - 2m18sec
# 4 lvl 200 it - 1m30sec

exec_cmd = 1;

sample_img = nib.load('t2_AD_11_followup_brain.nii')
print sample_img.shape
(dimX, dimY, dimZ) = sample_img.shape

print segmented_filenames

NR_TEMPLATES = len(template_filenames)
NR_FILES = len(long_filenames)

#os.system("cd longitudinal_images/")
for i in range(NR_FILES):
  
  fused_image = np.zeros((dimX, dimY, dimZ),int)
  for t in range(NR_TEMPLATES):

    segmented_file_full = "t%d_%s" % (t, segmented_filenames[i])
    imgt = nib.load(segmented_file_full)

    data = imgt.get_data()
  
    fused_image += data

  # do majority voting
  fused_image = (fused_image > (NR_TEMPLATES/2)).astype(np.uint8);  
  
  nib_fused_image = nib.Nifti1Image(fused_image, np.eye(4))
  nib.save(nib_fused_image, segmented_filenames[i])

 
