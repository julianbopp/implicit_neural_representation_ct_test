import h5py
import torch
import torch.nn.functional as F
from torch import from_numpy
from torch.utils.data import Dataset
from torchvision import transforms


class LodopabImage(Dataset):
    """Loads a single image from the LoDoPaB-CT dataset and makes pixel batching possible"""

    def __init__(self, resolution, set="ground_truth_train", pos1="000", pos2=0):
        self.resolution = resolution
        self.image_path = f"../dataset/{set}/{set}_{pos1}.hdf5"
        self.image = from_numpy(self.read_hdf5(self.image_path))[pos2, :, :].unsqueeze(
            0
        )

        self.transform = transforms.Compose(
            [
                transforms.Resize(resolution),
                # transforms.Normalize(torch.Tensor([1]), torch.Tensor([1]))
            ]
        )

        self.image = self.transform(self.image)

        self.coords = self.get_mgrid(resolution, dim=2)
        self.pixels = self.image.permute(1, 2, 0).view(-1, 1)

    def __len__(self):
        return self.image.shape[1] * self.image.shape[2]

    def __getitem__(self, idx):
        return self.coords[idx, :], self.pixels[idx]

    def read_hdf5(self, path):
        file = h5py.File(path, "r")
        with file as f:
            group_key = list(f.keys())[0]
            data = f[group_key][()]
        file.close()
        return data

    def get_mgrid(self, sidelen, dim=2):
        """Generates a flattened grid of (x,y,...) coordinates in a range of -1 to 1.
        sidelen: int
        dim: int"""
        tensors = tuple(dim * [torch.linspace(-1, 1, steps=sidelen)])
        mgrid = torch.stack(torch.meshgrid(*tensors), dim=-1)
        mgrid = mgrid.reshape(-1, dim)
        return mgrid

    def get_2d_np(self):
        return self.image.detach().numpy()[0, :, :]

    def sample_image(self, grid, image):
        """
        Sample image with coordinates in [-1,1]^2 using bilinear interpolation
        :param grid: meshgrid with shape (1,X,Y,2)
        :param image: shape (X,Y)
        :return: pixel value at coordinates
        """
        reshaped_image = image.unsqueeze(0).unsqueeze(0)
        sampled_image = F.grid_sample(
            reshaped_image,
            grid,
            mode="bilinear",
            padding_mode="zeros",
            align_corners=True,
        )

        return sampled_image
