import os
import nibabel as nib
import scipy
import scipy.ndimage.interpolation
#import skimage
import numpy as np
from scipy import ndimage

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

seg_mid_base_filenames = [name.split(".")[0] + "_midspace_brain.nii" for name in long_AD_baseline_filenames]
seg_mid_followup_filenames = [name.split(".")[0] + "_midspace_brain.nii" for name in long_AD_followup_filenames]

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

xSlice = 100;
ySlice = 65;
zSlice = 132;
foldPrefix = '../report/figures/diff/'

img1 = nib.load(long_filenames[i])
ref = img1.get_data()
print img1.affine[0:3, 0:3]
print ref.dtype

# rescale the images
#trans_ref = scipy.ndimage.interpolation.zoom(ref, (0.9375,1.5,0.9375))
#print trans_ref.shape
#trans_flo = scipy.ndimage.interpolation.zoom(flo, (0.9375,1.5,0.9375))
#print trans_flo.shape

# initial difference
img2 = nib.load(template_filenames[t])
flo = img2.get_data()

diffInit = ref - flo
scipy.misc.imsave(foldPrefix + 't1Init_x.jpg', diffInit[xSlice,:,:])
scipy.misc.imsave(foldPrefix + 't1Init_y.jpg', diffInit[:,ySlice,:])
scipy.misc.imsave(foldPrefix + 't1Init_z.jpg', diffInit[:,:,zSlice])

nib_diff = nib.Nifti1Image(diffInit, img1.affine)
nib.save(nib_diff, '../diffInit.nii')

# after affine transformation
img3 = nib.load(aff_reg_filenames[i])
aff = img3.get_data()
diffAff = ref - aff
nib_diff = nib.Nifti1Image(diffAff, img1.affine)
nib.save(nib_diff, '../diffAff.nii')

scipy.misc.imsave(foldPrefix + 't1Aff_x.jpg', diffAff[xSlice,:,:])
scipy.misc.imsave(foldPrefix + 't1Aff_y.jpg', diffAff[:,ySlice,:])
scipy.misc.imsave(foldPrefix + 't1Aff_z.jpg', diffAff[:,:,zSlice])

# after nonlinear deformation
img4 = nib.load(nonlin_reg_filenames[i])
nonlin = img4.get_data()
diffNonlin = ref - nonlin
nib_diff = nib.Nifti1Image(diffNonlin, img1.affine)
nib.save(nib_diff, '../diffNonlin.nii')

scipy.misc.imsave(foldPrefix + 't1Nonlin_x.jpg', diffNonlin[xSlice,:,:])
scipy.misc.imsave(foldPrefix + 't1Nonlin_y.jpg', diffNonlin[:,ySlice,:])
scipy.misc.imsave(foldPrefix + 't1Nonlin_z.jpg', diffNonlin[:,:,zSlice])

# segmentation overlaying t1 image
img5 = nib.load(segmented_filenames[i])
seg = img5.get_data()

maxIntensity = np.max(ref)
maxSeg = np.max(seg)

print maxIntensity
print maxSeg
seg = seg * maxIntensity * 1
segOverlay = np.maximum(ref, seg)
scipy.misc.imsave(foldPrefix + 't1Seg_x.jpg', segOverlay[xSlice,:,:])
scipy.misc.imsave(foldPrefix + 't1Seg_y.jpg', segOverlay[:,ySlice,:])
scipy.misc.imsave(foldPrefix + 't1Seg_z.jpg', segOverlay[:,:,zSlice])

nib_diff = nib.Nifti1Image(segOverlay, img1.affine)
nib.save(nib_diff, '../segOverlay.nii')

# boundary region between baseline and followup

img6 = nib.load(seg_mid_base_filenames[i])
seg_mid_base_data = img6.get_data()

img7 = nib.load(seg_mid_followup_filenames[i])
seg_mid_followup_data = img7.get_data()

seg_union = ((seg_mid_base_data + seg_mid_followup_data) >= 1).astype(np.uint8); 
seg_intersection = ((seg_mid_base_data + seg_mid_followup_data) == 2).astype(np.uint8); 

# dilate the union and erode the intersection
struct1 = ndimage.generate_binary_structure(3, 2)
dil_seg_union = ndimage.binary_dilation(seg_union, structure=struct1, iterations=1).astype(seg_union.dtype)
ero_seg_intersection = ndimage.binary_erosion(seg_intersection, structure=struct1, iterations=1).astype(seg_intersection.dtype)

# obtain the boundary region by XORing the dilated union and eroded segmentation
segBoundary = ((dil_seg_union + ero_seg_intersection ) == 1).astype(np.uint8)
segBoundary = segBoundary * 256

scipy.misc.imsave(foldPrefix + 'bsiBoundary_x.jpg', segBoundary[135,:,:])
scipy.misc.imsave(foldPrefix + 'bsiBoundary_y.jpg', segBoundary[:,74,:])
scipy.misc.imsave(foldPrefix + 'bsiBoundary_z.jpg', segBoundary[:,:,154])

nib_diff = nib.Nifti1Image(segBoundary, img6.affine)
nib.save(nib_diff, '../bsiBoundary.nii')


