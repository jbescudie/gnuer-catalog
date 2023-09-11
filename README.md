# Demonstration of using an object store as an experiment artefacts management.


By using a simple type system, we can quickly yet completely define a schema representing the domain of our experiment.
This can be achieved by adding serialization/deserialization and a storage mechanism on top of the type system.

The following describes the demo project of a fictitious ML experiment.


## Code organization

`experiment_model.py`: we define the schema, that is all objects that will contain values relevant to the experiments.

`env.py`: seperating settings specific to this system (e.g. filesystem paths) allows the rest of the code to be free of settings unrelated to the experiments, while still allowing customization.

`populate.py`: defines all the variations of the experiment model to be tested (here we do variation only on one a parameter: `seed`). This task write to hyperparameters catalog.

`train.py`: contains the training code. This task loads an experiment from the catalog, run the exepriment, save results to other catalogs.

Other tasks would then leverage the results catalog for analysis, plotting...

In this pure python implementation, the supporting modules are placed in the `shared` python package and are designed to be reusable across experiments. `dummydumb_framework.py` is a mock for a ML framework and would typically be also a separate package.



## Running all experiments.

Check how the folder $CATALOG_PATH evolves at every step.

```
# folder of your choice on your system (see env.py)
export CATALOG_PATH=./demo-experiment-catalogs

# add hyperparameters to the experiment catalog 
python populate.py

# print one experiment
python populate.py 8ddc7cacd40674e9fcb8f43d2efcfd7f

# run one experiment
python train.py 8ddc7cacd40674e9fcb8f43d2efcfd7f

# run all experiments
python populate.py | xargs -I % python train.py %


```




