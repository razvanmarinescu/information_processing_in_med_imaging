#! /usr/bin/env python

# During this workshop, we will develop a simple 2D implementation of the demons algorithm.
# For this purpose, a python module has been developed. It contains all the required functions.
# The functions are located in the "ipmi_workshop.cpp", which you first need to compile.
# This can be done by running the file setup.py with the following command:
# $ python setup.py build_ext --inplace

# In your python file, you will then be able to import the compiled module, e.g.:
import ipmi_workshop as registration

# We also need to import other relevant modules such as:
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pdb

# Below are some utilities that will enable you to manipulate images
def read_png_file(filename):
    png=Image.open(filename)
    image_array=np.array(png.getdata(),np.uint8)[:,0].reshape(png.size[1], png.size[0])
    return image_array.astype('float64')

def array_to_image(array):
    minimal_value=np.min(array)
    maximal_value=np.max(array)
    if minimal_value < 0 or maximal_value > 255:
        array = 255*(array-minimal_value)/(maximal_value-minimal_value)
    array_uint8=array.astype('uint8')
    return Image.fromarray(array_uint8, 'L')

def save_png_file(array,filename):
    png=array_to_image(array)
    png.save(filename)

def display_image(array):
    png=array_to_image(array)
    png.show()
    
# Within the main, the functions implemented in the registration module are presented    
def main():

    # Let first create two images: one reference and one floating image
    dim=255
    reference_image = read_png_file("image_10.png")
    floating_image  = read_png_file("image_11.png")


    # Both images are smoothed using a Gaussian kernel. The first argument is a numpy array
    # corresponding to the image to smooth and the second argument is the standard deviation
    # of the Gaussian kernel used for smooothing
    #smoothedRef_image = registration.smoothing(reference_image, 10)
    #smoothedFlo_image = registration.smoothing(floating_image, 10)
    
    smoothedRef_image = reference_image;
    smoothedFlo_image = floating_image;
 

    # An displacement field encoding an identity transformation is created.
    displacementField = np.zeros((reference_image.shape[0],reference_image.shape[1],2))
    
    # The floating image is warped based on the displacement field
    interpolationType = 3
    # 0, 1 and 3 denotes nearest-neighbour, linear and cubic interpolation respectively
    
    warped_image = registration.resample(smoothedFlo_image, \
                                         displacementField, \
                                         interpolationType)
        
    # The sum squared difference between both image is computed
    ssd_value = registration.measure(smoothedRef_image, warped_image)
    print('Ini value = '+str(ssd_value))
    
    for i in range(0,200):
        # The optical float between the two images is computed
        ssd_gradient = registration.gradient(smoothedRef_image, \
                                             smoothedFlo_image, \
                                             displacementField, \
                                             interpolationType)
    
        ssd_gradient = registration.smoothing(ssd_gradient, 3);
        #print np.shape(ssd_gradient)

        # The gradient is scaled
        scaling = np.max(ssd_gradient)
        if scaling < np.abs(np.min(ssd_gradient)):
            scaling = np.abs(np.min(ssd_gradient))
        ssd_gradient /= scaling
                                         
        # The optical flow is composed with the current displacement field
        displacementField = registration.composition(ssd_gradient, displacementField)

           
        #displacementField = registration.smoothing(displacementField, 0.5);

        # The floating image is warped based on the displacement field
        warped_image = registration.resample(smoothedFlo_image, \
                                             displacementField, \
                                             interpolationType)
                                         
        # The sum squared difference between both image is computed
        ssd_value = registration.measure(smoothedRef_image, warped_image)
        print('New value = '+str(ssd_value))

    #display_image(smoothedRef_image)   
    #display_image(smoothedFlo_image)   
    #display_image(warped_image)   
    
    # Compute the map of Jacobian determinant of the transformation
    jacobian_map = registration.jacobian(displacementField)
    print('Jacobian determinant min value:\t'+str(np.min(jacobian_map)))
    print('Jacobian determinant max value:\t'+str(np.max(jacobian_map)))
    # Log scaled is used for display
#    mask=jacobian_map<=0
#    jacobian_map[mask]=10.e-20;
#    display_image(np.log(jacobian_map))  
    
    types = ["brain", "lhippo", "rhippo", "vens"]
    src_images = [ "image_11_" + i + ".png" for i in types]
    trg_images = [ "image_10_" + i + ".png" for i in types]
    # brain

    dice_before = []
    dice_after = []
    for i in range(len(types)):
      seg_source = read_png_file(src_images[i]);
      seg_source_propag = registration.resample(seg_source, displacementField,0);
      seg_target = read_png_file(trg_images[i]);
      dice_before += [calc_dice(seg_source, seg_target)]
      dice_after += [calc_dice(seg_source_propag, seg_target)]
   
    print "dice_before:", dice_before
    print "dice_after:", dice_after

    dice_sum = sum(dice_after)
    print dice_sum
    
    #ssd_value = registration.measure(seg_source, seg_source_propag)
    #print ssd_value

    #display_image(seg_source)
    #display_image(seg_source_propag)

 

  
def calc_dice(seg_source, seg_target):

  AandB = np.count_nonzero((seg_source + seg_target) == 255*2)

  A = np.count_nonzero(seg_source)
  B = np.count_nonzero(seg_target)

  score = 2*(float(AandB)/(A+B))
  print AandB, A, B, score

  return score  




def readme_workshop():
    print('')
    print('********** Workshop Registration 2 - IPMI Module **********')
    print('')
    print('In the current folder, you will find several 2D images and associated segmentations.')
    print('Based on the functions presented in the main function of this file, implement a demons')
    print('algorithm. Use segmentation propagation to assess the quality of the obtained')
    print('registrations (by computing the Dice Score between propagated and real segmentation) and')
    print('ensure that no folding is generated. Use then a cross-validation approach to segment all')
    print('10 images provided using the 9 others as templates. Majority voting can be used to fuse')
    print('the propagated segmentations.')
    print('')
    
if __name__ == "__main__":
    readme_workshop()
    main()
