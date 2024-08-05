import typing


# future
class HashProtocol(typing.Protocol):
    @classmethod
    def hash(Proto, Type, instance, current_hash: bytes = None) -> bytes:  # TODO decide whether to keep current_hash
        raise NotImplementedError()


# current
import hashlib
from shared import deser  # TODO future: will move to WalkProtocol

def hash(current_hash: bytes, Type, instance) -> bytes:
    if current_hash is None:
        current_hash = b''
    current_hash = hashlib.new("md5", current_hash)
    # TODO: currently experimental.*_HPARAMS dependecy is hard coded in deser.py (see future)
    for walk_step in deser.walk(Type, instance):
        # note: we don t rely on the file format, only on step (container/base) type encoding
        as_bytes = deser.to_bytes(walk_step.type, walk_step.value)
        current_hash.update(as_bytes)
    return current_hash.digest()



def test_hash_HPARAMS_return_bytes():
    import shared.hparams
    for hparams in shared.hparams.fixture_hparams():
        current_hash = None
        Type = type(hparams)
        instance = hparams
        current_hash = hash(current_hash, Type, instance)
        assert isinstance(current_hash, bytes)
        
    
def old_test_hash_EXPERIMENT_HPARAMS_return_bytes():
    """ DEPRECATED because it relies on shared.experimental. Hint: see test_hash_HPARAMS_return_bytes() """
    raise Exception(""" DEPRECATED because it relies on shared.experimental. Hint: see test_hash_HPARAMS_return_bytes() """)
    import shared.experimental
    for experiment_hparams in shared.experimental.fixture_experiment_hparams():
        current_hash = None
        Type = type(experiment_hparams)
        instance = experiment_hparams
        current_hash = hash(current_hash, Type, instance)
        assert isinstance(current_hash, bytes)


if __name__ == "__main__":
    test_hash_EXPERIMENT_HPARAMS_return_bytes()
