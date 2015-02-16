#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import SimpleITK as sitk

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--img", required=True, help="Input image")
parser.add_argument("-o", "--out", required=True, help="Result segmentation")


args = parser.parse_args()
infile=args.img
outfile=args.out

#Your code goes here
input=sitk.ReadImage(infile)
filter = sitk.OtsuThresholdImageFilter()
filter.SetInsideValue(0)
filter.SetOutsideValue(255)

binimg = filter.Execute(input)


eroFilter = sitk.BinaryErodeImageFilter()
eroFilter.SetKernelRadius(50).SetForegroundValue(100)
erodedImg = eroFilter.Execute(binimg)

sitk.WriteImage(erodedImg, "eroded.png")

dilFilter = sitk.BinaryDilateImageFilter()
dilFilter.SetKernelRadius(5).SetForegroundValue(1)
dilatedImg = dilFilter.Execute(erodedImg)


sitk.WriteImage(dilatedImg, outfile)
