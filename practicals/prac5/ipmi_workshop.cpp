#include <stdio.h>
#include <Python.h>
#include <numpy/ndarrayobject.h>

/* *************************************************************** */
/* *************************************************************** */
static char resample_doc[] =
      "warpedImage = ipmi_workshop.resample(floatingImage, displacementField, interpolation)";
/* *************************************************************** */
void interpCubicSplineKernel(double relative, double *basis)
{
   if(relative<0.0) relative=0.0; //reg_rounding error
   double FF= relative*relative;
   basis[0] = (relative * ((2.0-relative)*relative - 1.0))/2.0;
   basis[1] = (FF * (3.0*relative-5.0) + 2.0)/2.0;
   basis[2] = (relative * ((4.0-3.0*relative)*relative + 1.0))/2.0;
   basis[3] = (relative-1.0) * FF/2.0;
}
void gradCubicSplineKernel(double relative, double *basis, double *derivative)
{
   interpCubicSplineKernel(relative,basis);
   if(relative<0.0) relative=0.0; //reg_rounding error
   double FF= relative*relative;
   derivative[0] = (4.0*relative - 3.0*FF - 1.0)/2.0;
   derivative[1] = (9.0*relative - 10.0) * relative/2.0;
   derivative[2] = (8.0*relative - 9.0*FF + 1)/2.0;
   derivative[3] = (3.0*relative - 2.0) * relative/2.0;
}
/* *************************************************************** */
void interpLinearKernel(double relative, double *basis)
{
   if(relative<0.0) relative=0.0; //reg_rounding error
   basis[1]=relative;
   basis[0]=1.0-relative;
}
void gradLinearKernel(double relative, double *basis, double *derivative)
{
   interpLinearKernel(relative, basis);
   if(relative<0.0) relative=0.0; //reg_rounding error
   derivative[0]=-1;
   derivative[1]=1;
}
/* *************************************************************** */
void interpNearestNeighKernel(double relative, double *basis)
{
   if(relative<0.0) relative=0.0; //reg_rounding error
   basis[0]=basis[1]=0;
   if(relative>0.5)
      basis[1]=1;
   else basis[0]=1;
}
/* *************************************************************** */
static PyObject *workshop_resample(PyObject *self, PyObject *args)
{
  /* Parse the arguments */
  PyObject *floating_obj;
  PyObject *dispField_obj;
  int interpType;
  if (!PyArg_ParseTuple(args, "OOi", &floating_obj, &dispField_obj, &interpType))
       return NULL;
  
  /* Conversion from Object to numpy arrays */
  PyObject *floating_np = PyArray_FROM_OTF(floating_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  PyObject *dispField_np = PyArray_FROM_OTF(dispField_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  
  /* Check for error */
   if (floating_np == NULL || dispField_np == NULL) {
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Error when parsing the input data in the resample function.");
       return NULL;
   }
   
   /* Perform some checks on the input arguments */
   if(interpType!=0 && interpType!=1 && interpType!=3){
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Interpolation type is expected to be equal to 0 (nearest-neighboor), 1 (linear) or 3 (cubic)");
       return NULL;
   }
   if(PyArray_NDIM(floating_np)!=2){
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The floating image is expected to have 2 dimensions");
       return NULL;
   }
   if(PyArray_NDIM(dispField_np)!=3){
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The displacement field image is expected to have 3 dimensions");
       return NULL;
   }
   if(PyArray_DIM(dispField_np, 2)!=2){
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The displacement field image is expected to have a dimension of 2 along the third axis");
       return NULL;
   }
   
   /* Conversion to C pointer */
   double *floatingData = static_cast<double *>(PyArray_DATA(floating_np));
   double *dispFieldData = static_cast<double *>(PyArray_DATA(dispField_np));
   
   /* Extract some relevant information */
   npy_intp floating_dim[2]={
      (npy_intp)PyArray_DIM(floating_np, 0),
      (npy_intp)PyArray_DIM(floating_np, 1)
   };
   npy_intp dispField_dim[2]={
      (npy_intp)PyArray_DIM(dispField_np, 0),
      (npy_intp)PyArray_DIM(dispField_np, 1)
   };
   
   /* Create a warped image array */
   double *warpedData = (double *)calloc(dispField_dim[0]*dispField_dim[1], sizeof(double));
   
   /* Perform the actual resampling */
   double xBasis[4], yBasis[4], relative[2];
   int a, b, X, previous[2];
   int kernel_size=2;
   int kernel_offset=0;
   void (*kernelCompFctPtr)(double,double *)=&interpLinearKernel;
   switch(interpType){
   case 0:
	  kernel_size=2;
	  kernelCompFctPtr=&interpNearestNeighKernel;
	  kernel_offset=0;
	  break; // nereast-neighboor interpolation
   case 1:
      kernel_size=2;
      kernelCompFctPtr=&interpLinearKernel;
      kernel_offset=0;
      break; // linear interpolation
   case 3:
      kernel_size=4;
      kernelCompFctPtr=&interpCubicSplineKernel;
      kernel_offset=1;
      break; // cubic spline interpolation
   }

   double paddingValue=0.;
   double *xyzPointer;
   double xTempNewValue, intensity, position[2];
   npy_intp index=0;
   for(npy_intp x=0; x<dispField_dim[0]; ++x)
   {
     for(npy_intp y=0; y<dispField_dim[1]; ++y)
     {
      // Numpy: Last index varies the fatest
      position[0]=dispFieldData[2*index]   + static_cast<double>(x);
      position[1]=dispFieldData[2*index+1] + static_cast<double>(y);

      previous[0] = floor(position[0]);
      previous[1] = floor(position[1]);

      relative[0]=position[0]-static_cast<double>(previous[0]);
      relative[1]=position[1]-static_cast<double>(previous[1]);

      (*kernelCompFctPtr)(relative[0], xBasis);
      (*kernelCompFctPtr)(relative[1], yBasis);
      previous[0] -= kernel_offset;
      previous[1] -= kernel_offset;

      intensity=0.;
      for(a=0; a<kernel_size; a++)
      {
         X = previous[0]+a;
         // Numpy: Last index varies the fatest
         xyzPointer = &floatingData[previous[1]+X*floating_dim[1]];
         xTempNewValue=0.0;
         for(b=0; b<kernel_size; b++)
         {
            if(-1<X && X<floating_dim[0] &&
               -1<(previous[1]+b) && (previous[1]+b)<floating_dim[1])
            {
               xTempNewValue +=  *xyzPointer * yBasis[b];
            }
            else
            {
               // paddingValue
               xTempNewValue +=  paddingValue * yBasis[b];
            }
            // Numpy: Last index varies the fatest
            xyzPointer++;
         }
         intensity += xTempNewValue * xBasis[a];
      }
      warpedData[index]=intensity;
      index++;
     } // y 
   } // x
   
   /* Clean up. */
   Py_DECREF(floating_np);
   Py_DECREF(dispField_np);
   
   /* return the warped image */ 
   PyObject* warped_np = PyArray_SimpleNewFromData(2, dispField_dim, NPY_DOUBLE, warpedData);
   //free(warpedData);

   return Py_BuildValue("O", warped_np);
}
/* *************************************************************** */
/* *************************************************************** */
static char measure_doc[] =
      "measureValue = ipmi_workshop.measure(referenceImage, warpedImage)";
/* *************************************************************** */
static PyObject *workshop_measure(PyObject *self, PyObject *args)
{
  /* Parse the arguments */
  PyObject *reference_obj;
  PyObject *warped_obj;
  if (!PyArg_ParseTuple(args, "OO", &reference_obj, &warped_obj))
       return NULL;
  
  /* Conversion from Object to numpy arrays */
  PyObject *reference_np = PyArray_FROM_OTF(reference_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  PyObject *warped_np = PyArray_FROM_OTF(warped_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  
  /* Check for error */
   if ((reference_np == NULL) || (warped_np == NULL)) {
       Py_XDECREF(reference_np);
       Py_XDECREF(warped_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Error when parsing the input data in the measure function.");
       return NULL;
   }
   if(PyArray_NDIM(reference_np)!=2 || PyArray_NDIM(warped_np)!=2){
       Py_XDECREF(reference_np);
       Py_XDECREF(warped_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The input images are expected to have 2 dimensions");
       return NULL;
   }
   npy_intp reference_dim[2]={
      (npy_intp)PyArray_DIM(reference_np, 0),
      (npy_intp)PyArray_DIM(reference_np, 1)
   };
   if((npy_intp)PyArray_DIM(warped_np, 0)!=reference_dim[0] ||
      (npy_intp)PyArray_DIM(warped_np, 1)!=reference_dim[1]){
       Py_XDECREF(reference_np);
       Py_XDECREF(warped_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The input images are expected to have the same dimension");
       return NULL;
   }

   /* Conversion to C pointer */
   double *referenceData = static_cast<double *>(PyArray_DATA(reference_np));
   double *warpedData = static_cast<double *>(PyArray_DATA(warped_np));

   /* Allocate a measure variable */
   double measure=0;
   
   /* Compute the SSD */
   for(npy_intp i=0; i<reference_dim[0]*reference_dim[1]; ++i)
      measure += (referenceData[i]-warpedData[i])*(referenceData[i]-warpedData[i]);
   
   /* Clean up. */
   Py_DECREF(reference_np);
   Py_DECREF(warped_np);
   
   /* return the deformation field image */ 
   return Py_BuildValue("d", measure);
}
/* *************************************************************** */
/* *************************************************************** */
static char gradient_doc[] =
      "gradientImage = ipmi_workshop.gradient(referenceImage, floatingImage, displacementField, interpType)";
/* *************************************************************** */
static PyObject *workshop_gradient(PyObject *self, PyObject *args)
{
  /* Parse the arguments */
  PyObject *reference_obj;
  PyObject *floating_obj;
  PyObject *dispField_obj;
  int interpType;
  if (!PyArg_ParseTuple(args, "OOOi", &reference_obj, &floating_obj,
                        &dispField_obj, &interpType))
       return NULL;
   
  /* Conversion from Object to numpy arrays */
  PyObject *reference_np = PyArray_FROM_OTF(reference_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  PyObject *floating_np = PyArray_FROM_OTF(floating_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  PyObject *dispField_np = PyArray_FROM_OTF(dispField_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  
  /* Check for error */
   if ((reference_np == NULL) || (floating_np == NULL) || (dispField_np == NULL)) {
       Py_XDECREF(reference_np);
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Error when parsing the input data in the gradient function.");
       return NULL;
   }   
   /* Perform some checks on the input arguments */
   if(interpType!=1 && interpType!=3){
       Py_XDECREF(reference_np);
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Interpolation type is expected to be equal to 1 (linear) or 3 (cubic)");
       return NULL;
   }
   if(PyArray_NDIM(reference_np)!=2){
       Py_XDECREF(reference_np);
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The reference image is expected to have 2 dimensions");
       return NULL;
   }
   if(PyArray_NDIM(floating_np)!=2){
       PyErr_SetString(PyExc_RuntimeError,
                       "The floating image is expected to have 2 dimensions");
       return NULL;
   }
   if(PyArray_NDIM(dispField_np)!=3){
       Py_XDECREF(reference_np);
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The displacement field image is expected to have 3 dimensions");
       return NULL;
   }
   if(PyArray_DIM(dispField_np, 2)!=2){
       Py_XDECREF(reference_np);
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The displacement field image is expected to have a dimension of 2 along the third axis");
       return NULL;
   }
   if(PyArray_DIM(reference_np, 0)!=PyArray_DIM(dispField_np, 0) ||
      PyArray_DIM(reference_np, 1)!=PyArray_DIM(dispField_np, 1)){
       Py_XDECREF(reference_np);
       Py_XDECREF(floating_np);
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The reference and displacement field are expected to have the same dimension along the first and second axis");
       return NULL;
   }
   
   /* Conversion to C pointer */
   double *referenceData = static_cast<double *>(PyArray_DATA(reference_np));
   double *floatingData = static_cast<double *>(PyArray_DATA(floating_np));
   double *dispFieldData = static_cast<double *>(PyArray_DATA(dispField_np));
   
   /* Extract some relevant information */
   npy_intp floating_dim[2]={
      (npy_intp)PyArray_DIM(floating_np, 0),
      (npy_intp)PyArray_DIM(floating_np, 1)
   };
   npy_intp dispField_dim[3]={
      (npy_intp)PyArray_DIM(dispField_np, 0),
      (npy_intp)PyArray_DIM(dispField_np, 1),
      (npy_intp)PyArray_DIM(dispField_np, 2)
   };
   
   /* Create a warped image array */
   double *gradientData = (double *)calloc(dispField_dim[0]*dispField_dim[1]*dispField_dim[2], sizeof(double));
   double *warpedData = (double *)calloc(dispField_dim[0]*dispField_dim[1], sizeof(double));
   
   /* Perform the actual SSD gradient computation */
   void (*kernelCompFctPtr)(double,double *,double *) = &gradLinearKernel;
   int kernel_size=2, kernel_offset=0;
   switch(interpType){
   case 1:
      kernel_size=2;
      kernelCompFctPtr=&gradLinearKernel;
      kernel_offset=0;
      break; // linear interpolation
   case 3:
      kernel_size=4;
      kernelCompFctPtr=&gradCubicSplineKernel;
      kernel_offset=1;
      break; // cubic spline interpolation
   }
   double xBasis[4], yBasis[4], deriv[4], relative[2];
   int a, b, X, previous[2];
   double paddingValue=0.;
   double *xyzPointer;
   double xTempNewValue, yTempNewValue;
   double warpedValue, gradientX, gradientY;
   double position[2];
   npy_intp index=0;
   for(npy_intp x=0; x<dispField_dim[0]; ++x)
   {
     for(npy_intp y=0; y<dispField_dim[1]; ++y)
     {
	  // Numpy: Last index varies the fatest
	  position[0]=dispFieldData[2*index] + (double)x;
	  position[1]=dispFieldData[2*index+1] + (double)y;

	  previous[0] = floor(position[0]);
	  previous[1] = floor(position[1]);

	  relative[0]=position[0]-static_cast<double>(previous[0]);
	  relative[1]=position[1]-static_cast<double>(previous[1]);

      (*kernelCompFctPtr)(relative[0], xBasis, deriv);
      (*kernelCompFctPtr)(relative[1], yBasis, deriv);
	  
	  previous[0] -= kernel_offset;
	  previous[1] -= kernel_offset;

	  warpedValue=0.;
	  gradientX=0.;
	  gradientY=0.;

	  for(a=0; a<kernel_size; a++)
	  {
		 X = previous[0]+a;
		 // Numpy: Last index varies the fatest
		 xyzPointer = &floatingData[previous[1]+X*floating_dim[1]];
		 xTempNewValue=0.0;
		 yTempNewValue=0.0;
		 for(b=0; b<kernel_size; b++)
		 {
			if(-1<X && X<floating_dim[0] &&
			   -1<(previous[1]+b) && (previous[1]+b)<floating_dim[1])
			{
			   xTempNewValue +=  *xyzPointer * yBasis[b];
			   yTempNewValue +=  *xyzPointer * deriv[b];
			}
			else
			{
			   // paddingValue
			   xTempNewValue +=  paddingValue * yBasis[b];
			   yTempNewValue +=  paddingValue * deriv[b];
			}
			// Numpy: Last index varies the fatest
			xyzPointer++;
		 }
		 warpedValue += xTempNewValue * xBasis[a];
		 gradientX   += xTempNewValue * deriv[a];
		 gradientY   += yTempNewValue * xBasis[a];
	  }
	  warpedData[index]    = warpedValue;
	  // Numpy: Last index varies the fatest
	  gradientData[2*index]  = gradientX;
	  gradientData[2*index+1]= gradientY;
	  index++;
     } // y
   } // x
   
   /* Optical Flow Computation */
   double *MeasureGradientData = (double *)calloc(dispField_dim[0]*dispField_dim[1]*dispField_dim[2], sizeof(double));
   double common;
   for(npy_intp index=0; index<dispField_dim[0]*dispField_dim[1]; ++index)
   {
      common=-2.f * (warpedData[index] - referenceData[index]);
      MeasureGradientData[2*index]  = common * gradientData[2*index];
      MeasureGradientData[2*index+1]= common * gradientData[2*index+1];
   }
   
   /* Clean up. */
   free(warpedData);
   free(gradientData);
   Py_DECREF(reference_np);
   Py_DECREF(floating_np);
   Py_DECREF(dispField_np);
   
   /* return the warped image */ 
   PyObject* MeasureGradient_np = PyArray_SimpleNewFromData(3, dispField_dim, NPY_DOUBLE, MeasureGradientData);
   //free(MeasureGradientData);

   return Py_BuildValue("O", MeasureGradient_np);
}
/* *************************************************************** */
/* *************************************************************** */
static char smoothing_doc[] =
      "smoothedImage = ipmi_workshop.smoothing(inputImage, kernelStdev)";
/* *************************************************************** */
void inplace_Gaussian_convolution(double *input_data,
                                  npy_intp *input_dim,
                                  double kernelStd)
{

   if(input_dim[0]>1024 || input_dim[1]>1024)
      PyErr_SetString(PyExc_RuntimeError,
	     "The convolution function only support image with dimension up to 1024");
   npy_intp index;
   npy_intp pixelNumber = input_dim[0]*input_dim[1];

   double *densityPtr = (double *)calloc(pixelNumber*input_dim[2], sizeof(double));
   for(index=0; index<pixelNumber; ++index)
      densityPtr[index]   = 1.0;
      
   // Compute the Gaussian kernel
   int radius=static_cast<int>(kernelStd*3.0f);
   double kernel[1024], *kernelPtr;
   for(int i=-radius; i<=radius; ++i)
	  kernel[radius+i]=exp(-(double)(i*i)/(2.0*kernelStd*kernelStd)) /
					   (kernelStd*2.506628274631);
   // Allocate some buffer
   double bufferIntensity[1024];
   double bufferDensity[1024];
   // Loop over the x and y dimensions
   int index_offset=1;if(input_dim[2]==2) index_offset=2;
   for(int z=0;z<input_dim[2];++z)
   {
      // ALONG THE X AXIS
      for(int y=0;y<input_dim[1];++y)
      {
         // Extract the current line
         for(int line=0;line<input_dim[0];++line){
            // Numpy: Last index varies the fatest
            index = index_offset*(line*input_dim[1]+y)+z;
            bufferIntensity[line]= input_data[index];
            bufferDensity[line]  = densityPtr[index];
         }
         // Perform the kernel convolution along 1 line
         for(int line=0;line<input_dim[0];++line)
         {
            // Define the kernel boundaries
            int shiftPre = line - radius;
            int shiftPst = line + radius + 1;
            if(shiftPre<0)
            {
               kernelPtr = &kernel[-shiftPre];
               shiftPre=0;
            }
            else kernelPtr = &kernel[0];
            if(shiftPst>input_dim[0])
               shiftPst=input_dim[0];               
            // Set the current values to zero
            double intensitySum=0;
            double densitySum=0;
            // Increment the current value by performing the weighted sum
            for(int k=shiftPre; k<shiftPst; ++k)
            {
               intensitySum +=  *kernelPtr * bufferIntensity[k];
               densitySum   +=  *kernelPtr++ * bufferDensity[k];
            } // k
            // Numpy: Last index varies the fatest
            index = index_offset*(line*input_dim[1]+y)+z;
            input_data[index] = intensitySum;
            densityPtr[index] = densitySum;
         } // line
      } // z
      /* ALONG THE Y AXIS */
      for(int x=0;x<input_dim[0];++x)
      {
         // Extract the current line
         for(int y=0;y<input_dim[1];++y){
            bufferIntensity[y]= input_data[index_offset*(x*input_dim[1]+y)+z];
            bufferDensity[y]  = densityPtr[index_offset*(x*input_dim[1]+y)+z];
         }
         // Perform the kernel convolution along 1 line
         for(int line=0;line<input_dim[1];++line)
         {
            // Define the kernel boundaries
            int shiftPre = line - radius;
            int shiftPst = line + radius + 1;
            if(shiftPre<0)
            {
               kernelPtr = &kernel[-shiftPre];
               shiftPre=0;
            }
            else kernelPtr = &kernel[0];
            if(shiftPst>input_dim[1]) shiftPst=input_dim[1];
            // Set the current values to zero
            double intensitySum=0;
            double densitySum=0;
            // Increment the current value by performing the weighted sum
            for(int k=shiftPre; k<shiftPst; ++k)
            {
               intensitySum +=  *kernelPtr * bufferIntensity[k];
               densitySum   +=  *kernelPtr++ * bufferDensity[k];
            } // k
            input_data[index_offset*(x*input_dim[1]+line)+z] = intensitySum;
            densityPtr[index_offset*(x*input_dim[1]+line)+z] = densitySum;
         } // line
      } // x
   } // z
   // Normalise per timepoint
   for(index=0; index<pixelNumber; ++index)
      input_data[index] = input_data[index]/densityPtr[index];
   free(densityPtr);
}
/* *************************************************************** */
static PyObject *workshop_smoothing(PyObject *self, PyObject *args)
{
  /* Parse the arguments */
  PyObject *input_obj;
  double kernelStd;
  if (!PyArg_ParseTuple(args, "Od", &input_obj, &kernelStd))
       return NULL;
   
  /* Conversion from Object to numpy arrays */
  PyObject *input_np = PyArray_FROM_OTF(input_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  
  /* Check for error */
   if (input_np == NULL) {
       Py_XDECREF(input_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Error when parsing the input data in the gradient function.");
       return NULL;
   }
   if(PyArray_NDIM(input_np)!=2 && PyArray_NDIM(input_np)!=3){
       Py_XDECREF(input_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The smoothing function support 2D and 3D arrays");
       return NULL;
   }
   
   /* Conversion to C pointer */
   double *inputData = static_cast<double *>(PyArray_DATA(input_np));
   npy_intp input_dim[3]={
      (npy_intp)PyArray_DIM(input_np, 0),
      (npy_intp)PyArray_DIM(input_np, 1),
      (npy_intp)PyArray_DIM(input_np, 2)
   };
   if(PyArray_NDIM(input_np)==2) input_dim[2]=1;
   
   /* Create a warped image array */
   double *smoothedData = (double *)malloc(input_dim[0]*input_dim[1]*input_dim[2]*sizeof(double));
   memcpy(smoothedData, inputData, input_dim[0]*input_dim[1]*input_dim[2]*sizeof(double));
   
   /* Perform the convolution */
   inplace_Gaussian_convolution(smoothedData, input_dim, kernelStd);
   
   /* return the smoothed image */
   PyObject* smoothed_np = PyArray_SimpleNewFromData(PyArray_NDIM(input_np), input_dim, NPY_DOUBLE, smoothedData);
   
   /* Clean up. */
   Py_DECREF(input_np);
//    free(smoothedData);

   return Py_BuildValue("O", smoothed_np);
}
/* *************************************************************** */
/* *************************************************************** */
static char jacobian_doc[] =
      "jacobianImage = ipmi_workshop.jacobian(displacementField)";
/* *************************************************************** */
static PyObject *workshop_jacobian(PyObject *self, PyObject *args)
{
  /* Parse the arguments */
  PyObject *dispField_obj;
  if (!PyArg_ParseTuple(args, "O", &dispField_obj))
       return NULL;
   
  /* Conversion from Object to numpy arrays */
  PyObject *dispField_np = PyArray_FROM_OTF(dispField_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  
  /* Check for error */
   if (dispField_np == NULL) {
       Py_XDECREF(dispField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Error when parsing the input data in the jacobian function.");
       return NULL;
   }
   if(PyArray_NDIM(dispField_np)!=3){
       PyErr_SetString(PyExc_RuntimeError,
                       "The deformation field is expected to be a 3D arrays");
       return NULL;
   }
   
   /* Conversion to C pointer */
   double *dispFieldData = static_cast<double *>(PyArray_DATA(dispField_np));
   npy_intp dispField_dim[3]={
      (npy_intp)PyArray_DIM(dispField_np, 0),
      (npy_intp)PyArray_DIM(dispField_np, 1),
      (npy_intp)PyArray_DIM(dispField_np, 2)
   };
   
   /* Create a warped image array */
   double *jacobianData = (double *)calloc(dispField_dim[0]*dispField_dim[1], sizeof(double));
   
   /* Compute the Jacobian Determinant */
   double basis[2]= {1.0,0.0};
   double first[2]= {-1.0,1.0};
   double firstX, firstY, defX, defY;
   double jacobianMatrix[2][2];
   jacobianMatrix[0][0]=jacobianMatrix[0][1]=0.;
   jacobianMatrix[1][0]=jacobianMatrix[1][1]=0.;
   
   int currentIndex, x, y, a, b, index;
   for(x=0; x<dispField_dim[0]; ++x)
   {
      // Numpy: Last index varies the fatest
      currentIndex=x*dispField_dim[1];
      for(y=0; y<dispField_dim[1]; ++y)
      {
         // Sliding is assumed. The Jacobian at the boundary are then replicated
         if(x==dispField_dim[0]-1 || y==dispField_dim[1]-1){
			 if(x==dispField_dim[0]-1) index = currentIndex - dispField_dim[1];
			 if(y==dispField_dim[1]-1) index = currentIndex - 1;
   			 jacobianData[currentIndex] = jacobianData[index];
		 }
         else{
			 jacobianMatrix[0][0]=jacobianMatrix[0][1]=0.;
			 jacobianMatrix[1][0]=jacobianMatrix[1][1]=0.;

			 for(a=0; a<2; ++a)
			 {
                // Numpy: Last index varies the fatest
				index=(x+a)*dispField_dim[1]+y;
				for(b=0; b<2; ++b)
				{
				   // Compute the basis function values
				   firstX=first[a]*basis[b];
				   firstY=basis[a]*first[b];

				   // Get the deformation field values
				   defX = dispFieldData[2*index]+(double)(x+a);
				   defY = dispFieldData[2*index+1]+(double)(y+b);

				   // Symmetric difference to compute the derivatives
				   jacobianMatrix[0][0] += firstX*defX;
				   jacobianMatrix[0][1] += firstY*defX;
				   jacobianMatrix[1][0] += firstX*defY;
				   jacobianMatrix[1][1] += firstY*defY;
				   ++index;
               }
            }//b
         }//a
		 jacobianData[currentIndex] = jacobianMatrix[0][0] * jacobianMatrix[1][1]
		                            - jacobianMatrix[1][0] * jacobianMatrix[0][1];
         currentIndex++;
      }// y 
   }// x
   
   /* Clean up. */
   Py_DECREF(dispField_np);
   
   /* return the warped image */ 
   PyObject* jacobian_np = PyArray_SimpleNewFromData(2, dispField_dim, NPY_DOUBLE, jacobianData);
   //free(jacobianData);

   return Py_BuildValue("O", jacobian_np);
}
/* *************************************************************** */
/* *************************************************************** */
static char composition_doc[] =
      "finalDispField = ipmi_workshop.composition(initialDispField, update)";
/* *************************************************************** */
static PyObject *workshop_composition(PyObject *self, PyObject *args)
{
  /* Parse the arguments */
  PyObject *initialDispField_obj;
  PyObject *updateField_obj;
  if (!PyArg_ParseTuple(args, "OO", &initialDispField_obj, &updateField_obj))
       return NULL;
   
  /* Conversion from Object to numpy arrays */
  PyObject *initialDispField_np = PyArray_FROM_OTF(initialDispField_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  PyObject *updateField_np = PyArray_FROM_OTF(updateField_obj, NPY_DOUBLE, NPY_IN_ARRAY);
  
  /* Check for error */
   if ((initialDispField_np == NULL) || (updateField_np == NULL)) {
       Py_XDECREF(initialDispField_np);
       Py_XDECREF(updateField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Error when parsing the input data in the composition function.");
       return NULL;
   }
   if(PyArray_NDIM(initialDispField_np)!=3){
       Py_XDECREF(initialDispField_np);
       Py_XDECREF(updateField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The initial displacement field is expected to be a 3D arrays");
       return NULL;
   }
   if(PyArray_NDIM(updateField_np)!=3){
       Py_XDECREF(initialDispField_np);
       Py_XDECREF(updateField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "The update field is expected to be a 3D arrays");
       return NULL;
   }
   if(PyArray_DIM(initialDispField_np, 0)!=PyArray_DIM(updateField_np, 0) ||
      PyArray_DIM(initialDispField_np, 1)!=PyArray_DIM(updateField_np, 1) ||
      PyArray_DIM(initialDispField_np, 2)!=PyArray_DIM(updateField_np, 2)){
       Py_XDECREF(initialDispField_np);
       Py_XDECREF(updateField_np);
       PyErr_SetString(PyExc_RuntimeError,
                       "Both input fields are expected to have the same dimension");
       return NULL;
   }
   
   /* Conversion to C pointer */
   double *initialDispData = static_cast<double *>(PyArray_DATA(initialDispField_np));
   double *updateFieldData = static_cast<double *>(PyArray_DATA(updateField_np));
   npy_intp dispField_dim[3]={
      (npy_intp)PyArray_DIM(initialDispField_np, 0),
      (npy_intp)PyArray_DIM(initialDispField_np, 1),
      (npy_intp)PyArray_DIM(initialDispField_np, 2)
   };
   
   /* Create a warped image array */
   double *finalDispFieldData = (double *)malloc(dispField_dim[0]*dispField_dim[1]*dispField_dim[2]*sizeof(double));
   memcpy(finalDispFieldData, initialDispData,
          dispField_dim[0]*dispField_dim[1]*dispField_dim[2]*sizeof(double));
   
   /* Compose the fields */
   double initDefX, initDefY, newDispX, newDispY;
   int pre[2], a, b, aa, bb, temp_index;
   double relX[2], relY[2], dispX, dispY, basis;
   npy_intp index=0;
   for(npy_intp x=0; x<dispField_dim[0]; ++x)
   {
      for(npy_intp y=0; y<dispField_dim[1]; ++y)
      {
         initDefX = initialDispData[2*index]   + (double)x;
         initDefY = initialDispData[2*index+1] + (double)y;

         // Linear interpolation to compute the new displacement
         pre[0]=(int)floor(initDefX);
         pre[1]=(int)floor(initDefY);
         
         relX[1]=initDefX-(double)pre[0];
         relX[0]=1.-relX[1];
         
         relY[1]=initDefY-(double)pre[1];
         relY[0]=1.-relY[1];
         
         newDispX=newDispY=0.;
         for(a=0; a<2; ++a)
         {
            for(b=0; b<2; ++b)
            {
               if((pre[0]+a)>-1 && (pre[0]+a)<dispField_dim[0] &&
                  (pre[1]+b)>-1 && (pre[1]+b)<dispField_dim[1])
               {
                  // Uses the displacement field if voxel is in its space
                  temp_index=(pre[0]+a)*dispField_dim[1]+pre[1]+b;
                  dispX = updateFieldData[2*temp_index];
                  dispY = updateFieldData[2*temp_index+1];
               }
               else
               {
                  /* Cheap sliding "a la Marc" for the workshop */
                  aa=a;bb=b;
                  if(pre[0]+a<0) aa=0;
                  if(pre[1]+b<0) bb=0;
                  if(pre[0]+a>=dispField_dim[0]) aa=dispField_dim[0]-1;
                  if(pre[1]+b>=dispField_dim[1]) bb=dispField_dim[1]-1;
                  temp_index=aa*dispField_dim[1]+bb;
                  dispX = updateFieldData[2*temp_index]; 
                  dispY = updateFieldData[2*temp_index+1];
               }
               basis = relX[a] * relY[b];
               newDispX += dispX * basis;
               newDispY += dispY * basis;
            } // b
         } // a
         finalDispFieldData[2*index]   += newDispX;
         finalDispFieldData[2*index+1] += newDispY;
         index++;
      } // y
   }// x
   
   
   /* return the warped image */ 
   PyObject* finaldispField_np = PyArray_SimpleNewFromData(3, dispField_dim, NPY_DOUBLE, finalDispFieldData);
//    free(finalDispFieldData);

   /* Clean up. */
   Py_DECREF(initialDispField_np);
   Py_DECREF(updateField_np);

   return Py_BuildValue("O", finaldispField_np);
}
/* *************************************************************** */
/* *************************************************************** */
static char module_doc[] =
      "C interfaces for the second IPMI registration workshop";
/* *************************************************************** */
static PyMethodDef allMethods[] = {
   {"resample", workshop_resample, METH_VARARGS, resample_doc},
   {"measure", workshop_measure, METH_VARARGS, measure_doc},
   {"gradient", workshop_gradient, METH_VARARGS, gradient_doc},
   {"smoothing", workshop_smoothing, METH_VARARGS, smoothing_doc},
   {"jacobian", workshop_jacobian, METH_VARARGS, jacobian_doc},
   {"composition", workshop_composition, METH_VARARGS, composition_doc},
   {NULL, NULL, 0, NULL}
};
/* *************************************************************** */
PyMODINIT_FUNC initipmi_workshop(void)
{
    PyObject *m = Py_InitModule3("ipmi_workshop", allMethods, module_doc);
    if (m == NULL)
        return;
    import_array();
}
/* *************************************************************** */
/* *************************************************************** */
