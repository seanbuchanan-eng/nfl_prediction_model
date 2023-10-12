"""
This module contains the saved models developed for the 
AI portion of the website.
"""

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
    """
    The version 1 neural network. Takes point_diff_diff,
    elo_diff_diff, yard_diff_diff, turnover_diff_diff, 
    and elo_spread as inputs.

    Returns
    -------
    torch model
        Version 1 neural network with trained parameter values.
    """
    model = V1NeuralNetwork()
    model.load_state_dict(torch.load('models/v1.pth'))
    model.eval()
    return model