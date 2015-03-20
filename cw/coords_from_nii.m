function [xs ys zs] = coords_from_nii(nii)
%function to get the voxel coordinates for the x, y, and z axis from a nii
%structure as returned by load_untouch_nii

%NOTE - does not work if rotations are included in the header

%if sform is set gets voxel coords from sform, else gets them from qform

if nii.hdr.hist.sform_code == 1
    %use sform
    
    %check for rotations
    if any(nii.hdr.hist.srow_x(2:3) > 0) || any(nii.hdr.hist.srow_y([1 3]) > 0) || any(nii.hdr.hist.srow_z(1:2) > 0)
        warning('Rotation included in sform. Rotations have not yet been implemented in this code and will be ignored!');
    end
    xs = (0:nii.hdr.dime.dim(2)-1)*nii.hdr.hist.srow_x(1)+nii.hdr.hist.srow_x(4);
    ys = (0:nii.hdr.dime.dim(3)-1)*nii.hdr.hist.srow_y(2)+nii.hdr.hist.srow_y(4);
    zs = (0:nii.hdr.dime.dim(4)-1)*nii.hdr.hist.srow_z(3)+nii.hdr.hist.srow_z(4);
elseif nii.hdr.hist.sform_code == 0
    %check for rotations
    if nii.hdr.hist.quatern_b ~= 0 || nii.hdr.hist.quatern_c ~= 0 || nii.hdr.hist.quatern_d ~= 0
        warning('Rotation included in qform. Rotations have not yet been implemented in this code and will be ignored!');
    end
    xs = (0:nii.hdr.dime.dim(2)-1)*nii.hdr.dime.pixdim(2)+nii.hdr.hist.qoffset_x;
    ys = (0:nii.hdr.dime.dim(3)-1)*nii.hdr.dime.pixdim(3)+nii.hdr.hist.qoffset_y;
    zs = (0:nii.hdr.dime.dim(4)-1)*nii.hdr.dime.pixdim(4)+nii.hdr.hist.qoffset_z;
else
    error(['unknown sform code: ' num2str(nii.hdr.dime.sform_code)]);
end