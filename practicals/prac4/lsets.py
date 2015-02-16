
import numpy as np
import scipy as sc
import scipy.ndimage as ndi
import matplotlib.pyplot as plt


def NeumannBoundCond(x):
  x[0,0] = x[2,2] 
  x[0,-1] = x[2,-3] 
  x[-1,0] = x[-3,2] 
  x[-1,-1] = x[-3,-3] 
  x[0,1:-2] = x[2,1:-2] 
  x[-1,1:-2] = x[-3,1:-2] 
  x[1:-2,0] = x[1:-2,2] 
  x[1:-2,-1] = x[1:-2,-3] 

  return x

epsilon = 1.5
sigmaIn = 0.8
ts = 3.0
Internal_weight = 0.05/ts
Length_weight = 10.0
Area_weight = -20.0
numiter = 500


imgData = sc.ndimage.imread("Obj.bmp")
LevelSet = ndi.imread("Start.bmp", np.float64)
LevelSet = ((LevelSet>0)*8)-4

print np.shape(LevelSet)

imgSmooth = ndi.gaussian_filter(imgData, sigma=(2,2), order=0, mode='reflect')
imgX = ndi.gaussian_filter(imgData, sigma=(1,0), order=1, mode='reflect')
imgY = ndi.gaussian_filter(imgData, sigma=(0,1), order=1, mode='reflect')

g = 1/(1+(imgX**2 + imgY**2))
Vx = ndi.gaussian_filter(g, sigma=(1,0), order=1, mode='reflect')
Vy = ndi.gaussian_filter(g, sigma=(0,1), order=1, mode='reflect')


for i in range(1000):

  # penalising term
  Laplacian = ndi.filters.laplace(LevelSet, mode='reflect', cval=0.0)

  print np.shape(LevelSet)
  LevelSetGradX = ndi.gaussian_filter(LevelSet, sigma=(1,0), order=1, mode='reflect')
  LevelSetGradY = ndi.gaussian_filter(LevelSet, sigma=(0,1), order=1, mode='reflect')
  normDu = np.sqrt(LevelSetGradX**2 + LevelSetGradY**2 + 1e-10);

  Nx = LevelSetGradX/normDu
  Ny = LevelSetGradY/normDu

  Nxx = ndi.gaussian_filter(Nx, sigma=(1,0), order=1, mode='reflect')
  Nyy = ndi.gaussian_filter(Ny, sigma=(0,1), order=1, mode='reflect')
  Divergence = Nxx = Nyy
  
  PenalisingTerm = Internal_weight * (Laplacian/16.0*13.0 - Divergence)

  PenalisingTerm = PenalisingTerm * ( (PenalisingTerm > 0.01) | (PenalisingTerm < -0.01) )
  
  # weighted length term

  Dirac = ((1.0/2.0)/ epsilon) * (1.0 + np.cos(np.pi*LevelSet/epsilon)) * (LevelSet <= epsilon) * (LevelSet >= -epsilon)

  Divergence2 = (Vx*Nx + Vy*Ny + g*Divergence)

  WeightedLengthTerm = Length_weight * Dirac * Divergence2

  # Weighted Area term
  WeightedAreaTerm = Area_weight * g * Dirac

  
  # put it all together
  LevelSet = LevelSet + ts*(PenalisingTerm + WeightedLengthTerm + WeightedAreaTerm);

  LevelSet = NeumannBoundCond(LevelSet)

  
segImage = LevelSet > 0 
segImage.show()
plt.imshow(segImage)
