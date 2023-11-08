import torch
from torch.utils.data import DataLoader
from torchmetrics.audio import SignalNoiseRatio

from radon_transform import radon_transform

from skimage.transform import radon, iradon

import matplotlib.pyplot as plt

import numpy as np

from siren import Siren
from lodopabimage import LodopabImage
CUDA = False

resolution = 256
img_siren = Siren(in_features=2, out_features=1, hidden_features=resolution,
                  hidden_layers=3, outermost_linear=True)

if CUDA:
    img_siren.load_state_dict(torch.load('img_siren.pt'))
else:
    img_siren.load_state_dict(torch.load('img_siren.pt', map_location=torch.device('cpu')))
img_siren.eval()

dataset = LodopabImage(resolution)
dataloader = DataLoader(dataset, batch_size=dataset.__len__())

model_input, ground_truth = next(iter(dataloader))

ground_truth = ground_truth.view(1,resolution,-1)
ground_truth_image = ground_truth.reshape(resolution,resolution).detach().numpy()
ground_truth_radon = radon(ground_truth_image, np.arange(180), circle=False)
ground_truth = torch.from_numpy(ground_truth_radon).unsqueeze(0)

model_output, coords = img_siren(model_input)
model_output = radon_transform(model_output.view(1, resolution, resolution), 180)

fig, axes = plt.subplots(2, 2, figsize=(18, 6))
axes[0][0].set_title("SIREN Radon")
axes[0][0].imshow(model_output.cpu().view(-1, 180).detach().numpy())

axes[0][1].set_title("SIREN Inv Radon")
axes[0][1].imshow(iradon(model_output.cpu().view(-1, 180).detach().numpy(), circle=False))

axes[1][0].set_title("Ground Truth Radon")
axes[1][0].imshow(ground_truth_radon)

axes[1][1].set_title("Ground Truth Inverse Radon")
axes[1][1].imshow(iradon(ground_truth_radon, circle=False))


snr = SignalNoiseRatio()
print(snr(torch.from_numpy(iradon(model_output.cpu().view(-1, 180).detach().numpy(), circle=False)), torch.from_numpy(iradon(ground_truth_radon, circle=False))))

plt.show()
