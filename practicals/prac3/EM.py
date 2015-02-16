#! /usr/bin/python

import numpy as np
import scipy.stats
from PIL import Image
import matplotlib.pyplot as plt

def read_file(filename):
    imagefile = Image.open(filename)
    image_array = np.array(imagefile.getdata(), np.uint8).reshape(imagefile.size[1], imagefile.size[0])
    return image_array.astype('float32')

def array_to_image(array):
    minimal_value = np.min(array)
    maximal_value = np.max(array)
    if minimal_value < 0 or maximal_value > 255:
        array = 255*(array-minimal_value)/(maximal_value-minimal_value)
    array_uint8 = array.astype('uint8')
    return Image.fromarray(array_uint8, 'L')

def save_file(array,filename):
    imagefile = array_to_image(array)
    imagefile.save(filename)


print "Loading data"
imgData = read_file("brain.png")

mask = imgData > 30;

# Priors
GM_Prior = read_file("GM_prior.png")
WM_Prior = read_file("WM_prior.png")
CSF_Prior = read_file("CSF_prior.png")
Other_Prior = read_file("NonBrain_prior.png")


didNotConverge = 1
numclass = 4

#initialise mean and variances
mean  = np.random.rand(numclass,1)*256;
var = (np.random.rand(numclass,1)*10)+200;

# Allocate space for the posteriors
classProb=np.ndarray([np.size(imgData,0),np.size(imgData,1),numclass])
classProbSum=np.ndarray([np.size(imgData,0),np.size(imgData,1)])

# Allocate space for the priors if using them
classPrior=np.ndarray([np.size(imgData,0),np.size(imgData,1),4])
classPrior[:, :, 0] = GM_Prior/255
classPrior[:, :, 1] = WM_Prior/255
classPrior[:, :, 2] = CSF_Prior/255
classPrior[:, :, 3] = Other_Prior/255


logLik=-1000000000
oldLogLik=-1000000000
iteration=0

# Iterative process
while didNotConverge:
    iteration=iteration+1

    # Expectation
    classProbSum[:, :] = 0;
    for classIndex in range(0, numclass):
        gaussPdf = scipy.stats.norm(mean[classIndex], var[classIndex]).pdf(imgData)
        classProb[:, :, classIndex] = gaussPdf * classPrior[:,:,classIndex]; # use equal priors on all classes
        classProbSum[:, :] += classProb[:,:,classIndex]

    # normalise posterior
    for classIndex in range(0, numclass):
        classProb[:, :, classIndex] = classProb [:,:, classIndex] / classProbSum

    # Cost function
    oldLogLik = logLik
    logLik = np.sum(np.sum(np.log(classProbSum),1),0)
    print str(logLik) + "   " + str((-logLik - oldLogLik)/-(oldLogLik))

    # Maximization
    for classIndex in range(0, numclass):
        pik = mask.flatten() * classProb[:,:, classIndex].flatten()
        mean[classIndex] = np.sum(pik * imgData.flatten())/np.sum(pik)
        var[classIndex] = np.sum(pik*((imgData.flatten() - mean[classIndex])**2))/np.sum(pik)

        print str(classIndex)+" = "+str(mean[classIndex])+" , "+str(var[classIndex])

    if (logLik - oldLogLik)/-oldLogLik < 0.00001 and iteration > 5:
        didNotConverge=0


np.histogram(imgData.flatten())
plt.hist(imgData.flatten(), 200)
plt.show()
 
save_file(classProb[ : ,: ,0] * 255, "seg0.png")
save_file(classProb[ : ,: ,1] * 255, "seg1.png")
save_file(classProb[ : ,: ,2] * 255, "seg2.png")
save_file(classProb[ : ,: ,3] * 255, "seg3.png")
