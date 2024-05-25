"""Catalog module.


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


######  (HPARAMS_HPARAMS and BASE_TYPE_OR_HPARAMS)
class BASE_TYPE_OR_HPARAMS(HPARAMS):
    """a HPARAMS to describe union of BASE_TYPE and HPARAMS_HPARAMS"""
    # see deser.is_composite_type(Type)
    base_type: str  # resolvable by globals().get ?
    type_hex : str  # resolvable by TypeCatalog.get

    @staticmethod
    def from_type(type):
        global BASE_TYPE_OR_HPARAMS
        import shared.deser
        import shared.catalog
        
        base_type= ""
        if shared.deser.is_base_type(type):
            assert not shared.deser.is_composite_type(type)
            base_type = type.__name__

        type_hex = ""
        if type in (BASE_TYPE_OR_HPARAMS,HPARAMS_HPARAMS):
            # special case to avoid infinite recursion
            base_type = type.__name__
        elif shared.deser.is_composite_type(type):
            assert not shared.deser.is_base_type(type)
            print("BASE_TYPE_OR_HPARAMS.from_type",type.__name__)
            type_hparams = HPARAMS_HPARAMS.from_HPARAMS(type)
            #type_hex = shared.hash.hash(b"", HPARAMS_HPARAMS, type_hparams).hex()
            type_catalog = shared.catalog.Catalog.type_catalog()
            type_hex = type_catalog.add(HPARAMS_HPARAMS)

        return BASE_TYPE_OR_HPARAMS(base_type, type_hex)
    
    def to_type(base_type_or_hparams):
        import shared.deser
        base_type, type_hex = base_type_or_hparams
        if base_type:
            assert not type_hex
            for _base_type in shared.deser.base_types:
                if _base_type.__name__ == base_type:
                    return _base_type
            # remaining are special cases defined in from_type
            return globals()[base_type]
        elif type_hex:
            assert not base_type
            type_catalog = HPARAMS_HPARAMS.type_catalog()
            return type_catalog.get(bytes.from_hex(type_hex))
        raise TypeError(base_type_or_hparams)
        
    
class HPARAMS_HPARAMS(HPARAMS):
    """a HPARAMS able to describe any HPARAMS"""
    name  : str
    fields: str
    types : BASE_TYPE_OR_HPARAMS

    @staticmethod
    def from_HPARAMS(_HPARAMS):
        print("HPARAMS_HPARAMS.from_HPARAMS",_HPARAMS.__name__, flush=True)
        name   = _HPARAMS.__name__
        fields = _HPARAMS._fields
        # HARAMS.__annotations__ type -> BASE_TYPE_OR_HPARAMS
        types  = []
        for field in fields:
            type = _HPARAMS.__annotations__[field]
            types += [BASE_TYPE_OR_HPARAMS.from_type(type)]
        types = BASE_TYPE_OR_HPARAMS(
            base_type=tuple(t.base_type for t in types),
            type_hex =tuple(t.type_hex  for t in types),
        )

        return HPARAMS_HPARAMS(name, fields, types)

    @staticmethod
    def to_HPARAMS(H_H):
        fields_and_types={}
        for field_i, field in enumerate(H_H.fields):
            base_type_or_hparams    = BASE_TYPE_OR_HPARAMS(H_H.types.base_type[field_i], H_H.types.type_hex[field_i])
            fields_and_types[field] = BASE_TYPE_OR_HPARAMS.to_type(base_type_or_hparams)
        return HPARAMS(
            H_H.name,
            **fields_and_types
        )

def test_HPARAMS_HPARAMS_from_HPARAMS():                
    class _HPARAMS(HPARAMS):
        dummy: int
        dumb : BASE_TYPE_OR_HPARAMS
            

    _HPARAMS_HPARAMS = HPARAMS_HPARAMS.from_HPARAMS(_HPARAMS)


if __name__ == "dev":
    import os, pathlib
    os.environ["CATALOG_ROOT_PATH"] = str(pathlib.Path.home() / "tmp")
    import os
    if os.path.abspath(".").endswith("/shared"):
        os.chdir("..")
    import importlib
    import shared.hparams
    importlib.reload(shared.hparams)
    from shared.hparams import *
    
    import shared.catalog
    importlib.reload(shared.catalog)
    from shared.catalog import *
    
if __name__=="test":
    import types
    items = tuple(globals().items())
    for name,value in items:
        if name.startswith("test_") and isinstance(value,types.FunctionType):
            print(value)
            value()

    import shared.catalog
    catalog = shared.catalog.Catalog(
        os.environ["CATALOG_ROOT_PATH"] + "/test_file_catalog",
        Type=shared.catalog.FILE_HPARAMS,
        item_suffix=".file",
    )
