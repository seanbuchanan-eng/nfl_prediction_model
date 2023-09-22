import torch
from torch import nn


class V1NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(5, 5),
            nn.ReLU(),
            nn.Linear(5, 1),
        )

    def forward(self, x):
        output = self.linear_relu_stack(x)
        return output

def v1():
    model = V1NeuralNetwork()
    model.load_state_dict(torch.load('models/v1.pth'))
    model.eval()
    return model