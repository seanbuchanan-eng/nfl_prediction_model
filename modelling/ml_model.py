
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader, random_split

conn = sqlite3.connect('../db.sqlite')
cur = conn.cursor()

# get data by joining game and mldata tables
games = cur.execute("""
                    SELECT Games.home_points, Games.away_points, MLData.*
                    FROM Games JOIN MLData on Games.id = MLData.game_id""").fetchall()
conn.close()

# normalize input data between [0,1]
games_df = pd.DataFrame(games)
games_norm = games_df.drop(games_df.columns[[0,1,2,3]], axis=1)
games_norm = (games_norm-games_norm.min())/(games_norm.max()-games_norm.min())
games_final = pd.concat((games_df.iloc[:,:2], games_norm), axis=1)

# set labels to the spread for the home team 

# set input to the row from mldata minus id and game_id

# normalize data
# convert to tensor using torch.tensor(tuple)
# pytorch basics tutorial are helpful here.
class GameDataset(Dataset):
    def __init__(self, games, transform=None, target_transform=None):
        self.data = games
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, index):
        home_points = self.data.iloc[index, 0:1].to_numpy()
        away_points = self.data.iloc[index, 1:2].to_numpy()
        label = home_points - away_points
        model_input = self.data.iloc[index, 2:].to_numpy()
        if self.transform:
            model_input = self.transform(model_input, dtype=torch.float32)
        if self.target_transform:
            label = self.target_transform(label, dtype=torch.float32)
        return model_input, label
    
dataset = GameDataset(games_final, torch.tensor, torch.tensor)
gen1 = torch.Generator().manual_seed(42)
train, test = random_split(dataset, [0.7, 0.3], generator=gen1)

train_dataloader = DataLoader(train, batch_size=64, shuffle=True)
test_dataloader = DataLoader(test, batch_size=64, shuffle=True)


# select device
device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)
print(f"Using {device} device")

# build the network
class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(227, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
        )

    def forward(self, x):
        output = self.linear_relu_stack(x)
        return output
    
def check_model():

    train_features, train_labels = next(iter(train_dataloader))
    print(f"Feature batch shape: {train_features.size()}")
    print(f"Labels batch shape: {train_labels.size()}")
    input_data = train_features[0:1]
    label = train_labels[0]
    print(f"input_data: {input_data}")
    print(f"Label: {label}")

    model = NeuralNetwork().to(device)
    print(model)

    y_pred = model(input_data)
    print(f"Predicted class: {y_pred}")

def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)

    model.train()
    for batch, (X, y) in enumerate(dataloader):
        pred = model(X)
        loss = loss_fn(pred, y)

        # backpropogate
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        if batch % 20 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

def test_loop(dataloader, model, loss_fn):

    model.eval()
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0

    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")


def main():
    learning_rate = 1e-3
    batch_size = 64
    epochs = 50

    model = NeuralNetwork()
    loss_fn = nn.L1Loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    for t in range(epochs):
        # print(f"Epoch {t+1}\n-------------------------------")
        train_loop(train_dataloader, model, loss_fn, optimizer)
        # test_loop(test_dataloader, model, loss_fn)
    print("Done!")

    torch.save(model.state_dict(), 'models/test_run1.pth')

main()