import torch
import torch.nn as nn
import torchvision.models as models
from torch.nn.utils.rnn import pack_padded_sequence

# build the encoder

class Encoder(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        
        """
        We will be using a pretrained inception 3 model that is available within the pytorch frame work and replace 
        top fc layer. 
        
        V3 = the pretrained inception
        modules = all the layers of V3 except for the last layer of V3
        """
        
        V3 = models.inception_v3(pretrained=True)
        modules = list(V3.children())[:-1]      # delete the last fc layer.
        self.V3 = nn.Sequential(*modules)
        self.linear = nn.Linear(resnet.fc.in_features, embed_size)
        self.bn = nn.BatchNorm1d(embed_size, momentum=0.01)
        
    def forward(self, images):
        """
        To be able to prevent over fitting, we want the retain the weights on every layer of the V3 except.
        """
        #do not train V3.
        with torch.no_grad():
            features = self.V3(images)
        
        # only train the linear layer that gives us the embedding.
        features = features.reshape(features.size(0), -1)
        features = self.bn(self.linear(features))
        return features


class DecoderRNN(nn.Module):
    def __init__(self, vocab_size, num_layers=1, max_seq_length=20, embed_size=512, hidden_size=200):
        """
        Set the hyper-parameters and build the layers.
        --------------
        Hyper-Parameters :
        embed_size = 512 (default)
        hidden_size = 512 (default)
        vocab_size = depends on dataset
        num_layers = 1 (default)
        max_seq_length = 20 (default)
        -------------- 
        """
        super(DecoderRNN, self).__init__()
        self.embed = nn.Embedding(vocab_size, embed_size)
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_size, vocab_size)
        self.max_seg_length = max_seq_length
        
    def forward(self, features, captions, lengths):
        """
        Use the Decoder 
        """
        embeddings = self.embed(captions)
        embeddings = torch.cat((features.unsqueeze(1), embeddings), 1)
        packed = pack_padded_sequence(embeddings, lengths, batch_first=True) 
        hiddens, _ = self.lstm(packed)
        outputs = self.linear(hiddens[0])
        return outputs
    
    def greedy_sample(self, features, states=None):
        """
        Generate captions for given image features using greedy search.
        """
        sampled_ids = []
        inputs = features.unsqueeze(1)
        for i in range(self.max_seg_length):
            hiddens, states = self.lstm(inputs, states)          # hiddens: (batch_size, 1, hidden_size)
            outputs = self.linear(hiddens.squeeze(1))            # outputs:  (batch_size, vocab_size)
            _, predicted = outputs.max(1)                        # predicted: (batch_size)
            sampled_ids.append(predicted)
            inputs = self.embed(predicted)                       # inputs: (batch_size, embed_size)
            inputs = inputs.unsqueeze(1)                         # inputs: (batch_size, 1, embed_size)
        sampled_ids = torch.stack(sampled_ids, 1)                # sampled_ids: (batch_size, max_seq_length)
        return sampled_ids

    def beam_search_sample(self, features, states=None):
        """
        Generate captions for given image features using beam search algorithm.
        """
        return pass
    
    def diverse_beam_search(self,features, states=None):
        """
        Generate captions for given image features using diverse beam search.
        """
        return pass
