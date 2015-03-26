function checkNii()

addpath NIFTI_20110921

img_orig = load_nii('longitudinal_images/AD_0_baseline.nii');

img_seg_mine = load_nii('longitudinal_images/AD_0_baseline_seg.nii');

img_seg_orig = load_nii('longitudinal_images/AD_0_baseline_brain.nii');

diff_img = img_seg_mine;
diff_img.img = img_seg_mine.img - img_seg_orig.img;

for i=0:10
  
  figure(1)
  dispNiiSlice(img_orig, 'z', 100 + 10*i);
  title('orig img')
  
  figure(2)
  dispNiiSlice(diff_img, 'z', 100 + 10*i);
  title('diff seg img')
  
  figure(3)
  dispNiiSlice(img_seg_mine, 'z', 100+10*i);
  title('img my seg')
  
  figure(4)
  dispNiiSlice(img_seg_orig, 'z', 100+10*i);
  title('img seg orig')
end

end