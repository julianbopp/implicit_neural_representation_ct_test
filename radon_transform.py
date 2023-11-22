import torch
from torchvision.transforms import v2
import typing
import skimage
import numpy as np
import math
from torch.nn import ConstantPad2d


def radon_transform(image: torch.Tensor, theta=None):
    """Dimension of torch tensor should be 1 x height x width"""
    if theta is None:
        theta = 180

    # Transform image to Grayscale with single channel
    image = v2.Grayscale(1)(image)

    _, height, width = image.shape
    diagonal = math.sqrt(2) * max([height, width])
    pad = [int(math.ceil(diagonal - s)) for s in [height, width]]
    new_center = [(s + p) // 2 for s, p in zip([height, width], pad)]
    old_center = [s // 2 for s in [height, width]]
    pad_before = [nc - oc for oc, nc in zip(old_center, new_center)]
    pad_width = [(pb, p - pb) for pb, p in zip(pad_before, pad)]
    pad = ConstantPad2d(pad_width[0] + pad_width[1], 0)
    image = pad(image)
    sinogram = torch.zeros([1, image.shape[1], theta])

    # Rotate by angle and sum in one dimension
    for i in range(theta):
        rotated_image = v2.RandomRotation((-i, -i), expand=False)(image)
        sum = torch.sum(rotated_image, 1)
        sinogram[0][:, i] = sum

    return sinogram


def batch_radon(t, f, L, theta=None):
    """
    t : tensor of points on radon projection plane
    theta : List [a, b] a start degree, b end degree
    f : function to sample from (support on [-1, 1])
    L : number of sample points on one Line
    """
    pi = 3.14159
    if theta is None:
        theta = np.arange(0, pi, step=pi / 180)
        theta = -theta
    else:
        theta = np.arange(theta[0], theta[1])

    # line equation:
    # (x(t),y(t)) = ( t sin(theta) + z cos(theta), -t cos(theta) + z sin(theta)
    z = torch.linspace(-1.414,1.414, steps=L)

    # sample_grid =
    output = torch.zeros(len(theta), len(t))
    index = 0
    for i in theta:
        i = torch.tensor(i)
        linex = (t * torch.sin(i)).unsqueeze(0) + (z * torch.cos(i)).unsqueeze(1)
        liney = (-t * torch.cos(i)).unsqueeze(0) + (z * torch.sin(i)).unsqueeze(1)

        linex = linex.unsqueeze(0)
        liney = liney.unsqueeze(0)

        line = torch.cat((linex, liney), 0)
        mask = torch.norm(line,dim=0) <= 1
        line = torch.transpose(line, 0, 2)
        # line = torch.transpose(line,0,1)
        f_out, _ = f(line)
        f_out = f_out.squeeze(2) * mask.T
        f_sum = torch.sum(f_out, 1)
        output[index, :] = f_sum

        index = index + 1

    return torch.flip(output, (0,))
