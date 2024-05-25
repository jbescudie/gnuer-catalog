"""Catalog module.


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.
"""
import typing
import pathlib, fcntl
from shared import deser, hash #, experimental

class Catalog(typing.NamedTuple):
    path: str          # filesystem
    # TODO using NamedTuple as base type incorrectly -> see subclasses ExperimentCatalog FileCatalog instantiation behaviour
    item_suffix: str   # filesystem
    Type : str         # import_from_qualname, hashable, de/serializable (e.g experimental.EXPERIMENT_HPARAMS
    salt: bytes = b''  # DEPRECATED: makes difficult to determine salt if several salts shared the same path

    def test_fixtures(catalog):
        # define an experiment in python
        import shared.experimental
        for experiment_hparams in shared.experimental.fixture_experiment_hparams():
            break
        
    def ensure_exists(catalog):
        path = pathlib.Path(catalog.path)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        #raise NotImplementedError("TODO mkdirs(catalog.path, exists_ok=True)")
    
    def item_path(catalog, hash) -> pathlib.Path:
        return pathlib.Path(catalog.path) / f"{hash.hex()}{catalog.item_suffix}"

    def contains(catalog, hash) -> bool:
        catalog.ensure_exists()
        return catalog.item_path(hash).exists()
    
    def add(catalog, item) -> "Hash":
        # derive hash
        _hash = hash.hash(catalog.salt, catalog.Type, item)
        # already in catalog ?
        if catalog.contains(_hash):
            return _hash
        # write it to disk
        item_path = catalog.item_path(_hash)
        with open(catalog.item_path(_hash), 'wb') as buffer:
            # acquire exclusive lock blocking
            fcntl.flock(buffer, fcntl.LOCK_EX)
            exception = None
            try:
                # serialize and write
                deser.serialize(catalog.Type, item, buffer)
            except Exception as exception:
                pass  # we release the lock before raising
            # release lock
            fcntl.flock(buffer, fcntl.LOCK_UN)

            if exception is not None:
                raise exception
            
        # set as read only
        item_path.chmod(0o400)
        return _hash

    E_ADD_NOSAFE = type("E_ADD_NOSAFE", (Exception,), {})
    def add_nosafe(catalog, item) -> "Hash":
        """variant of add: fails if exists"""
        # derive hash
        _hash = hash.hash(catalog.salt, catalog.Type, item)
        # already in catalog ?
        if catalog.contains(_hash):
            raise E_ADD_NOSAFE(f"Already contained in catalog: {_hash.hex()}")
        # write it to disk
        item_path = catalog.item_path(_hash)
        with open(catalog.item_path(_hash), 'wb') as buffer:
            # acquire exclusive lock NON blocking (would raise BlockingIOError)
            try:
                fcntl.flock(buffer, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise catalog.E_ADD_NOSAFE(f"Already locked in catalog: {_hash.hex()}")
            exception = None
            try:
                # serialize and write
                deser.serialize(catalog.Type, item, buffer)
            except Exception as _exception:
                exception = _exception
                pass  # we release the lock before raising
            # release lock
            fcntl.flock(buffer, fcntl.LOCK_UN)

            if exception is not None:
                raise exception
            
        # set as read only
        item_path.chmod(0o400)
        return _hash
    
    def get(catalog, hash):
        # already in catalog ?
        if not catalog.contains(hash):
            raise KeyError(f"{hash.hex()} not in catalog {catalog}")        
        # it can now be reloaded
        item_path = catalog.item_path(hash)
        with open(catalog.item_path(hash), 'rb') as buffer:
            # acquire shared lock blocking
            fcntl.flock(buffer, fcntl.LOCK_SH)
            exception = None
            try:
                # read and deserialize
                item = deser.deserialize(catalog.Type, buffer)
            except Exception as _exception:
                exception = _exception
                pass  # we release the lock before raising
            # release lock
            fcntl.flock(buffer, fcntl.LOCK_UN)

            if exception is not None:
                raise exception

        return item

    def iter(catalog) -> ["Hash"]:
        catalog.ensure_exists()
        path = pathlib.Path(catalog.path)
        for _path in path.glob(f"*{catalog.item_suffix}"):
            _hash_hex = _path.parts[-1][:-len(catalog.item_suffix)]
            _hash = bytes.fromhex(_hash_hex)
            yield _hash
        
        
        
    def log(catalog, hash, index, artefact):
        # TODO implement as another catalog for Type artefact, path=f"{catalog.path}/{hash}.ARTEFACTS"
        #      shared.hash.hash(Type=Index)
        raise DeprecatedError("use another catalog instead")
        raise NotImplementedError("artefact catalog a index is not implemented yet")


class ROCatalog(Catalog):
    def ensure_exists(catalog):
        path = pathlib.Path(catalog.path)
        assert path.exists()
    def add(catalog, item) -> "Hash":
        raise Exception("ROCatalog is read only")
    


class FILE_HPARAMS(typing.NamedTuple):
    name: str
    bytes: bytes

class FileCatalog(Catalog):
    """store plain bytes file"""
    path: pathlib.Path
    item_suffix: str = ".file"
    Type: str = FILE_HPARAMS
    salt: bytes = b''

def test_HPARAMS_Catalog():
    import os
    import pathlib
    import shared.hparams

    for hparams in shared.hparams.fixture_hparams():
        HPARAMS = type(hparams)
        
        SDEXPERIMENTS_PATH = pathlib.Path(os.environ["SDEXPERIMENTS_PATH"])
        catalog = Catalog(
            path = SDEXPERIMENTS_PATH / "testHPARAMSCatalog",
            item_suffix = ".hparams",
            Type = HPARAMS,
            salt = b'',
        )

        # clean up
        import shutil
        try:
            shutil.rmtree( pathlib.Path(catalog.path) )
        except FileNotFoundError:
            pass

        # actual tests
        #for experiment_hparams in shared.experimental.fixture_experiment_hparams():
        for item in [hparams]:
            _hash = catalog.add(item)
            assert catalog.contains(_hash)
            _item = catalog.get(_hash)
            assert _item == item
            assert _hash in catalog.iter()


        # clean up
        shutil.rmtree( pathlib.Path(catalog.path) )


def fixture_FILE_HPARAMS():
    yield FILE_HPARAMS(name="test-empty", bytes=b'')
    yield FILE_HPARAMS(name="test-10-bytes" , bytes=b'0'*10)
    yield FILE_HPARAMS(name="test-10-Kbytes", bytes=b'0'*10*2**10)
    yield FILE_HPARAMS(name="test-10-Mbytes", bytes=b'0'*10*2**20)
        
def test_FileCatalog():
    import os
    import pathlib
    SDEXPERIMENTS_PATH = pathlib.Path(os.environ["SDEXPERIMENTS_PATH"])
    catalog = FileCatalog(
        path = SDEXPERIMENTS_PATH / "testFileCatalog",
        item_suffix = ".file",
        Type = FILE_HPARAMS,
        salt = b'',
    )

    # clean up
    import shutil
    try:
        shutil.rmtree( pathlib.Path(catalog.path) )
    except FileNotFoundError:
        pass

    # actual tests
    for file_hparams in fixture_FILE_HPARAMS():
        item  = file_hparams
        _hash = catalog.add(item)
        assert catalog.contains(_hash)
        _item = catalog.get(_hash)
        assert _item == item
        assert _hash in catalog.iter()
            

    # clean up
    shutil.rmtree( pathlib.Path(catalog.path) )

        
if __name__ == "debug":
    import pathlib
    import os
    if pathlib.Path.cwd().parts[-1] == "shared":
       os.chdir("..")
    import shared.catalog
    import importlib
    importlib.reload(shared.catalog)
    import shared.deser
    importlib.reload(shared.deser)
    from shared.catalog import *
    
    
