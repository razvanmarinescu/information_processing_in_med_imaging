function checkNii()

addpath NIFTI_20110921

img_seg = load_nii('longitudinal_images/AD_0_baseline_seg.nii');

img_orig = load_nii('longitudinal_images/AD_0_baseline_brain.nii');

diff_img = img_seg;
diff_img.img = img_seg.img - img_orig.img;

for i=0:10
  figure(1)
  dispNiiSlice(diff_img, 'z', 100 + 10*i);
  title('diff img')
  
  figure(2)
  dispNiiSlice(img_seg, 'z', 100+10*i);
  title('img seg')
  
  figure(3)
  dispNiiSlice(img_orig, 'z', 100+10*i);
  title('img_orig')
end
end