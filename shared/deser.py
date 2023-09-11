"""author: jb.escudie
license: GNU GPLv3
"""
import typing

### future ( not used yet: current implementation is at mdule level )
# composite types
class WalkStep(typing.NamedTuple):
    name: str
    type: type
    value: object
    
class WalkProtocol(typing.Protocol):
    @classmethod
    def is_composite_type(Proto, Type) -> bool:
        raise NotImplementedError()
        #      (used in walk, from_walk, to_bytes, from_bytes)
        #      1. could use not is_base_type (but breaks tests)
        #      2. could use a context set by caller (but complex use)
        #      3. could use a test (but its universality adds an implicit dependency for caller)
    @classmethod
    def walk(Proto, Type, obj: "composite_type") -> [WalkStep]:
        raise NotImplementedError()
    @classmethod
    def from_walk(Proto, Type, walk_steps: [WalkStep]) -> "composite_type,[WalkSteps]":
        raise NotImplementedError()
    
# container and base types
class BaseTypeProtocol(typing.Protocol):
    @classmethod
    def is_base_type(Proto, Type) -> bool:
        raise NotImplementedError()
    
    @classmethod
    def to_bytes(Type, obj) -> bytes:
        raise NotImplementedError()
    
    @classmethod
    def from_bytes(Type, as_bytes) -> "base_type": # TODO note we assume as_byte is complete and all consumed
        raise NotImplementedError()

class WalkStepProtocol(typing.Protocol):
    @classmethod
    def encode_walk_step(Proto, walk_step: WalkStep) -> bytes:
        raise NotImplementedError()
    
    @classmethod
    def decode_walk_step(Proto, buffer) -> "bytes,buffer": # TODO note could loose type info as we dont return a WalkStep
        raise NotImplementedError()

class DeserProtocol(typing.Protocol):
    @classmethod
    def serialize(Proto, Type, obj, buffer):
        raise NotImplementedError()
    
    @classmethod
    def deserialize(Proto, Type, buffer) -> "composite_type":
        raise NotImplementedError()

    
### current
def is_composite_type(Type) -> bool:
    # TODO shared.experimental dependency
    # -> refactor module into a WalkProtocol
    import shared.hparams
    return shared.hparams.is_HPARAMS_subclass_safe(Type)

    
def walk(Type, obj: "HPARAMS") -> [WalkStep]:
    type_annotations = Type.__annotations__
    for annotation_name, annotation_type in type_annotations.items():
        # TODO walk type
        value = getattr(obj, annotation_name) if obj != Type else annotation_type
        if is_composite_type(annotation_type):
            yield from walk(annotation_type, value)
        else:
            yield WalkStep(annotation_name, annotation_type, value)
    
def from_walk(Type, walk_steps: [WalkStep]) -> "object,[WalkSteps]":
    type_annotations = Type.__annotations__
    names  = []
    types  = []
    values = []
    walk_steps = iter(walk_steps)
    for annotation_name, annotation_type in type_annotations.items():
        names += [annotation_name]
        types += [annotation_type]
        if is_composite_type(annotation_type):
            value, walk_steps = from_walk(annotation_type, walk_steps)
        else:
            walk_step = next(walk_steps)
            value = walk_step.value
            #raise NotImplementedError("container or base")
            #yield WalkStep(annotation_name, annotation_type, value)
        values += [value]
    return Type(**{name:value for name,type,value in zip(names,types,values)}), walk_steps

def is_iterator_empty(iterator):
    """note: is destructive (i.e will consume). Intended for asserting iterable is fully consumed """
    try:
        next(iterator)
        return False
    except StopIteration:
        return True

# container and base types
def is_base_type(Type):
    return Type in (str, int, float, bool, bytes)

StartContainerToken = b'['
SeparatorToken = bytes(1)  # TODO may require escaping
EndContainerToken = b']'

def to_bytes(Type, obj) -> bytes:
    assert not is_composite_type(Type)
    # TODO fails if Type says basic type but is not expected type (e.g. list)
    assert isinstance(obj, Type) or isinstance(obj, tuple), f"expected {Type} or tuple of {Type}, got {type(obj)}"
    # container
    if isinstance(obj, tuple):
        return StartContainerToken + SeparatorToken.join(to_bytes(Type, item) for item in obj) + EndContainerToken
    # item
    elif Type == str:
        return obj.encode("utf-8")
    elif Type == int:
        return str(obj).encode("utf-8")
    elif Type == float:
        return str(obj).encode("utf-8")
    elif Type == bool:
        return str(int(obj)).encode("utf-8")
    elif Type == bytes:
        return obj
    else:
        raise ValueError()

def from_bytes(Type, as_bytes) -> object:
    assert not is_composite_type(Type)
    # container
    if as_bytes[0:1] == StartContainerToken:
        assert as_bytes[-1:] == EndContainerToken
        return tuple(from_bytes(Type, item) for item in as_bytes[1:-1].split(SeparatorToken))
    # item
    elif Type == str:
        return as_bytes.decode("utf-8")
    elif Type == int:
        return int(as_bytes.decode("utf-8"))
    elif Type == float:
        return float(as_bytes.decode("utf-8"))
    elif Type == bool:
        return bool(int(as_bytes.decode("utf-8")))
    elif Type == bytes:
        return as_bytes
    else:
        raise ValueError()


# deser
## serialize  : walk -> to_bytes  -> encode_walk_step -> join
## deserialize: split-> decode_walk_step -> from_bytes-> from_walk
import struct

def encode_walk_step(walk_step: WalkStep) -> bytes:
    assert isinstance(walk_step.value, bytes), f"step should already be encoded in bytes, got {type(walk_step.value).__name__}. Hint: use to_bytes()"
    size = len(walk_step.value)
    assert size < 2**32, f'frame size must be encode as uint32be, got {size} > 2**32'
    size_as_bytes = struct.pack("!L", size)
    return size_as_bytes + walk_step.value

def decode_walk_step(buffer) -> "bytes,buffer":
    calcsize = struct.calcsize("!L")
    size_as_bytes = buffer.read(calcsize)
    size, *_ = struct.unpack("!L", size_as_bytes)
    value_as_bytes = buffer.read(size)
    return value_as_bytes, buffer

def serialize(Type, obj, buffer):
    for walk_step in walk(Type, obj):
        try:
            value_as_bytes = to_bytes(walk_step.type, walk_step.value)
            step_as_bytes  = WalkStep(walk_step.name, walk_step.type, value_as_bytes)
            encoded_step   = encode_walk_step(step_as_bytes)
            buffer.write(encoded_step)
        except Exception as e:
            raise Exception(walk_step.name, e)

def deserialize(Type, buffer) -> object:
    def iterate(Type, buffer):
      for walk_step in walk(Type, Type):
        try:
            value_as_bytes, buffer = decode_walk_step(buffer)
            step_as_bytes  = WalkStep(walk_step.name, walk_step.type, value_as_bytes)
            value = from_bytes(walk_step.type, value_as_bytes)
            step = WalkStep(walk_step.name, walk_step.type, value)
            yield step
        except Exception as e:
            raise Exception(walk_step, e)
    reconstructed, remaining_steps = from_walk(Type,iterate(Type, buffer))
    assert is_iterator_empty(remaining_steps), "not all steps were consumed"
    return reconstructed


# tests
def test_HPARAMS_types_are_composed_of_base_types():
    import shared.hparams
    for HPARAMS in shared.hparams.fixture_HPARAMS():
        Type = HPARAMS
        for walk_step in walk(Type, Type):
            assert is_base_type(walk_step.type)
            
def test_walk_HPARAMS_round_trip():
    import shared.hparams
    for hparams in shared.hparams.fixture_hparams():
        Type = type(hparams)
        instance = hparams
        walk_steps = walk(Type, instance)
        reconstructed, walk_steps = from_walk(Type, walk_steps)
        assert is_iterator_empty(walk_steps), "not all steps were consumed"
        assert reconstructed == instance

def test_as_bytes_HPARAMS_round_trip():
    import shared.hparams
    for hparams in shared.hparams.fixture_hparams():
        Type = type(hparams)
        instance = hparams
        for walk_step in walk(Type, instance):
            as_bytes = to_bytes(walk_step.type, walk_step.value)
            assert isinstance(as_bytes, bytes)
            decoded  = from_bytes(walk_step.type, as_bytes)
            assert decoded == walk_step.value, f"{decoded} != {walk_step.value}"

def test_deser_HPARAMS_round_trip():
    import shared.hparams
    import io
    for hparams in shared.hparams.fixture_hparams():
        buffer = io.BytesIO()
        Type = type(hparams)
        instance = hparams
        serialize(Type, instance, buffer)
        
        buffer.seek(0)
        reconstructed = deserialize(Type, buffer)

        assert reconstructed == instance
    
if __name__ == "__main__":
    import os
    if os.path.abspath(os.curdir).endswith("shared"): os.chdir("..")
    from shared.deser import *
    test_experimental_HPARAMS_types_are_composed_of_base_types()
    test_walk_HPARAMS_round_trip()
    test_as_bytes_HPARAMS_round_trip()
    test_deser_HPARAMS_round_trip()

# demo
def demo():
    # define an experiment in python
    import shared.experimental
    for experiment_hparams in shared.experimental.fixture_experiment_hparams():
        break
    # write it to disk
    import pathlib
    with open(pathlib.Path.home() / "xhp.hparams", 'wb') as buffer:
        serialize(shared.experimental.EXPERIMENT_HPARAMS, experiment_hparams, buffer)
    # it can now be reloaded
    with open(pathlib.Path.home() / "xhp.hparams", 'rb') as buffer:
        experiment_hparams = deserialize(shared.experimental.EXPERIMENT_HPARAMS, buffer)
    
        
