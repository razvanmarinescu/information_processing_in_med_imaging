import os
import nibabel as nib
import scipy

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
f3d_options = "-ln 4 -maxit 200"; # I think 4 lvl x 200 it is ideal
#f3d_options = "-ln 1 -maxit 10"; # I think 4 lvl x 200 it is ideal
# 2 lvl 200 it - 1m26sec
# 3 lvl 300 it - 2m16sec
# 4 lvl 300 it - 2m18sec
# 4 lvl 200 it - 1m30sec

exec_cmd = 1;

#os.system("cd longitudinal_images/")
i = 0
t = 0

img1 = nib.load(long_filenames[i])
ref = img1.get_data()

img2 = nib.load(template_filenames[t])
flo = img2.get_data()

diff = ref - flo
print img1.shape

scipy.misc.imsave('diff_x.jpg', diff[100,:,:])

aff_reg_cmd = 'reg_aladin -ref %s -flo %s -res t%d_%s -aff t%d_%s %s' % (long_filenames[i], template_filenames[t], t, aff_reg_filenames[i], t, aff_mat_filenames[i], aladin_options)

nonlin_reg_cmd = 'reg_f3d -ref %s -flo %s -res t%d_%s -aff t%d_%s -cpp t%d_%s %s' % (long_filenames[i], template_filenames[t], t, nonlin_reg_filenames[i], t, aff_mat_filenames[i], t, nonlin_cpp_filenames[i], f3d_options)

resample_cmd = 'reg_resample -ref %s -flo %s -res t%d_%s -trans t%d_%s -inter 0' % (long_filenames[i], labeled_temp_filenames[t], t, segmented_filenames[i], t, nonlin_cpp_filenames[i])



