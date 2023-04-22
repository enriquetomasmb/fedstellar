from typing import List, Dict
import lightning as pl
import torch
from torch.nn import functional as F
from torchmetrics.classification import MulticlassAccuracy, MulticlassRecall, MulticlassPrecision, MulticlassF1Score, MulticlassConfusionMatrix

EPOCH_OUTPUT = List[Dict[str, torch.Tensor]]

###############################
#    Multilayer Perceptron    #
###############################


class MLP(pl.LightningModule):
    """
    Multilayer Perceptron (MLP) to solve MNIST with PyTorch Lightning.
    """

    def __init__(
            self,
            metric=[MulticlassAccuracy, MulticlassPrecision, MulticlassRecall, MulticlassF1Score, MulticlassConfusionMatrix],
            out_channels=10,
            lr_rate=0.001,
            seed=None
    ):  # low lr to avoid overfitting

        # Set seed for reproducibility iniciialization
        if seed is not None:
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)

        super().__init__()
        self.lr_rate = lr_rate
        self.l1 = torch.nn.Linear(28 * 28, 256)
        self.l2 = torch.nn.Linear(256, 128)
        self.l3 = torch.nn.Linear(128, out_channels)

        self.training_step_outputs = []
        self.training_step_real = []

        self.validation_step_outputs = []
        self.validation_step_real = []

        self.test_step_outputs = []
        self.test_step_real = []
        self.metric=[]
        if type(metric) is list:
            for m in metric:
                self.metric.append(m(num_classes=10))
        else:
            self.metric = metric(num_classes=10)

    def forward(self, x):
        """ """
        batch_size, channels, width, height = x.size()

        # (b, 1, 28, 28) -> (b, 1*28*28)
        x = x.view(batch_size, -1)
        x = self.l1(x)
        x = torch.relu(x)
        x = self.l2(x)
        x = torch.relu(x)
        x = self.l3(x)
        x = torch.log_softmax(x, dim=1)
        return x

    def configure_optimizers(self):
        """ """
        return torch.optim.Adam(self.parameters(), lr=self.lr_rate)
    
    def log_metrics(self, phase, y_pred, y, print_cm = True):
        if type(self.metric) is list:
            for m in self.metric:
                if (isinstance(m, MulticlassConfusionMatrix)):
                    if print_cm:
                        print(phase+"/CM\n", m(y_pred, y))
                    else:
                        pass
                else:
                    self.log(phase+"/"+m.__class__.__name__.replace("Multiclass", ""), m(y_pred, y))
        else:
            self.log(phase+"/"+self.metric.__class__.__name__.replace("Multiclass", ""), self.metric(y_pred, y))

    def training_step(self, batch, batch_id):
        """ """
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        out = torch.argmax(logits, dim=1)
        self.training_step_outputs.append(out)
        self.training_step_real.append(y)
        
        self.log("Train/Loss", loss, prog_bar=True)
        self.log_metrics("Train", out, y, print_cm=False)
        
        return loss

    def on_train_epoch_end(self):
        out = torch.cat(self.training_step_outputs)
        y = torch.cat(self.training_step_real)
        self.log_metrics("TrainEpoch", out, y, print_cm=True)

        self.training_step_outputs.clear()  # free memory
        self.training_step_real.clear()

    def validation_step(self, batch, batch_idx):
        """ """
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        out = torch.argmax(logits, dim=1)
        self.validation_step_outputs.append(out)
        self.validation_step_real.append(y)
        self.log("Validation/Loss", loss, prog_bar=True)
        self.log_metrics("Validation", out, y, print_cm=False)
        return loss
    
    def on_validation_epoch_end(self):
        out = torch.cat(self.validation_step_outputs)
        y = torch.cat(self.validation_step_real)
        self.log_metrics("ValidationEpoch", out, y, print_cm=True)

        self.validation_step_outputs.clear()  # free memory
        self.validation_step_real.clear()

    def test_step(self, batch, batch_idx):
        """ """
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        out = torch.argmax(logits, dim=1)
        self.test_step_outputs.append(out)
        self.test_step_real.append(y)
        self.log("Test/Loss", loss, prog_bar=True)
        self.log_metrics("Test", out, y, print_cm=False)
        return loss

    def on_test_epoch_end(self):
        out = torch.cat(self.test_step_outputs)
        y = torch.cat(self.test_step_real)
        self.log_metrics("TestEpoch", out, y, print_cm=True)

        self.test_step_outputs.clear()  # free memory
        self.test_step_real.clear()
