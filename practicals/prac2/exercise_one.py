#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import SimpleITK as sitk

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--img", required=True, help="Input image")
parser.add_argument("-o", "--out", required=True, help="Result segmentation")
parser.add_argument("-u", "--up", required=True, help="Upper threshold", type=float)
parser.add_argument("-l", "--low", required=True, help="Lower threshold", type=float)

args = parser.parse_args()
infile=args.img
outfile=args.out
low=args.low
up=args.up

#Your code goes here

input = sitk.ReadImage(infile)
output = sitk.BinaryThreshold(input, low, up, 0, 255)
sitk.WriteImage(output, outfile)
