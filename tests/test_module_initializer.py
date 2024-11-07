import dataclasses
import unittest
from typing import Any

from soialib import spec
from soialib.keyed_items import KeyedItems
from soialib.method import Method
from soialib.module_initializer import init_module
from soialib.timestamp import Timestamp


class ModuleInitializerTestCase(unittest.TestCase):
    def init_test_module(self) -> dict[str, Any]:
        globals: dict[str, Any] = {}
        init_module(
            records=(
                spec.Struct(
                    id="my/module.soia:Point",
                    fields=(
                        spec.Field(
                            name="x",
                            number=0,
                            type=spec.PrimitiveType.FLOAT32,
                        ),
                        spec.Field(
                            name="y",
                            number=2,
                            type=spec.PrimitiveType.FLOAT32,
                        ),
                    ),
                    removed_numbers=(1,),
                ),
                spec.Struct(
                    id="my/module.soia:Segment",
                    fields=(
                        spec.Field(
                            name="a",
                            number=0,
                            type="my/module.soia:Point",
                            has_mutable_getter=True,
                        ),
                        spec.Field(
                            name="bb",
                            _attribute="b",
                            number=1,
                            type="my/module.soia:Point",
                            has_mutable_getter=True,
                        ),
                        spec.Field(
                            name="c",
                            number=2,
                            type=spec.OptionalType("my/module.soia:Point"),
                            has_mutable_getter=True,
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:Shape",
                    fields=(
                        spec.Field(
                            name="points",
                            number=0,
                            type=spec.ArrayType("my/module.soia:Point"),
                            has_mutable_getter=True,
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:Primitives",
                    fields=(
                        spec.Field(
                            name="bool",
                            number=0,
                            type=spec.PrimitiveType.BOOL,
                        ),
                        spec.Field(
                            name="bytes",
                            number=1,
                            type=spec.PrimitiveType.BYTES,
                        ),
                        spec.Field(
                            name="f32",
                            number=2,
                            type=spec.PrimitiveType.FLOAT32,
                        ),
                        spec.Field(
                            name="f64",
                            number=3,
                            type=spec.PrimitiveType.FLOAT64,
                        ),
                        spec.Field(
                            name="i32",
                            number=4,
                            type=spec.PrimitiveType.INT32,
                        ),
                        spec.Field(
                            name="i64",
                            number=5,
                            type=spec.PrimitiveType.INT32,
                        ),
                        spec.Field(
                            name="u64",
                            number=6,
                            type=spec.PrimitiveType.INT32,
                        ),
                        spec.Field(
                            name="s",
                            number=7,
                            type=spec.PrimitiveType.STRING,
                        ),
                        spec.Field(
                            name="t",
                            number=8,
                            type=spec.PrimitiveType.TIMESTAMP,
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:After",
                    fields=(
                        spec.Field(
                            name="points",
                            number=0,
                            type=spec.ArrayType("my/module.soia:Point"),
                            has_mutable_getter=True,
                        ),
                    ),
                ),
                spec.Enum(
                    id="my/module.soia:PrimaryColor",
                    constant_fields=(
                        spec.ConstantField(
                            name="RED",
                            number=10,
                        ),
                        spec.ConstantField(
                            name="GREEN",
                            number=20,
                        ),
                        spec.ConstantField(
                            name="BLUE",
                            number=30,
                        ),
                    ),
                ),
                spec.Enum(
                    id="my/module.soia:Status",
                    constant_fields=(
                        spec.ConstantField(
                            name="OK",
                            number=1,
                        ),
                    ),
                    value_fields=(
                        spec.ValueField(
                            name="error",
                            number=2,
                            type=spec.PrimitiveType.STRING,
                        ),
                    ),
                    removed_numbers=(1, 4),
                ),
                spec.Enum(
                    id="my/module.soia:JsonValue",
                    constant_fields=(
                        spec.ConstantField(
                            name="NULL",
                            number=1,
                        ),
                    ),
                    value_fields=(
                        spec.ValueField(
                            name="bool",
                            number=2,
                            type=spec.PrimitiveType.BOOL,
                        ),
                        spec.ValueField(
                            name="number",
                            number=3,
                            type=spec.PrimitiveType.FLOAT64,
                        ),
                        spec.ValueField(
                            name="string",
                            number=4,
                            type=spec.PrimitiveType.STRING,
                        ),
                        spec.ValueField(
                            name="array",
                            number=5,
                            type=spec.ArrayType("my/module.soia:JsonValue"),
                        ),
                        spec.ValueField(
                            name="object",
                            number=6,
                            type="my/module.soia:JsonValue.Object",
                        ),
                    ),
                    removed_numbers=(
                        100,
                        101,
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:JsonValue.Object",
                    fields=(
                        spec.Field(
                            name="entries",
                            number=0,
                            type=spec.ArrayType(
                                item="my/module.soia:JsonValue.ObjectEntry",
                                key_attributes=("name",),
                            ),
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:JsonValue.ObjectEntry",
                    fields=(
                        spec.Field(
                            name="name",
                            number=0,
                            type=spec.PrimitiveType.STRING,
                        ),
                        spec.Field(
                            name="value",
                            number=1,
                            type="my/module.soia:JsonValue",
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:Parent",
                    fields=(),
                ),
                spec.Enum(
                    id="my/module.soia:Parent.NestedEnum",
                ),
                spec.Struct(
                    id="my/module.soia:Stuff",
                    fields=(
                        spec.Field(
                            name="enum_wrappers",
                            number=0,
                            type=spec.ArrayType(
                                item="my/module.soia:EnumWrapper",
                                key_attributes=(
                                    "status",
                                    "kind",
                                ),
                            ),
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:EnumWrapper",
                    fields=(
                        spec.Field(
                            name="status",
                            number=0,
                            type="my/module.soia:Status",
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:Stuff.Overrides",
                    _class_name="NameOverrides",
                    _class_qualname="Stuff.NameOverrides",
                    fields=(
                        spec.Field(
                            name="x",
                            _attribute="y",
                            number=0,
                            type=spec.PrimitiveType.INT32,
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:RecOuter",
                    fields=(
                        spec.Field(
                            name="r",
                            number=0,
                            type="my/module.soia:RecOuter.RecInner",
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:RecOuter.RecInner",
                    fields=(
                        spec.Field(
                            name="r",
                            number=0,
                            type="my/module.soia:RecOuter",
                        ),
                    ),
                ),
                spec.Struct(
                    id="my/module.soia:Foobar",
                    fields=(
                        spec.Field(
                            name="a",
                            number=1,
                            type=spec.PrimitiveType.INT32,
                        ),
                        spec.Field(
                            name="b",
                            number=3,
                            type=spec.PrimitiveType.INT32,
                        ),
                        spec.Field(
                            name="point",
                            number=4,
                            type="my/module.soia:Point",
                        ),
                    ),
                    removed_numbers=(0, 2),
                ),
            ),
            methods=(
                spec.Method(
                    name="FirstMethod",
                    number=-300,
                    request_type="my/module.soia:Point",
                    response_type="my/module.soia:Shape",
                ),
                spec.Method(
                    name="SecondMethod",
                    number=-301,
                    request_type="my/module.soia:Point",
                    response_type="my/module.soia:Shape",
                    _var_name="MethodVar",
                ),
            ),
            constants=(
                spec.Constant(
                    name="C",
                    type="my/module.soia:Point",
                    json_code="[1.5, 0, 2.5]",
                ),
            ),
            globals=globals,
            record_id_to_adapter={},
        )
        return globals

    def test_struct_getters(self):
        point_cls = self.init_test_module()["Point"]
        point = point_cls(x=1.5, y=2.5)
        self.assertEqual(point.x, 1.5)
        self.assertEqual(point.y, 2.5)

    def test_to_mutable(self):
        point_cls = self.init_test_module()["Point"]
        point = point_cls(x=1.5, y=2.5)
        mutable = point.to_mutable()
        mutable.x = 4.0
        point = mutable.to_frozen()
        self.assertEqual(point.x, 4.0)
        self.assertEqual(point.y, 2.5)
        self.assertIs(point.to_frozen(), point)

    def test_struct_eq(self):
        point_cls = self.init_test_module()["Point"]
        a = point_cls(x=1.5, y=2.5)
        b = point_cls(x=1.5, y=2.5)
        c = point_cls(x=1.5, y=3.0)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, "foo")
        self.assertEqual(point_cls(), point_cls(x=0.0, y=0.0))

    def test_or_mutable(self):
        point_cls = self.init_test_module()["Point"]
        point_cls.OrMutable

    def test_primitives_default_values(self):
        primitives_cls = self.init_test_module()["Primitives"]
        a = primitives_cls(
            bool=False,
            bytes=b"",
            f32=0.0,
            f64=0,
            i32=0,
            i64=0,
            u64=0,
            t=Timestamp.EPOCH,
        )
        b = primitives_cls()
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_primitives_to_json(self):
        primitives_cls = self.init_test_module()["Primitives"]
        serializer = primitives_cls.SERIALIZER
        p = primitives_cls(
            bool=True,
            bytes=b"a",
            f32=3.14,
            f64=3.14,
            i32=1,
            i64=2,
            u64=3,
            t=Timestamp.from_unix_millis(4),
        )
        self.assertEqual(serializer.to_json(p), [1, "61", 3.14, 3.14, 1, 2, 3, "", 4])

    def test_primitives_from_json(self):
        primitives_cls = self.init_test_module()["Primitives"]
        serializer = primitives_cls.SERIALIZER
        json = [0] * 100
        self.assertEqual(serializer.from_json(json), primitives_cls.DEFAULT)
        self.assertEqual(
            serializer.from_json([1, "61", 3.14, 3.14, 1, 2, 3, "", 4]),
            primitives_cls(
                bool=True,
                bytes=b"a",
                f32=3.14,
                f64=3.14,
                i32=1,
                i64=2,
                u64=3,
                t=Timestamp.from_unix_millis(4),
            ),
        )

    def test_primitives_repr(self):
        primitives_cls = self.init_test_module()["Primitives"]
        serializer = primitives_cls.SERIALIZER
        p = primitives_cls(
            bool=True,
            bytes=b"a",
            f32=3.14,
            f64=3.14,
            i32=1,
            i64=2,
            u64=3,
            t=Timestamp.from_unix_millis(4),
        )
        self.assertEqual(
            str(p),
            "Primitives(\n  bool=True,\n  bytes=b'a',\n  f32=3.14,\n  f64=3.14,\n  i32=1,\n  i64=2,\n  u64=3,\n  t=Timestamp(\n    unix_millis=4,\n    _formatted='1970-01-01T00:00:00.004000Z',\n  ),\n)",
        )

    def test_from_json_converts_between_ints_and_floats(self):
        primitives_cls = self.init_test_module()["Primitives"]
        serializer = primitives_cls.SERIALIZER
        p = serializer.from_json([0, 0, 3])
        self.assertEqual(p.f32, 3.0)
        self.assertIsInstance(p.f32, float)
        p = serializer.from_json({"i32": 1.2})
        self.assertEqual(p.i32, 1)
        self.assertIsInstance(p.i32, int)

    def test_cannot_mutate_frozen_class(self):
        point_cls = self.init_test_module()["Point"]
        serializer = point_cls.SERIALIZER
        point = point_cls(x=1.5, y=2.5)
        try:
            point.x = 3.5
            self.fail("expected to raise FrozenInstanceError")
        except dataclasses.FrozenInstanceError:
            pass
        self.assertEqual(point.x, 1.5)

    def test_point_to_dense_json(self):
        point_cls = self.init_test_module()["Point"]
        serializer = point_cls.SERIALIZER
        point = point_cls(x=1.5, y=2.5)
        self.assertEqual(serializer.to_json(point), [1.5, 0, 2.5])
        self.assertEqual(serializer.to_json(point, readable=False), [1.5, 0, 2.5])
        self.assertEqual(serializer.to_json_code(point), "[1.5,0,2.5]")
        point = point_cls(x=1.5, y=0.0)
        self.assertEqual(serializer.to_json(point), [1.5])

    def test_point_to_readable_json(self):
        point_cls = self.init_test_module()["Point"]
        point = point_cls(x=1.5, y=2.5)
        json = point_cls.SERIALIZER.to_json(point, readable=True)
        self.assertEqual(json, {"x": 1.5, "y": 2.5})
        json_code = point_cls.SERIALIZER.to_json_code(point, readable=True)
        self.assertEqual(json_code, '{\n  "x": 1.5,\n  "y": 2.5\n}')

    def test_point_from_dense_json(self):
        point_cls = self.init_test_module()["Point"]
        serializer = point_cls.SERIALIZER
        self.assertEqual(serializer.from_json([1.5, 0, 2.5]), point_cls(x=1.5, y=2.5))
        self.assertEqual(serializer.from_json([1.5]), point_cls(x=1.5))
        self.assertEqual(serializer.from_json([0.0]), point_cls.DEFAULT)
        self.assertEqual(serializer.from_json(0), point_cls.DEFAULT)

    def test_point_from_readable_json(self):
        point_cls = self.init_test_module()["Point"]
        point = point_cls.SERIALIZER.from_json({"x": 1.5, "y": 2.5})
        self.assertEqual(point, point_cls(x=1.5, y=2.5))
        point = point_cls.SERIALIZER.from_json_code('{"x":1.5,"y":2.5}')
        self.assertEqual(point, point_cls(x=1.5, y=2.5))
        point = point_cls.SERIALIZER.from_json_code('{"x":1.5,"y":2.5,"z":[]}')
        self.assertEqual(point, point_cls(x=1.5, y=2.5))
        point = point_cls.SERIALIZER.from_json_code('{"x":1,"y":2}')
        self.assertEqual(point.x, 1.0)
        self.assertIsInstance(point.x, float)

    def test_point_with_unrecognized_and_removed_fields(self):
        point_cls = self.init_test_module()["Point"]
        serializer = point_cls.SERIALIZER
        point = serializer.from_json([1.5, 1, 2.5, True])
        self.assertEqual(point, point_cls(x=1.5, y=2.5))
        self.assertEqual(serializer.to_json(point), [1.5, 0, 2.5, True])
        point = point.to_mutable().to_frozen()
        self.assertEqual(serializer.to_json(point), [1.5, 0, 2.5, True])

    def test_struct_to_dense_json_with_removed_fields(self):
        test_module = self.init_test_module()
        foobar_cls = test_module["Foobar"]
        point_cls = test_module["Point"]
        serializer = foobar_cls.SERIALIZER
        foobar = foobar_cls()
        self.assertEqual(serializer.to_json_code(foobar), "[]")
        self.assertEqual(serializer.from_json_code("[]"), foobar)
        foobar = foobar_cls(a=3)
        self.assertEqual(serializer.to_json_code(foobar), "[0,3]")
        self.assertEqual(serializer.from_json_code("[0,3]"), foobar)
        self.assertEqual(serializer.from_json_code("[0,3.1]"), foobar)
        foobar = foobar_cls(b=3, point=point_cls.DEFAULT)
        self.assertEqual(serializer.to_json_code(foobar), "[0,0,0,3]")
        self.assertEqual(serializer.from_json_code("[0,0,0,3]"), foobar)
        self.assertEqual(serializer.from_json_code("[0,0,0,3.1]"), foobar)
        foobar = foobar_cls(point=point_cls(x=2))
        self.assertEqual(serializer.to_json_code(foobar), "[0,0,0,0,[2.0]]")
        self.assertEqual(serializer.from_json_code("[0,0,0,0,[2.0]]"), foobar)

    def test_struct_ctor_accepts_mutable_struct(self):
        module = self.init_test_module()
        segment_cls = module["Segment"]
        point_cls = module["Point"]
        segment = segment_cls(
            a=point_cls(x=1.0, y=2.0).to_mutable(),
            b=point_cls(x=3.0, y=4.0),
        )
        self.assertEqual(
            segment,
            segment_cls(
                a=point_cls(x=1.0, y=2.0),
                b=point_cls(x=3.0, y=4.0),
                c=None,
            ),
        )

    def test_struct_ctor_checks_type_of_struct_param(self):
        module = self.init_test_module()
        segment_cls = module["Segment"]
        try:
            segment_cls(
                # Should be a Point
                a=segment_cls.DEFAULT,
            )
            self.fail("Expected to fail")
        except Exception as e:
            self.assertIn("Point", str(e))

    def test_struct_ctor_raises_error_if_unknown_arg(self):
        module = self.init_test_module()
        segment_cls = module["Segment"]

    def test_to_frozen_checks_type_of_struct_field(self):
        module = self.init_test_module()
        segment_cls = module["Segment"]
        mutable = segment_cls.Mutable()
        mutable.a = segment_cls.DEFAULT  # Should be a Point
        try:
            mutable.to_frozen()
            self.fail("Expected to fail")
        except Exception as e:
            self.assertIn("Point", str(e))

    def test_struct_ctor_accepts_mutable_list(self):
        module = self.init_test_module()
        shape_cls = module["Shape"]
        point_cls = module["Point"]
        shape = shape_cls(
            points=[
                point_cls(x=1.0, y=2.0).to_mutable(),
                point_cls(x=3.0, y=4.0),
            ],
        )
        self.assertEqual(
            shape,
            shape_cls(
                points=(
                    point_cls(x=1.0, y=2.0),
                    point_cls(x=3.0, y=4.0),
                ),
            ),
        )

    def test_listuple_not_copied(self):
        module = self.init_test_module()
        shape_cls = module["Shape"]
        point_cls = module["Point"]
        shape = shape_cls(
            points=[
                point_cls(x=1.0, y=2.0),
                point_cls(x=3.0, y=4.0),
            ],
        )
        other_shape = shape.to_mutable().to_frozen()
        self.assertIsNot(other_shape, shape)
        self.assertIs(other_shape.points, shape.points)
        self.assertIsNot(other_shape.points.__class__, tuple)

    def test_single_empty_listuple_instance(self):
        module = self.init_test_module()
        shape_cls = module["Shape"]
        shape = shape_cls(
            points=[],
        )
        self.assertIs(shape.points, shape_cls(points=[]).points)
        self.assertIs(shape.points, shape.to_mutable().to_frozen().points)
        self.assertIsNot(shape.points, ())

    def test_optional(self):
        module = self.init_test_module()
        segment_cls = module["Segment"]
        point_cls = module["Point"]
        segment = segment_cls(
            c=point_cls.Mutable(x=1.0, y=2.0),
        )
        other_segment = segment.to_mutable().to_frozen()
        self.assertEqual(
            other_segment,
            segment_cls(
                c=point_cls(x=1.0, y=2.0),
            ),
        )

    def test_enum_unknown_constant(self):
        module = self.init_test_module()
        primary_color_cls = module["PrimaryColor"]
        unknown = primary_color_cls.UNKNOWN
        self.assertEqual(unknown.kind, "?")
        self.assertEqual(unknown.value, None)
        self.assertIs(unknown.union, unknown)
        serializer = primary_color_cls.SERIALIZER
        self.assertEqual(serializer.to_json(unknown), 0)
        self.assertEqual(serializer.to_json(unknown, readable=True), "?")

    def test_enum_user_defined_constant(self):
        module = self.init_test_module()
        primary_color_cls = module["PrimaryColor"]
        red = primary_color_cls.RED
        self.assertEqual(red.kind, "RED")
        self.assertEqual(red.value, None)
        self.assertIs(red.union, red)
        serializer = primary_color_cls.SERIALIZER
        self.assertEqual(serializer.to_json(red), 10)
        self.assertEqual(serializer.to_json(red, readable=True), "RED")

    def test_enum_wrap(self):
        module = self.init_test_module()
        status_cls = module["Status"]
        error = status_cls.wrap_error("An error occurred")
        self.assertEqual(error.kind, "error")
        self.assertEqual(error.value, "An error occurred")
        self.assertIs(error.union, error)
        serializer = status_cls.SERIALIZER
        self.assertEqual(serializer.to_json(error), [2, "An error occurred"])
        self.assertEqual(
            serializer.to_json(error, readable=True),
            {"kind": "error", "value": "An error occurred"},
        )

    def test_enum_wrap_around_mutable_struct(self):
        module = self.init_test_module()
        json_value_cls = module["JsonValue"]
        json_object_cls = json_value_cls.Object
        json_object = json_value_cls.wrap_object(json_object_cls().to_mutable())
        self.assertEqual(json_object.kind, "object")
        self.assertEqual(json_object.value, json_object_cls.DEFAULT)
        self.assertEqual(
            json_object, json_value_cls.wrap_object(json_object_cls.DEFAULT)
        )

    def test_enum_to_json(self):
        module = self.init_test_module()
        status_cls = module["Status"]
        serializer = status_cls.SERIALIZER
        self.assertEqual(serializer.to_json(status_cls.UNKNOWN), 0)
        self.assertEqual(serializer.to_json(status_cls.UNKNOWN, readable=True), "?")
        self.assertEqual(serializer.to_json(status_cls.OK), 1)
        self.assertEqual(serializer.to_json(status_cls.OK, readable=True), "OK")
        self.assertEqual(serializer.to_json(status_cls.OK, readable=False), 1)
        self.assertEqual(serializer.to_json(status_cls.wrap_error("E")), [2, "E"])
        self.assertEqual(
            serializer.to_json(status_cls.wrap_error("E"), readable=True),
            {"kind": "error", "value": "E"},
        )

    def test_enum_from_json(self):
        module = self.init_test_module()
        status_cls = module["Status"]
        serializer = status_cls.SERIALIZER
        self.assertEqual(serializer.from_json(0), status_cls.UNKNOWN)
        self.assertEqual(serializer.from_json("?"), status_cls.UNKNOWN)
        self.assertEqual(serializer.from_json(1), status_cls.OK)
        self.assertEqual(serializer.from_json("OK"), status_cls.OK)
        self.assertEqual(serializer.from_json([2, "E"]), status_cls.wrap_error("E"))
        self.assertEqual(
            serializer.from_json({"kind": "error", "value": "E"}),
            status_cls.wrap_error("E"),
        )

    def test_complex_enum_from_json(self):
        module = self.init_test_module()
        json_value_cls = module["JsonValue"]
        serializer = json_value_cls.SERIALIZER
        json_value = serializer.from_json(
            [
                5,
                [
                    0,
                    1,
                    [2, True],
                    [3, 3.14],
                    [4, "foo"],
                    [
                        6,
                        [["a", 0], ["b", 0]],
                    ],
                    [5, [[5, []]]],
                ],
            ]
        )
        self.assertEqual(
            json_value,
            json_value_cls.wrap_array(
                [
                    json_value_cls.UNKNOWN,
                    json_value_cls.NULL,
                    json_value_cls.wrap_bool(True),
                    json_value_cls.wrap_number(3.14),
                    json_value_cls.wrap_string("foo"),
                    json_value_cls.wrap_object(
                        json_value_cls.Object(
                            entries=[
                                json_value_cls.ObjectEntry(),
                                json_value_cls.ObjectEntry.DEFAULT,
                            ],
                        )
                    ),
                    json_value_cls.wrap_array(
                        [
                            json_value_cls.wrap_array([]),
                        ]
                    ),
                ]
            ),
        )
        self.assertEqual(
            serializer.from_json(
                {
                    "kind": "array",
                    "value": [
                        "?",
                        "NULL",
                        {"kind": "bool", "value": True},
                        {"kind": "number", "value": 3.14},
                        {"kind": "string", "value": "foo"},
                        {"kind": "object", "value": {"entries": [{}, {}]}},
                        {"kind": "array", "value": [{"kind": "array", "value": []}]},
                    ],
                }
            ),
            json_value,
        )

    def test_struct_with_enum_field(self):
        json_value_cls = self.init_test_module()["JsonValue"]
        json_object_entry_cls = json_value_cls.ObjectEntry
        self.assertEqual(json_object_entry_cls.DEFAULT.value, json_value_cls.UNKNOWN)
        self.assertEqual(json_object_entry_cls().value, json_value_cls.UNKNOWN)

    def test_enum_with_unrecognized_and_removed_fields(self):
        json_value_cls = self.init_test_module()["JsonValue"]
        serializer = json_value_cls.SERIALIZER
        json_value = serializer.from_json(100)  # removed
        self.assertEqual(json_value, json_value_cls.UNKNOWN)
        self.assertEqual(serializer.to_json(json_value), 0)
        json_value = serializer.from_json([101, True])  # removed
        self.assertEqual(json_value, json_value_cls.UNKNOWN)
        self.assertEqual(serializer.to_json(json_value), 0)
        json_value = serializer.from_json(102)  # unrecognized
        self.assertEqual(json_value, json_value_cls.UNKNOWN)
        self.assertEqual(serializer.to_json(json_value), 102)
        json_value = serializer.from_json([102, True])  # unrecognized
        self.assertEqual(json_value, json_value_cls.UNKNOWN)
        self.assertEqual(serializer.to_json(json_value), [102, True])

    def test_class_name(self):
        module = self.init_test_module()
        shape_cls = module["Shape"]
        json_value_cls = module["JsonValue"]
        json_object_cls = json_value_cls.Object
        self.assertEqual(shape_cls.__name__, "Shape")
        self.assertEqual(shape_cls.__qualname__, "Shape")
        self.assertEqual(json_value_cls.__name__, "JsonValue")
        self.assertEqual(json_value_cls.__qualname__, "JsonValue")
        self.assertEqual(json_object_cls.__name__, "Object")
        self.assertEqual(json_object_cls.__qualname__, "JsonValue.Object")

    def test_struct_repr(self):
        module = self.init_test_module()
        point_cls = module["Point"]
        self.assertEqual(
            repr(point_cls(x=1.5)),
            "Point(x=1.5)",
        )
        self.assertEqual(
            repr(point_cls(x=1.5).to_mutable()),
            "\n".join(
                [
                    "Point.Mutable(",
                    "  x=1.5,",
                    "  y=0.0,",
                    ")",
                ]
            ),
        )
        self.assertEqual(
            repr(point_cls(x=1.5, y=2.5)),
            "\n".join(
                [
                    "Point(",
                    "  x=1.5,",
                    "  y=2.5,",
                    ")",
                ]
            ),
        )
        self.assertEqual(
            repr(point_cls()),
            "Point()",
        )
        self.assertEqual(
            repr(point_cls.DEFAULT),
            "Point.DEFAULT",
        )
        self.assertEqual(
            repr(point_cls.DEFAULT.to_mutable()),
            "\n".join(
                [
                    "Point.Mutable(",
                    "  x=0.0,",
                    "  y=0.0,",
                    ")",
                ]
            ),
        )
        shape_cls = module["Shape"]
        self.assertEqual(
            repr(shape_cls(points=[])),
            "Shape()",
        )
        self.assertEqual(
            repr(shape_cls(points=[]).to_mutable()),
            "Shape.Mutable(points=[])",
        )
        self.assertEqual(
            repr(shape_cls(points=[point_cls(x=1.5)])),
            "\n".join(
                [
                    "Shape(",
                    "  points=[",
                    "    Point(x=1.5),",
                    "  ],",
                    ")",
                ]
            ),
        )
        self.assertEqual(
            repr(
                shape_cls(
                    points=[
                        point_cls(x=1.5),
                        point_cls(y=2.5),
                    ],
                )
            ),
            "\n".join(
                [
                    "Shape(",
                    "  points=[",
                    "    Point(x=1.5),",
                    "    Point(y=2.5),",
                    "  ],",
                    ")",
                ]
            ),
        )
        self.assertEqual(
            repr(
                shape_cls.Mutable(
                    points=[
                        point_cls(x=1.5),
                        point_cls(y=2.5).to_mutable(),
                    ]
                )
            ),
            "\n".join(
                [
                    "Shape.Mutable(",
                    "  points=[",
                    "    Point(x=1.5),",
                    "    Point.Mutable(",
                    "      x=0.0,",
                    "      y=2.5,",
                    "    ),",
                    "  ],",
                    ")",
                ]
            ),
        )

    def test_enum_constant_repr(self):
        module = self.init_test_module()
        primary_color_cls = module["PrimaryColor"]
        parent_cls = module["Parent"]
        nested_enum_cls = parent_cls.NestedEnum
        self.assertEqual(repr(primary_color_cls.UNKNOWN), "PrimaryColor.UNKNOWN")
        self.assertEqual(repr(primary_color_cls.RED), "PrimaryColor.RED")
        self.assertEqual(repr(nested_enum_cls.UNKNOWN), "Parent.NestedEnum.UNKNOWN")

    def test_enum_value_repr(self):
        module = self.init_test_module()
        status_cls = module["Status"]
        json_value_cls = module["JsonValue"]
        json_object_cls = json_value_cls.Object
        self.assertEqual(
            repr(status_cls.wrap_error("An error")),
            "Status.wrap_error('An error')",
        )
        self.assertEqual(
            repr(status_cls.wrap_error("multiple\nlines\n")),
            "\n".join(
                [
                    "Status.wrap_error(",
                    "  '\\n'.join([",
                    "    'multiple',",
                    "    'lines',",
                    "    '',",
                    "  ])",
                    ")",
                ]
            ),
        )
        self.assertEqual(
            repr(json_value_cls.wrap_object(json_object_cls().DEFAULT)),
            "JsonValue.wrap_object(JsonValue.Object.DEFAULT)",
        )
        self.assertEqual(
            repr(json_value_cls.wrap_object(json_object_cls())),
            "\n".join(
                [
                    "JsonValue.wrap_object(",
                    "  JsonValue.Object()",
                    ")",
                ]
            ),
        )

    def test_find_in_keyed_items(self):
        json_value_cls = self.init_test_module()["JsonValue"]
        object_cls = json_value_cls.Object
        entry_cls = json_value_cls.ObjectEntry
        json_object = object_cls(
            entries=[
                entry_cls(
                    name="foo",
                    value=json_value_cls.wrap_string("value of foo"),
                ),
                entry_cls(
                    name="bar",
                    value=json_value_cls.wrap_string("value of bar #0"),
                ),
                entry_cls(
                    name="foobar",
                    value=json_value_cls.wrap_string("value of foobar"),
                ),
                entry_cls(
                    name="bar",
                    value=json_value_cls.wrap_string("value of bar #1"),
                ),
            ]
        )
        entries = json_object.entries
        self.assertIsInstance(entries, KeyedItems)
        self.assertIs(entries.find("foo"), entries[0])
        self.assertIs(entries.find("zoo"), None)
        self.assertIs(entries.find("bar"), entries[3])
        self.assertIs(entries.find_or_default("foo"), entries[0])
        self.assertIs(entries.find_or_default("zoo"), entry_cls.DEFAULT)

    def test_find_in_keyed_items_with_complex_path(self):
        module = self.init_test_module()
        stuff_cls = module["Stuff"]
        enum_wrapper_cls = module["EnumWrapper"]
        status_cls = module["Status"]
        stuff = stuff_cls(
            enum_wrappers=[
                enum_wrapper_cls(
                    status=status_cls.OK,
                ),
                enum_wrapper_cls(
                    status=status_cls.wrap_error("an error"),
                ),
                enum_wrapper_cls(
                    status=status_cls.OK,
                ),
            ]
        )
        enum_wrappers = stuff.enum_wrappers
        self.assertIsInstance(enum_wrappers, KeyedItems)
        self.assertIs(enum_wrappers.find("OK"), enum_wrappers[2])
        self.assertIs(enum_wrappers.find("error"), enum_wrappers[1])
        self.assertIs(enum_wrappers.find_or_default("?"), enum_wrapper_cls.DEFAULT)
        enum_wrappers = stuff.to_mutable().to_frozen().enum_wrappers
        self.assertIs(enum_wrappers.find("error"), enum_wrappers[1])

    def test_name_overrides(self):
        name_overrides_cls = self.init_test_module()["Stuff"].NameOverrides
        name_overrides = name_overrides_cls(y=3)
        self.assertEqual(name_overrides.y, 3)
        self.assertEqual(name_overrides_cls.__name__, "NameOverrides")
        self.assertEqual(name_overrides_cls.__qualname__, "Stuff.NameOverrides")

    def test_mutable_getter_of_struct(self):
        module = self.init_test_module()
        segment_cls = module["Segment"]
        point_cls = module["Point"]
        segment = segment_cls(
            a=point_cls(x=1.0, y=2.0),
            b=point_cls(x=3.0, y=4.0),
        ).to_mutable()
        a = segment.mutable_a
        self.assertIsInstance(a, point_cls.Mutable)
        self.assertIs(segment.mutable_a, a)
        segment.a = "foo"
        try:
            segment.mutable_a()
            self.fail("Expected to fail")
        except TypeError as e:
            self.assertEqual(str(e), "expected: Point or Point.Mutable; found: str")

    def test_mutable_getter_of_array(self):
        module = self.init_test_module()
        shape_cls = module["Shape"]
        point_cls = module["Point"]
        shape = shape_cls(
            points=[
                point_cls(x=1.0, y=2.0),
                point_cls(x=3.0, y=4.0),
            ],
        ).to_mutable()
        points = shape.mutable_points
        self.assertIsInstance(points, list)
        self.assertIs(shape.mutable_points, points)

    def test_methods(self):
        module = self.init_test_module()
        first_method = module["FirstMethod"]
        self.assertEqual(
            first_method,
            Method(
                name="FirstMethod",
                number=-300,
                request_serializer=module["Point"].SERIALIZER,
                response_serializer=module["Shape"].SERIALIZER,
            ),
        )
        second_method = module["MethodVar"]
        self.assertEqual(
            second_method,
            Method(
                name="SecondMethod",
                number=-301,
                request_serializer=module["Point"].SERIALIZER,
                response_serializer=module["Shape"].SERIALIZER,
            ),
        )

    def test_constants(self):
        module = self.init_test_module()
        c = module["C"]
        Point = module["Point"]
        self.assertEqual(c, Point(x=1.5, y=2.5))
