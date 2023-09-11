'''this module should centralize calls specific to this environment

seperating settings specific to this system (e.g. filesystem paths) allows the rest of the code to be free of settings unrelated to the experiments, while still allowing customization.

here we do that by:
 - encapsulating calls to environment variables
 - having a consitent pattern for using catalogs

this also allows migration to another mechanism than environnment variable, such as a configuration file for example, without having to change the code related to experiments.
'''

import shared.catalog
import os, pathlib     


def default_catalog(HPARAMS: shared.hparams.HPARAMS, write=False) -> shared.catalog.Catalog:
    """utility to standardize a catalog for a given HPARAMS type."""
    try:
        CATALOG_PATH = pathlib.Path(os.environ["CATALOG_PATH"])
    except KeyError:
        raise Exception("CATALOG_PATH is not defined.\nHint: set CATALOG_PATH environment variable to the catalog directory of your choice.")

    Catalog = shared.catalog.Catalog if write else shared.catalog.ROCatalog
    
    return Catalog(
        path        = CATALOG_PATH / HPARAMS.__name__,
        item_suffix = f".{HPARAMS.__name__.lower()}",
        Type        = HPARAMS,
        salt        = b""
    )
