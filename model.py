import torch
import torch.nn as nn

class CLCNN(nn.Module):
    def __init__(self, max_length, embed_size=512, filter_sizes=(2, 3, 4, 5), filter_num=1500):
        super(CLCNN, self).__init__() # Call a method of super class.
        self.filter_sizes = filter_sizes
        self.filter_num = filter_num
        
        self.emb = nn.Embedding(0xffff, embed_size, padding_idx=0) # Get only kinds of three-byte characters of UTF-8
        
        # Convolution layer
        self.conv0 = nn.Sequential(
            nn.Conv2d(1, filter_num, (filter_sizes[0], embed_size)),
            nn.ReLU(),
            nn.MaxPool2d((max_length - filter_sizes[0] + 1, 1))
        )
        
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, filter_num, (filter_sizes[1], embed_size)),
            nn.ReLU(),
            nn.MaxPool2d((max_length - filter_sizes[1] + 1, 1))
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(1, filter_num, (filter_sizes[2], embed_size)),
            nn.ReLU(),
            nn.MaxPool2d((max_length - filter_sizes[2] + 1, 1))
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv2d(1, filter_num, (filter_sizes[3], embed_size)),
            nn.ReLU(),
            nn.MaxPool2d((max_length - filter_sizes[3] + 1, 1))
        )
        
        # Fully connected layer
        self.dense = nn.Sequential(
            nn.Linear(filter_num * len(self.filter_sizes), 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 50),
            nn.Softmax(dim=1)
        )
    
    def forward(self, x):
        #print('input:', x.size())
        out = self.emb(x)
        #print('emb:', out.size())
        emb_out = out.unsqueeze(1) # Insert a dimension
        #print('emb_ex:', emb_out.size())

        concat_out = torch.cat((self.conv0(emb_out), self.conv1(emb_out), self.conv2(emb_out), self.conv3(emb_out)), 1)
        #print('concatnated:', concat_out.size())
        out = concat_out.view(-1, self.filter_num * len(self.filter_sizes))
        #print('flatten:', out.size())
        out = self.dense(out)
        #print('output:', out.size())
        
        return out
