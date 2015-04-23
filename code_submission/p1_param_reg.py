import os

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

exec_cmd = 1
debug = 0

level_indices = range(len(levels))
iter_indices = range(len(iterations))
r_indices= range(1,3) # only do 3 rounds out of 10, because it takes a very long time
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

for l in level_indices:
  for it in iter_indices:
    f3d_options = "-ln %d -maxit %d" % (levels[l], iterations[it]); # I think 4 lvl x 200 it is ideal

    for r in r_indices:
      t_indices = range(0,r) + range(r+1,NR_TEMP)
      print t_indices
      if debug:
        t_indices = [t_indices[0]]
      t_indices = [r-1]

      fold_prefix = "l%di%d/r%d" % (l, it,r)
      os.system("mkdir -p %s" % fold_prefix)
      
      for t in t_indices:
        aff_reg_cmd = 'reg_aladin -ref %s -flo %s -res %s/%s -aff %s/%s %s' % (templates[r], templates[t], fold_prefix, aff_reg_filenames[t], fold_prefix, aff_mat_filenames[t], aladin_options)
        print aff_reg_cmd
        if exec_cmd:
          os.system(aff_reg_cmd)
        
        nonlin_reg_cmd = 'reg_f3d -ref %s -flo %s -res %s/%s -aff %s/%s -cpp %s/%s %s' % (templates[r], templates[t], fold_prefix, nonlin_reg_filenames[t], fold_prefix, aff_mat_filenames[t], fold_prefix, nonlin_cpp_filenames[t], f3d_options)

        print nonlin_reg_cmd
        if exec_cmd:
          os.system(nonlin_reg_cmd)

        resample_cmd = 'reg_resample -ref %s -flo %s -res %s/%s -trans %s/%s -inter 0' % (templates[r], labeled_temp_filenames[t], fold_prefix, segmented_filenames[t], fold_prefix, nonlin_cpp_filenames[t])

        print resample_cmd
        if exec_cmd:
          os.system(resample_cmd)


