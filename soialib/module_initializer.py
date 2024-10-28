from typing import Any, Union

from soialib import method, spec
from soialib.impl import arrays, enums, optionals, primitives, structs
from soialib.impl.type_adapter import TypeAdapter
from soialib.serializer import make_serializer

RecordAdapter = Union[structs.StructAdapter, enums.EnumAdapter]


_record_id_to_adapter: dict[str, RecordAdapter] = {}


def init_module(
    records: tuple[spec.Record, ...],
    methods: tuple[spec.Method, ...],
    constants: tuple[spec.Constant, ...],
    globals: dict[str, Any],
    # For testing
    record_id_to_adapter: dict[str, RecordAdapter] = _record_id_to_adapter,
) -> None:
    def resolve_type(type: spec.Type) -> TypeAdapter:
        if isinstance(type, spec.PrimitiveType):
            if type == spec.PrimitiveType.BOOL:
                return primitives.BOOL_ADAPTER
            elif type == spec.PrimitiveType.BYTES:
                return primitives.BYTES_ADAPTER
            elif type == spec.PrimitiveType.FLOAT32:
                return primitives.FLOAT32_ADAPTER
            elif type == spec.PrimitiveType.FLOAT64:
                return primitives.FLOAT64_ADAPTER
            elif type == spec.PrimitiveType.INT32:
                return primitives.INT32_ADAPTER
            elif type == spec.PrimitiveType.INT64:
                return primitives.INT64_ADAPTER
            elif type == spec.PrimitiveType.STRING:
                return primitives.STRING_ADAPTER
            elif type == spec.PrimitiveType.TIMESTAMP:
                return primitives.TIMESTAMP_ADAPTER
            elif type == spec.PrimitiveType.UINT64:
                return primitives.UINT64_ADAPTER
        elif isinstance(type, spec.ArrayType):
            return arrays.get_array_adapter(
                resolve_type(type.item),
                type.key_attributes,
            )
        elif isinstance(type, spec.OptionalType):
            return optionals.get_optional_adapter(resolve_type(type.other))
        elif isinstance(type, str):
            # A record id.
            return record_id_to_adapter[type]

    module_adapters: list[RecordAdapter] = []
    for record in records:
        if record.id in record_id_to_adapter:
            raise AssertionError(record.id)
        adapter: RecordAdapter
        if isinstance(record, spec.Struct):
            adapter = structs.StructAdapter(record)
        else:
            adapter = enums.EnumAdapter(record)
        module_adapters.append(adapter)
        record_id_to_adapter[record.id] = adapter
    # Once all the adapters of the module have been created, we can finalize them.
    for adapter in module_adapters:
        adapter.finalize(resolve_type)
        gen_class = adapter.gen_class
        # Add the class name to either globals() if the record is defined at the top
        # level, or the parent class otherwise.
        record_id = spec.RecordId.parse(adapter.spec.id)
        parent_id = record_id.parent
        class_name = adapter.spec.class_name
        if parent_id:
            parent_adapter = record_id_to_adapter[parent_id.record_id]
            setattr(parent_adapter.gen_class, class_name, gen_class)
            gen_class._parent_class = parent_adapter.gen_class
        else:
            globals[class_name] = gen_class
            gen_class._parent_class = None
        # TODO: comment
        gen_class.SERIALIZER = make_serializer(adapter)

    # Now that al the classes have been initialized, create the methods.
    for method_spec in methods:
        var_name = method_spec._var_name or method_spec.name
        request_serializer = make_serializer(resolve_type(method_spec.request_type))
        response_serializer = make_serializer(resolve_type(method_spec.response_type))
        globals[var_name] = method.Method(
            name=method_spec.name,
            number=method_spec.number,
            request_serializer=request_serializer,
            response_serializer=response_serializer,
        )
        del var_name, request_serializer, response_serializer

    # Create the constants.
    for constant in constants:
        serializer = make_serializer(resolve_type(constant.type))
        globals[constant.name] = serializer.from_json_code(constant.json_code)
        del serializer
