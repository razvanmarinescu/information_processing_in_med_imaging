import os

NR_TEMP = 10;
NR_SEG = 5;

template_filenames_stubs = ['../template_database/template_' + str(i) for i in range(NR_TEMP)]
long_AD_baseline_filenames = ['AD_' + str(i) + '_baseline.nii' for i in range(10,10+NR_SEG)]
long_AD_followup_filenames = ['AD_' + str(i) + '_followup.nii' for i in range(10,10+NR_SEG)]
long_CTL_baseline_filenames = ['CTL_' + str(i) + '_baseline.nii' for i in range(10,10+NR_SEG)]
long_CTL_followup_filenames = ['CTL_' + str(i) + '_followup.nii' for i in range(10,10+NR_SEG)]

template_filenames = [x + ".nii" for x in template_filenames_stubs]
long_filenames = long_AD_baseline_filenames + long_AD_followup_filenames + long_CTL_baseline_filenames + long_CTL_followup_filenames
#long_filenames = ['longitudinal_images/AD_0_baseline.nii']
#template_filenames = template_filenames[0]

aff_reg_filenames = [name.split(".")[0] + "_aff.nii" for name in long_filenames]
aff_mat_filenames = [name.split(".")[0] + "_aff_matrix.txt" for name in long_filenames]
nonlin_reg_filenames = [name.split(".")[0] + "_nonlin.nii" for name in long_filenames]
nonlin_cpp_filenames = [name.split(".")[0] + "_nonlin_cpp.nii" for name in long_filenames]
segmented_filenames = [name.split(".")[0] + "_brain.nii" for name in long_filenames]
labeled_temp_filenames = [name + "_brain.nii" for name in template_filenames_stubs]

aladin_options = "-speeeeed ";

# max 4 levels, 300 iterations each
f3d_options = "-ln 4 -maxit 10"; # I think 4 lvl x 200 it is ideal
# 2 lvl 200 it - 1m26sec
# 3 lvl 300 it - 2m16sec
# 4 lvl 300 it - 2m18sec
# 4 lvl 200 it - 1m30sec

exec_cmd = 1;

#os.system("cd longitudinal_images/")
for i in range(1):
  
  for t in range(1):
    aff_reg_cmd = 'reg_aladin -ref %s -flo %s -res %s -aff %s %s' % (long_filenames[i], template_filenames[t], aff_reg_filenames[i], aff_mat_filenames[i], aladin_options)
    print aff_reg_cmd
    if exec_cmd:
      os.system(aff_reg_cmd)
    
    nonlin_reg_cmd = 'reg_f3d -ref %s -flo %s -res %s -aff %s -cpp %s %s' % (long_filenames[i], template_filenames[t], nonlin_reg_filenames[i], aff_mat_filenames[i], nonlin_cpp_filenames[i], f3d_options)

    print nonlin_reg_cmd
    if exec_cmd:
      os.system(nonlin_reg_cmd)

    resample_cmd = 'reg_resample -ref %s -flo %s -res %s -trans %s -inter 0' % (long_filenames[i], labeled_temp_filenames[t], segmented_filenames[i], nonlin_cpp_filenames[i])

    print resample_cmd
    if exec_cmd:
      os.system(resample_cmd)


