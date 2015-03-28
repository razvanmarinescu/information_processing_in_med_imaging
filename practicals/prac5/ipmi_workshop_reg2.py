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

# Below are some utilities that will enable you to manipulate images
def read_png_file(filename):
    png=Image.open(filename)
    image_array=np.array(png.getdata(),np.uint8).reshape(png.size[1], png.size[0])
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
    reference_image = np.zeros((dim,dim))
    floating_image  = np.zeros((dim,dim))

    # The reference image will contain a circle
    for j in range(0,dim):
    	 for i in range(0,dim):
    	 	dist=np.sqrt(np.abs(i-dim/2)*np.abs(i-dim/2)+np.abs(j-dim/2)*np.abs(j-dim/2))
    	 	if dist<dim/3:
	    	 	reference_image[i,j]=255
    # The floating image will contain a square
    floating_image[dim/4:dim-dim/4,dim/4:dim-dim/4]=255
    
    # Both images are smoothed using a Gaussian kernel. The first argument is a numpy array
    # corresponding to the image to smooth and the second argument is the standard deviation
    # of the Gaussian kernel used for smooothing
    smoothedRef_image = registration.smoothing(reference_image, 10)
    smoothedFlo_image = registration.smoothing(floating_image, 10)
    
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
    
    for i in range(0,10):
        # The optical float between the two images is computed
        ssd_gradient = registration.gradient(smoothedRef_image, \
                                             smoothedFlo_image, \
                                             displacementField, \
                                             interpolationType)
    
        # The gradient is scaled
        scaling = np.max(ssd_gradient)
        if scaling < np.abs(np.min(ssd_gradient)):
            scaling = np.abs(np.min(ssd_gradient))
        ssd_gradient /= scaling
                                         
        # The optical flow is composed with the current displacement field
        displacementField = registration.composition(ssd_gradient, displacementField)
           
        # The floating image is warped based on the displacement field
        warped_image = registration.resample(smoothedFlo_image, \
                                             displacementField, \
                                             interpolationType)
                                         
        # The sum squared difference between both image is computed
        ssd_value = registration.measure(smoothedRef_image, warped_image)
        print('New value = '+str(ssd_value))

#    display_image(smoothedRef_image)   
#    display_image(smoothedFlo_image)   
#    display_image(warped_image)   
    
    # Compute the map of Jacobian determinant of the transformation
    jacobian_map = registration.jacobian(displacementField)
    print('Jacobian determinant min value:\t'+str(np.min(jacobian_map)))
    print('Jacobian determinant max value:\t'+str(np.max(jacobian_map)))
    # Log scaled is used for display
#    mask=jacobian_map<=0
#    jacobian_map[mask]=10.e-20;
#    display_image(np.log(jacobian_map))  
    

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
