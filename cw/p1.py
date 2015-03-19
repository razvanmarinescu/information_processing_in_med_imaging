import os

NR_TEMP = 10;
NR_SEG = 5;

template_filenames = ['template_database/template_' + str(i) + '.nii' for i in range(NR_TEMP)]
long_AD_baseline_filenames = ['longitudinal_images/AD_' + str(i) + '_baseline.nii' for i in range(10,10+NR_SEG)]
long_AD_followup_filenames = ['longitudinal_images/AD_' + str(i) + '_followup.nii' for i in range(10,10+NR_SEG)]
long_CTL_baseline_filenames = ['longitudinal_images/CTL_' + str(i) + '_baseline.nii' for i in range(10,10+NR_SEG)]
long_CTL_followup_filenames = ['longitudinal_images/CTL_' + str(i) + '_followup.nii' for i in range(10,10+NR_SEG)]

long_filenames = long_AD_baseline_filenames + long_AD_followup_filenames + long_CTL_baseline_filenames + long_CTL_followup_filenames

aff_reg_filenames = [name.split(".")[0] + "_aff.nii" for name in long_filenames]
aff_mat_filenames = [name.split(".")[0] + "_aff_matrix.txt" for name in long_filenames]
for i in [1]:#range(len(long_filenames)):
  aff_reg_cmd = 'reg_aladin -ref %s -flo %s -res %s -aff %s' % (template_filenames[0], long_filenames[i], aff_reg_filenames[i], aff_mat_filenames[i])
  print aff_reg_cmd
  os.system(aff_reg_cmd)
