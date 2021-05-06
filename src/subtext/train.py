import os
import sys
import numpy as np
from tqdm import tqdm
import time
import pickle
import argparse

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.utils.data as data_utils

from model import ChunkClassifier


# Device Setting
if torch.cuda.is_available():
    device = torch.device('cuda:0')
else:
    device = torch.device('cpu')
    
    
def load_dataset(path):
    
    data_path = path

    with open(data_path, 'rb') as rr:
        dataset = pickle.load(rr)

    dataset_fin = [data.permute(0, 2, 1) for data in dataset]

    train_x = torch.cat((dataset_fin[0], dataset_fin[1]), dim=0).to(device)
    train_y = torch.cat((torch.ones(len(dataset_fin[0])), torch.zeros(len(dataset_fin[1]))), dim=0).to(device)

    val_x = torch.cat((dataset_fin[2], dataset_fin[3]), dim=0).to(device)
    val_y = torch.cat((torch.ones(len(dataset_fin[2])), torch.zeros(len(dataset_fin[3]))), dim=0).to(device)

    test_x = torch.cat((dataset_fin[4], dataset_fin[5]), dim=0).to(device)
    test_y = torch.cat((torch.ones(len(dataset_fin[4])), torch.zeros(len(dataset_fin[5]))), dim=0).to(device)

    # batch iterator
    batch_size = 256

    trainset = data_utils.TensorDataset(train_x, train_y)
    train_loader = data_utils.DataLoader(trainset, batch_size = batch_size, shuffle = True)

    valset = data_utils.TensorDataset(val_x, val_y)
    val_loader = data_utils.DataLoader(valset, batch_size = len(valset), shuffle = True)

    testset = data_utils.TensorDataset(test_x, test_y)
    test_loader = data_utils.DataLoader(testset, batch_size = len(testset), shuffle = True)
    
    return train_loader, val_loader, test_loader



def trainer(input_model, *dataset):
    
    model = input_model
    
    train_loader, val_loader = dataset[0], dataset[1]
    
    crit = nn.BCEWithLogitsLoss()
    learning_rate = 1e-3

    optimizer = optim.Adam(model.parameters(), lr = learning_rate)

    decayRate = 0.998
    lr_scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer = optimizer, gamma = decayRate)

    train_loss_list = []
    val_loss_list = []
    train_corrects_sum = 0.0
    val_corrects_sum = 0.0

    train_tot_num = train_loader.dataset.__len__()
    val_tot_num = val_loader.dataset.__len__()

    epochs = 10
    for epoch in range(epochs):

        train_loss_sum = 0.0

        for i, train_block in enumerate(train_loader):

            train_X, train_Y = train_block[0], train_block[1]
            optimizer.zero_grad()

            # loss 계산
            train_pred = model(train_X)
            train_loss = crit(train_pred, train_Y)
            train_loss.backward()

            optimizer.step()

            # Prediction Accuracy
            train_pred_label = (train_pred > 0.0).float()
            train_corrects = (train_pred_label == train_Y).sum()
            train_corrects_sum += train_corrects.item()

            train_loss_sum += train_loss

        with torch.no_grad():
            val_loss_sum = 0.0
            for j, val_block in enumerate(val_loader):
                val_X, val_Y = val_block[0], val_block[1]

                val_pred = model(val_X)
                val_loss = crit(val_pred, val_Y)
                val_loss_sum += val_loss

                val_pred_label = (val_pred > 0.0).float()
                val_corrects = (val_pred_label == val_Y).sum()
                val_corrects_sum += val_corrects.item()

        train_loss_sum = 0.0

        print(f"Epoch {epoch+1} done.")
        print(f"Train Accuracy: {train_corrects_sum/train_tot_num:.4f} | Validation Accuracy: {val_corrects_sum/val_tot_num:.4f}\n")

        train_corrects_sum = 0.0
        val_corrects_sum = 0.0

        # learning rate decaying
        lr_scheduler.step()
    
    print("Train Finished.")
    
    return model


def evaluate(input_model, test_loader):
    
    input_model.eval()
    
    test_tot_num = test_loader.dataset.__len__()
    for i, test_block in enumerate(test_loader):
        test_X, test_Y = test_block[0], test_block[1]
        
        test_pred = input_model(test_X)
        test_pred_label = (test_pred > 0.0).float()
        test_corrects = (test_pred_label == test_Y).sum()

        print(f"Test Accuracy: {test_corrects.item()/test_tot_num:.4f}")

        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", default="/home/sks/korea_univ/21_1/TA/team_project/youtube_summarizer/dataset/subtext_dataset/nn_dataset_w3.pkl", type=str)
    parser.add_argument("--save_path", default="./ckpt/")

    args = parser.parse_args()
    
    # Load data / model
    train_loader, val_loader, test_loader = load_dataset(args.data_path)
    
    chunk_model = ChunkClassifier(x_features = 768)
    print(f"Device: {device}")
    chunk_model.to(device)
    
    # Train
    model = trainer(chunk_model, train_loader, val_loader)
    
    # Save
    torch.save(model.state_dict(), args.save_path, _use_new_zipfile_serialization=False)
    print(f"Model Saved at: {args.save_path}")
    
    # Test
    model.eval()
    evaluate(model, test_loader)

        
if __name__=='__main__':
    
    main()
    