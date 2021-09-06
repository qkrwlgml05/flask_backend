class LSTM(nn.Module):
    
    def __init__(self, input_dim, hidden_dim, num_layers, batch_size, dropout, use_bn, device):
        super(LSTM, self).__init__()
        self.input_dim = input_dim 
        self.hidden_dim = hidden_dim
        self.output_dim = 1
        self.num_layers = num_layers

        self.batch_size = batch_size
        self.dropout = dropout
        self.use_bn = use_bn 
        
        self.lstm = nn.LSTM(self.input_dim, self.hidden_dim, self.num_layers)
        self.regressor = self.make_regressor()
        
        self.device = device
        
    def init_hidden(self, batch_size):
        return (torch.zeros(self.num_layers, batch_size, self.hidden_dim).to(self.device),
                torch.zeros(self.num_layers, batch_size, self.hidden_dim).to(self.device))
    
    def make_regressor(self):
        layers = []
        if self.use_bn:
            layers.append(nn.BatchNorm1d(self.hidden_dim))
        layers.append(nn.Dropout(self.dropout))
        
        layers.append(nn.Linear(self.hidden_dim, self.hidden_dim // 2))
        layers.append(nn.ReLU())
        layers.append(nn.Linear(self.hidden_dim // 2, self.output_dim))
        #layers.append(nn.Sigmoid()) # 지운 이유 : BCEwithLogitLoss에 Sigmoid가 붙어 있기 때문 (없으면 안돌아감)
        regressor = nn.Sequential(*layers)
        return regressor
    
    def forward(self, x):
        hidden = self.init_hidden(x.size(1))
        
        lstm_out, self.hidden = self.lstm(x, hidden)
        y_pred = self.regressor(lstm_out[-1].view(x.size(1), -1))
#         t = Variable(torch.Tensor([0.5]))  # threshold
#         out = (y_pred > t).float() * 1
        return y_pred
