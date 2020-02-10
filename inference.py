import torch
import sys, os.path, glob
import pandas as pd

import model

csv_file = 'millionlive_idol_dict.csv'
weights_file = 'clcnn_50.pkl'
max_length = 110

device = torch.device('cpu')
model = model.CLCNN(max_length=max_length)
model.load_state_dict(torch.load(weights_file, map_location=device))
model.eval()

# Generate an idol dictionary
idol_data_frame = pd.read_csv(csv_file)
idol_df = idol_data_frame.set_index('id')
idol_dict = idol_df['idol_name'].to_dict()

def string_to_codepoint(_str, max_length=max_length):
    _encoded_str = [ord(_x) for _x in str(_str).strip()]
    _encoded_str = _encoded_str[:max_length]
    _str_len = len(str(_str)) # String length
    if _str_len < max_length: # If string length is less than a num of max_length, do zero padding
        _encoded_str += ([0] * (max_length - _str_len))
    
    return _encoded_str

def predict(model, input_str):
    model = model.eval()
    with torch.no_grad():
        output = model(input_str)
    
    return output

def inference(inputs):
    encoded_str = torch.LongTensor(string_to_codepoint(inputs)).unsqueeze(0).to(device)
    result = predict(model, encoded_str)
    res_df = pd.DataFrame(result.cpu().numpy())
    res_df.rename(columns=idol_dict, index={0: 'likelihood'}, inplace=True)
    res_df = res_df.T.sort_values('likelihood', ascending=False)

    #print(res_df['likelihood'][:10])
    #print(res_df['likelihood'][:10].to_dict())

    return res_df['likelihood'][:10].to_dict()

# For debug
#inference(input('Type:'))