"""here we centralizes the initial conditions for our experiments.


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.
"""

import experiment_model          # *your* experiment
from env import default_catalog  # access to catalog in *your* environment


def populate():
    """defines experiment_hparams and add them to their catalog."""
    experiment_hparams_catalog = default_catalog(experiment_model.EXPERIMENT_HPARAMS, write=True)
    # add some variations to the default experiment_hparams
    for seed in range(777, 777 + 7):
        experiment_hparams = experiment_model.EXPERIMENT_HPARAMS(seed=seed)
        experiment_hparams_hash = experiment_hparams_catalog.add(experiment_hparams)
    
def print_catalog():
    """utility that list the experiment_hparams hashes and print to stdout."""
    experiment_hparams_catalog = default_catalog(experiment_model.EXPERIMENT_HPARAMS)
    for experiment_hparams_hash in experiment_hparams_catalog.iter():
        print(experiment_hparams_hash.hex())

def print_experiment(experiment_hparams_hash):
    experiment_hparams_catalog = default_catalog(experiment_model.EXPERIMENT_HPARAMS)
    experiment_hparams = experiment_hparams_catalog.get(experiment_hparams_hash)
    import shared.hparams
    print(shared.hparams.pretty(experiment_hparams))
    
        
if __name__ == "__main__":
    # CLI
    try:
        import sys
        if not sys.argv[1:]:
            populate()
            print_catalog()
        else:
            experiment_hparams_hash = bytes.fromhex(sys.argv[1])
            print_experiment(experiment_hparams_hash)
    except Exception as e:
        print(f"""usage: python3 populate.py [<experiment_hparams_hash>]

        With no argument: write experiments to the experiment_hparams catalog and print the list.

        <experiment_hparams_hash>: if provided, pretty print the details of an experiment_hparams.
        
        ====
        called with argv: {sys.argv}
        got exception: {e}
        """)

