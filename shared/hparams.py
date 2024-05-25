"""Type system module.


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.
"""
import typing


HPARAMS = typing.NamedTuple


def pretty(hparams, depth=0):
    """return a 'pretty' string representation of a `hparams`."""
    LF,TAB,COLUMN = '\n','\t'*(depth+1), ': '
    max_field_name_length = max(map(len,hparams._fields))

    import shared.hash
    hparams_hash = shared.hash.hash(b'', type(hparams), hparams)
    rpr = f"{type(hparams).__name__}({hparams_hash.hex()})"
    for field_name in hparams._fields:
        field_name_fmt = (field_name + " "*max_field_name_length)[:max_field_name_length]
        field_value = getattr(hparams, field_name)
        if is_HPARAMS_instance_safe(field_value):
            field_value_fmt = pretty(field_value, depth+1)
        else:
            field_value_fmt = repr(field_value)
        rpr+= LF + TAB + field_name_fmt + COLUMN + field_value_fmt

    return rpr

def is_HPARAMS_subclass(obj) -> bool:
    if not isinstance(obj, type):
        raise TypeError(f"expected a type, got {type(obj).__name__}")
    is_name_ending_with_HPARAMS = obj.__name__.endswith("_HPARAMS")
    is_a_type = isinstance(obj, type)
    is_HPARAMS_subclass = issubclass(obj, HPARAMS)
    return is_name_ending_with_HPARAMS and is_a_type

def is_HPARAMS_subclass_safe(obj) -> bool:
    try:
        return is_HPARAMS_subclass(obj)
    except TypeError:
        return False

def is_HPARAMS_instance(obj) -> bool:
    return is_HPARAMS_subclass(type(obj))

def is_HPARAMS_instance_safe(obj) -> bool:
    return is_HPARAMS_subclass_safe(type(obj))


#### tests
def fixture_HPARAMS():
    class some_HPARAMS(HPARAMS):
        some_str: str
        some_int: int
        some_bool: bool
        some_bytes: bytes
    class some_NamedTuple_HPARAMS(typing.NamedTuple):
        some_str: str
        some_int: int
        some_bool: bool
        some_bytes: bytes
    yield some_HPARAMS
    yield some_NamedTuple_HPARAMS

def fixture_non_HPARAMS():
    class some_non_HPARAMS_(typing.NamedTuple):
        some_str: str
        some_int: int
        some_bool: bool
        some_bytes: bytes
    yield some_non_HPARAMS_
    
def fixture_hparams():
    for type_HPARAMS in fixture_HPARAMS():
        values = tuple(typ() for nam,typ in type_HPARAMS.__annotations__.items())
        instance = type_HPARAMS(*values)
        yield instance

def fixture_non_hparams():
    for type_non_HPARAMS in fixture_non_HPARAMS():
        values = tuple(typ() for nam,typ in type_non_HPARAMS.__annotations__.items())
        instance = type_non_HPARAMS(*values)
        yield instance

def test_is_HPARAMS_subclass_accepts_HPARAMS_subclasses():
    for type_HPARAMS in fixture_HPARAMS():
        assert is_HPARAMS_subclass(type_HPARAMS)
        
def test_is_HPARAMS_subclass_refuses_non_HPARAMS_subclasses():
    for type_non_HPARAMS in fixture_non_HPARAMS():
        raised = False
        accepted = False
        try:
            accepted = is_HPARAMS_subclass(type_non_HPARAMS)
        except Exception:
            raised = True
        refused= (not accepted) or raised
        assert refused, f"is_HPARAMS_subclass should refuse type_non_HPARAMS {type_non_HPARAMS}"

def test_is_HPARAMS_instance_accepts_instances_of_HPARAMS_subclasses():
    for hparams_instance in fixture_hparams():
        assert is_HPARAMS_instance(hparams_instance)

def test_is_HPARAMS_instance_refuses_non_HPARAMS_subclasses():
    for non_hparams_instance in fixture_non_hparams():
        raised = False
        accepted = False
        try:
            accepted = is_HPARAMS_instance(non_hparams_instance)
        except Exception:
            raised = True
        refused= (not accepted) or raised
        assert refused, f"is_HPARAMS_instance should refuse non_hparams_instance {non_hparams_instance}"


        
