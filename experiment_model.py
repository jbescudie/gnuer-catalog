"""here we centralize the schema describing our experiments.

first we define everything considered a hyperparmeters.
then we define the data model for logging results.


# the term HPARAMS here is confusing
#          e.g. using RESULTS would be easier to read here
#          but actually TYPE would have been more generic from the beginning


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

"""

from shared import hparams    # if this dependency bothers &you, please contact the author. 


## hyperparameters
class RANDOM_HPARAMS(hparams.HPARAMS):
    random: str     = "random.Normal"
    mean: float     = 0.
    std: float      = 1.

class DATASET_HPARAMS(hparams.HPARAMS):
    dataset: str    = "mnist.MNIST"
    split: str      = "train"
    sample_shape:int= (28,28)
    target_shape:int= (10,)
    size: int       = 50_000
    
class DATALOADER_HPARAMS(hparams.HPARAMS):
    batch_size: int = 100
    shuffler: RANDOM_HPARAMS = RANDOM_HPARAMS("random.Uniform")

class MODEL_HPARAMS(hparams.HPARAMS):
    model: str      = "model.MLP"
    layers: int     = (10,10)
    activation: str = "activation.ReLU"
    
class LOSS_HPARAMS(hparams.HPARAMS):
    loss: str       = "loss.MSE"

class OPTIMIZER_HPARAMS(hparams.HPARAMS):
    optimizer: str  = "SGD"
    lr: float       = 0.001
    init_w: RANDOM_HPARAMS = RANDOM_HPARAMS()
    init_b: RANDOM_HPARAMS = RANDOM_HPARAMS()

    
# note how this class is a composite of the other types. An experiment can be fully described by this class.
class EXPERIMENT_HPARAMS(hparams.HPARAMS):
    seed: int       = 777
    train_dataset: DATASET_HPARAMS = DATASET_HPARAMS(split="train")
    val_dataset:   DATASET_HPARAMS = DATASET_HPARAMS(split="val"  , size=5_000)
    test_dataset:  DATASET_HPARAMS = DATASET_HPARAMS(split="test" , size=5_000)
    dataloader: DATALOADER_HPARAMS = DATALOADER_HPARAMS()
    model:      MODEL_HPARAMS      = MODEL_HPARAMS()
    loss:       LOSS_HPARAMS       = LOSS_HPARAMS()
    optimizer:  OPTIMIZER_HPARAMS  = OPTIMIZER_HPARAMS()


## artefacts (produced by running the experiments)
class IterationLog_HPARAMS(hparams.HPARAMS):
    iteration: int
    loss: float

class ExperimentRef_HPARAMS(hparams.HPARAMS):
    experiment_hash_hex: str
    split: str

class RunLog_HPARAMS(hparams.HPARAMS):
    experiment: ExperimentRef_HPARAMS
    log: IterationLog_HPARAMS

class Checkpoint_HPARAMS(hparams.HPARAMS):
    experiment: ExperimentRef_HPARAMS
    iteration: int
    checkpoint: bytes 

