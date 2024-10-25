# TODO: test from JSON

import unittest
from typing import Any

from soialib import spec
from soialib.keyed_items import KeyedItems
from soialib.module_initializer import init_module_classes
from soialib.timestamp import Timestamp


class ModuleInitializerTestCase(unittest.TestCase):
    def init_test_module_classes(self) -> dict[str, Any]:
        globals: dict[str, Any] = {}
        init_module_classes(
            (
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
                            number=1,
                            type=spec.PrimitiveType.FLOAT32,
                        ),
                    ),
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
                            number=0,
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
                            number=0,
                        ),
                    ),
                    value_fields=(
                        spec.ValueField(
                            name="bool",
                            number=1,
                            type=spec.PrimitiveType.BOOL,
                        ),
                        spec.ValueField(
                            name="number",
                            number=2,
                            type=spec.PrimitiveType.FLOAT64,
                        ),
                        spec.ValueField(
                            name="string",
                            number=3,
                            type=spec.PrimitiveType.STRING,
                        ),
                        spec.ValueField(
                            name="array",
                            number=4,
                            type=spec.ArrayType("my/module.soia:JsonValue"),
                        ),
                        spec.ValueField(
                            name="object",
                            number=5,
                            type="my/module.soia:JsonValue.Object",
                        ),
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
            ),
            globals=globals,
            record_id_to_adapter={},
        )
        return globals

    def test_struct_getters(self):
        point_cls = self.init_test_module_classes()["Point"]
        point = point_cls(x=1.5, y=2.5)
        self.assertEqual(point.x, 1.5)
        self.assertEqual(point.y, 2.5)

    def test_to_mutable(self):
        point_cls = self.init_test_module_classes()["Point"]
        point = point_cls(x=1.5, y=2.5)
        mutable = point.to_mutable()
        mutable.x = 4.0
        point = mutable.to_frozen()
        self.assertEqual(point.x, 4.0)
        self.assertEqual(point.y, 2.5)
        self.assertIs(point.to_frozen(), point)

    def test_struct_eq(self):
        point_cls = self.init_test_module_classes()["Point"]
        a = point_cls(x=1.5, y=2.5)
        b = point_cls(x=1.5, y=2.5)
        c = point_cls(x=1.5, y=3.0)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, "foo")
        self.assertEqual(point_cls(), point_cls(x=0.0, y=0.0))

    def test_or_mutable(self):
        point_cls = self.init_test_module_classes()["Point"]
        point_cls.OrMutable

    def test_default_values(self):
        primitives_cls = self.init_test_module_classes()["Primitives"]
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
        self.assertEqual(hash(a), hash(b))

    def test_to_dense_json(self):
        point_cls = self.init_test_module_classes()["Point"]
        point = point_cls(x=1.5, y=2.5)
        json = point_cls.SERIALIZER.to_json(point)
        self.assertEqual(json, [1.5, 2.5])

    def test_to_readable_json(self):
        point_cls = self.init_test_module_classes()["Point"]
        point = point_cls(x=1.5, y=2.5)
        json = point_cls.SERIALIZER.to_json(point, readable_flavor=True)
        self.assertEqual(json, {"x": 1.5, "y": 2.5})

    def test_from_dense_json(self):
        point_cls = self.init_test_module_classes()["Point"]
        point = point_cls.SERIALIZER.from_json([1.5, 2.5])
        self.assertEqual(point, point_cls(x=1.5, y=2.5))

    def test_from_readable_json(self):
        point_cls = self.init_test_module_classes()["Point"]
        point = point_cls.SERIALIZER.from_json({"x": 1.5, "y": 2.5})
        self.assertEqual(point, point_cls(x=1.5, y=2.5))

    def test_struct_ctor_accepts_mutable_struct(self):
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
        segment_cls = module["Segment"]

    def test_to_frozen_checks_type_of_struct_field(self):
        module = self.init_test_module_classes()
        segment_cls = module["Segment"]
        mutable = segment_cls.Mutable()
        mutable.a = segment_cls.DEFAULT  # Should be a Point
        try:
            mutable.to_frozen()
            self.fail("Expected to fail")
        except Exception as e:
            self.assertIn("Point", str(e))

    def test_struct_ctor_accepts_mutable_list(self):
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
        shape_cls = module["Shape"]
        shape = shape_cls(
            points=[],
        )
        self.assertIs(shape.points, shape_cls(points=[]).points)
        self.assertIs(shape.points, shape.to_mutable().to_frozen().points)
        self.assertIsNot(shape.points, ())

    def test_optional(self):
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
        primary_color_cls = module["PrimaryColor"]
        unknown = primary_color_cls.UNKNOWN
        self.assertEqual(unknown.kind, "?")
        self.assertEqual(unknown.value, None)
        self.assertIs(unknown.union, unknown)
        serializer = primary_color_cls.SERIALIZER
        self.assertEqual(serializer.to_json(unknown), 0)
        self.assertEqual(serializer.to_json(unknown, readable_flavor=True), "?")

    def test_enum_user_defined_constant(self):
        module = self.init_test_module_classes()
        primary_color_cls = module["PrimaryColor"]
        red = primary_color_cls.RED
        self.assertEqual(red.kind, "RED")
        self.assertEqual(red.value, None)
        self.assertIs(red.union, red)
        serializer = primary_color_cls.SERIALIZER
        self.assertEqual(serializer.to_json(red), 10)
        self.assertEqual(serializer.to_json(red, readable_flavor=True), "RED")

    def test_enum_wrap(self):
        module = self.init_test_module_classes()
        status_cls = module["Status"]
        error = status_cls.wrap_error("An error occurred")
        self.assertEqual(error.kind, "error")
        self.assertEqual(error.value, "An error occurred")
        self.assertIs(error.union, error)
        serializer = status_cls.SERIALIZER
        self.assertEqual(serializer.to_json(error), [2, "An error occurred"])
        self.assertEqual(
            serializer.to_json(error, readable_flavor=True),
            {"kind": "error", "value": "An error occurred"},
        )

    def test_enum_wrap_around_mutable_struct(self):
        module = self.init_test_module_classes()
        json_value_cls = module["JsonValue"]
        json_object_cls = json_value_cls.Object
        json_object = json_value_cls.wrap_object(json_object_cls().to_mutable())
        self.assertEqual(json_object.kind, "object")
        self.assertEqual(json_object.value, json_object_cls.DEFAULT)
        self.assertEqual(
            json_object, json_value_cls.wrap_object(json_object_cls.DEFAULT)
        )

    def test_class_name(self):
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
        primary_color_cls = module["PrimaryColor"]
        parent_cls = module["Parent"]
        nested_enum_cls = parent_cls.NestedEnum
        self.assertEqual(repr(primary_color_cls.UNKNOWN), "PrimaryColor.UNKNOWN")
        self.assertEqual(repr(primary_color_cls.RED), "PrimaryColor.RED")
        self.assertEqual(repr(nested_enum_cls.UNKNOWN), "Parent.NestedEnum.UNKNOWN")

    def test_enum_value_repr(self):
        module = self.init_test_module_classes()
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
        json_value_cls = self.init_test_module_classes()["JsonValue"]
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
        module = self.init_test_module_classes()
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
        name_overrides_cls = self.init_test_module_classes()["Stuff"].NameOverrides
        name_overrides = name_overrides_cls(y=3)
        self.assertEqual(name_overrides.y, 3)
        self.assertEqual(name_overrides_cls.__name__, "NameOverrides")
        self.assertEqual(name_overrides_cls.__qualname__, "Stuff.NameOverrides")

    def test_mutable_getter_of_struct(self):
        module = self.init_test_module_classes()
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
        module = self.init_test_module_classes()
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
