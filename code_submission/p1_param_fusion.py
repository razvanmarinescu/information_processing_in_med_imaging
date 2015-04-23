import os
import nibabel as nib
import numpy as np
import csv


NR_TEMP = 10;
NR_SEG = 5;

template_stubs = ['../template_database/template_' + str(i) for i in range(NR_TEMP)]

templates = [x + ".nii" for x in template_stubs]

aff_reg_filenames = [str(i) + "_aff.nii" for i in range(NR_TEMP)]
aff_mat_filenames = [str(i) + "_aff_matrix.txt" for i in range(NR_TEMP)]
nonlin_reg_filenames = [str(i) + "_nonlin.nii" for i in range(NR_TEMP)]
nonlin_cpp_filenames = [str(i) + "_nonlin_cpp.nii" for i in range(NR_TEMP)]
segmented_filenames = [str(i) + "_brain.nii" for i in range(NR_TEMP)]
labeled_temp_filenames = [name + "_brain.nii" for name in template_stubs]

aladin_options = "-speeeeed ";

levels = [2,3,4,5]
iterations = [50, 150, 200,300]

debug = 0

level_indices = range(len(levels))
iter_indices = range(len(iterations))
r_indices= range(10) # only do 3 rounds out of 10, because it takes a very long time
if debug:
  level_indices=[0]
  iter_indices=[0]    
  r_indices = [0]

# max 4 levels, 300 iterations each
#f3d_options = "-ln 1 -maxit 10"; # I think 4 lvl x 200 it is ideal
# 2 lvl 200 it - 1m26sec
# 3 lvl 300 it - 2m16sec
# 4 lvl 300 it - 2m18sec
# 4 lvl 200 it - 1m30sec

#os.system("cd longitudinal_images/")

sample_img = nib.load('t2_AD_11_followup_brain.nii')
print sample_img.shape
(dimX, dimY, dimZ) = sample_img.shape

def compDice(a, b):
  return 2*np.sum(a*b)/np.sum(a+b) 


dice = np.zeros((len(level_indices), len(iter_indices), len(r_indices)), float)

for l in level_indices:
  for it in iter_indices:
    f3d_options = "-ln %d -maxit %d" % (levels[l], iterations[it]); # I think 4 lvl x 200 it is ideal

    for r in r_indices:
      t_indices = range(0,r) + range(r+1,NR_TEMP)
      #print t_indices
      if debug:
        t_indices = [t_indices[0]]

      fold_prefix = "l%di%d/r%d" % (l, it,r)
      os.system("mkdir -p %s" % fold_prefix)
    
      fused_image = np.zeros((dimX, dimY, dimZ),int)      

      for t in t_indices:
        imgt = nib.load("%s/%s" % (fold_prefix, segmented_filenames[t]))
        data = imgt.get_data()
        fused_image += data


      # do majority voting
      fused_image = (fused_image > (len(t_indices)/2)).astype(np.uint8);  
      
      nib_fused_image = nib.Nifti1Image(fused_image, imgt.affine)
      nib.save(nib_fused_image, fold_prefix + "/fused.nii")


      tempImg = nib.load(templates[r])
      tempData = imgt.get_data()

      dice[l,it,r] = compDice(fused_image, tempData)
      #print dice[l,it,r]


print dice
#with open("../dice.txt","w") as f:
#  writer = csvwriter(f, delimiter=',')
np.savetxt("../dice_l0.txt", dice[0,:,:], delimiter=',')
np.savetxt("../dice_l1.txt", dice[1,:,:], delimiter=',')
np.savetxt("../dice_l2.txt", dice[2,:,:], delimiter=',')
np.savetxt("../dice_l3.txt", dice[3,:,:], delimiter=',')
