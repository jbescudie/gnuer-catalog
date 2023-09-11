"""Training code for the demonstration experiment.


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.
"""
import experiment_model          # *your* experiment
from env import default_catalog  # access to catalog in *your* environment
import dummydumb_framework       # *your* favorite ML framework :)
import io


def train(experiment_hparams_hash):
    """run training for an experiment given by a set of values in the experiment_model.

    note the pattern for a task:
       1.  load from ROCatalog
       2. *do wome work
       3.  write to Catalog
    """
    #### 1. load from catalog
    experiment_hparams_catalog = default_catalog(experiment_model.EXPERIMENT_HPARAMS)
    experiment_hparams = experiment_hparams_catalog.get(experiment_hparams_hash)

    #### 2. the following parts will highly depend on the libraries/frameworks used
    # initialize
    train_dataset = dummydumb_framework.Dataset(
        experiment_hparams.train_dataset.dataset,
        experiment_hparams.train_dataset.split
    )
    dataloader    = dummydumb_framework.Dataloader(
        train_dataset,
        experiment_hparams.dataloader
    )
    model         = dummydumb_framework.Model(experiment_hparams.model)
    loss          = dummydumb_framework.Loss(experiment_hparams.loss)
    optimizer     = dummydumb_framework.Optimizer(experiment_hparams.optimizer, model=model)
    
    optimizer.init()
    
    # train loop
    train_log = []
    for iteration, (samples, targets) in enumerate(dataloader):
        outputs    = model(samples)
        train_loss = loss(targets, outputs)
        train_loss.backward()
        optimizer.step()

        # note how artefacts are part of the experiment_model
        iteration_log = experiment_model.IterationLog_HPARAMS(iteration, loss=train_loss.item())
        train_log += [iteration_log]

        
    #### 3. save train_log and trained model to their catalogs
    experiment_ref = experiment_model.ExperimentRef_HPARAMS(
        experiment_hparams_hash.hex(),
        "train"
    )

    # run_log
    run_log_catalog = default_catalog(experiment_model.RunLog_HPARAMS, write=True)
    run_log = experiment_model.RunLog_HPARAMS(
        experiment_ref,
        # note1: this part converts our list to 'columns' compatible with RunLog_HPARAMS
        experiment_model.IterationLog_HPARAMS(
            # note2: and tuple are immutable :)
            iteration=tuple(iteration_log.iteration for iteration_log in train_log),
            loss     =tuple(iteration_log.loss      for iteration_log in train_log),
        )
    )
    run_log_hash = run_log_catalog.add(run_log)

    # checkpoint
    checkpoint_catalog = default_catalog(experiment_model.Checkpoint_HPARAMS, write=True)
    buffer = io.BytesIO()
    model.save_checkpoint(buffer)
    # note3: checkpoints are our metadata, and then just bytes that the framework knows how to handle 
    checkpoint = experiment_model.Checkpoint_HPARAMS(
        experiment_ref,
        iteration,
        checkpoint=buffer.getvalue()
    )
    checkpoint_hash = checkpoint_catalog.add(checkpoint)

    print(f"training for experiment {experiment_hparams_hash.hex()} done. Wrote run_log {run_log_hash.hex()} and saved checkpoint {checkpoint_hash.hex()}")
    

if __name__ == "__main__":
    # CLI utility
    try:
        import sys
        experiment_hparams_hash = bytes.fromhex(sys.argv[1])
        train(experiment_hparams_hash)
    except Exception as e:
        print(f"""usage: python3 run.py <experiment_hparams_hash>

        called with argv: {sys.argv}
        got exception: {e}
        """)
