import unittest

from soialib import (
    Timestamp,
    array_serializer,
    optional_serializer,
    primitive_serializer,
)


class TimestampTestCase(unittest.TestCase):
    def test_primitive_serializers(self):
        self.assertEqual(primitive_serializer("bool").to_json_code(True), "1")
        self.assertEqual(
            primitive_serializer("bool").to_json_code(True, readable=True),
            "true",
        )
        self.assertEqual(primitive_serializer("bool").from_json_code("true"), True)
        self.assertEqual(primitive_serializer("bool").from_json_code("false"), False)
        self.assertEqual(primitive_serializer("bool").from_json_code("0"), False)

        self.assertEqual(primitive_serializer("int32").to_json_code(7), "7")
        self.assertEqual(
            primitive_serializer("int32").to_json_code(7, readable=True), "7"
        )
        self.assertEqual(
            primitive_serializer("int32").to_json_code(2147483648), "2147483647"
        )
        self.assertEqual(
            primitive_serializer("int32").to_json_code(-2147483649), "-2147483648"
        )
        self.assertEqual(primitive_serializer("int32").from_json_code("0"), 0)
        self.assertEqual(primitive_serializer("int32").from_json_code('"7"'), 7)
        self.assertEqual(primitive_serializer("int32").from_json_code("3.14"), 3)
        self.assertEqual(primitive_serializer("int32").from_json_code("-3.14"), -3)

        self.assertEqual(
            primitive_serializer("int64").to_json_code(2147483648), "2147483648"
        )
        self.assertEqual(
            primitive_serializer("int64").to_json_code(9007199254740991),
            "9007199254740991",
        )
        self.assertEqual(
            primitive_serializer("int64").to_json_code(9007199254740992),
            '"9007199254740992"',
        )
        self.assertEqual(
            primitive_serializer("int64").to_json_code(9223372036854775808),
            '"9223372036854775807"',
        )
        self.assertEqual(
            primitive_serializer("int64").to_json_code(-9007199254740991),
            "-9007199254740991",
        )
        self.assertEqual(
            primitive_serializer("int64").to_json_code(-9007199254740992),
            '"-9007199254740992"',
        )
        self.assertEqual(
            primitive_serializer("int64").to_json_code(-9223372036854775809),
            '"-9223372036854775808"',
        )
        self.assertEqual(primitive_serializer("int64").from_json_code("0"), 0)
        self.assertEqual(primitive_serializer("int64").from_json_code('"7"'), 7)
        self.assertEqual(primitive_serializer("int64").from_json_code("3.14"), 3)
        self.assertEqual(primitive_serializer("int64").from_json_code("-3.14"), -3)

        self.assertEqual(
            primitive_serializer("uint64").to_json_code(2147483648),
            "2147483648",
        )
        self.assertEqual(
            primitive_serializer("uint64").to_json_code(-1),
            "0",
        )
        self.assertEqual(
            primitive_serializer("uint64").to_json_code(9007199254740991),
            "9007199254740991",
        )
        self.assertEqual(
            primitive_serializer("uint64").to_json_code(9007199254740992),
            '"9007199254740992"',
        )
        self.assertEqual(primitive_serializer("uint64").from_json_code("0"), 0)
        self.assertEqual(primitive_serializer("uint64").from_json_code('"7"'), 7)
        self.assertEqual(primitive_serializer("uint64").from_json_code("3.14"), 3)
        self.assertEqual(primitive_serializer("uint64").from_json_code("-3.14"), -3)

        self.assertEqual(primitive_serializer("float32").to_json_code(3.14), "3.14")
        self.assertEqual(
            primitive_serializer("float32").to_json_code(float("inf")), "Infinity"
        )
        self.assertEqual(
            primitive_serializer("float32").to_json_code(-float("inf")), "-Infinity"
        )
        self.assertEqual(
            primitive_serializer("float32").to_json_code(float("nan")), "NaN"
        )
        self.assertEqual(primitive_serializer("float64").to_json_code(3.14), "3.14")
        self.assertEqual(
            primitive_serializer("float64").to_json_code(3.14, readable=True),
            "3.14",
        )

        self.assertEqual(
            primitive_serializer("timestamp").to_json_code(
                Timestamp.from_unix_millis(3)
            ),
            "3",
        )
        self.assertEqual(
            primitive_serializer("timestamp").to_json_code(
                Timestamp.from_unix_millis(3), readable=True
            ),
            '{\n  "unix_millis": 3,\n  "formatted": "1970-01-01T00:00:00.003000Z"\n}',
        )
        self.assertEqual(
            primitive_serializer("timestamp").from_json_code("3"),
            Timestamp.from_unix_millis(3),
        )
        self.assertEqual(
            primitive_serializer("timestamp").from_json_code(
                '{\n  "unix_millis": 3,\n  "formatted": "FOO",\n  "bar": true\n}'
            ),
            Timestamp.from_unix_millis(3),
        )

    def test_array_serializer(self):
        self.assertEqual(
            array_serializer(primitive_serializer("bool")).to_json_code((True, False)),
            "[1,0]",
        )
        self.assertEqual(
            array_serializer(primitive_serializer("bool")).to_json_code(
                (True, False), readable=True
            ),
            "[\n  true,\n  false\n]",
        )

    def test_optional_serializer(self):
        self.assertEqual(
            optional_serializer(primitive_serializer("bool")).to_json_code(True),
            "1",
        )
        self.assertEqual(
            optional_serializer(primitive_serializer("bool")).to_json_code(
                True, readable=True
            ),
            "true",
        )
        self.assertEqual(
            optional_serializer(primitive_serializer("bool")).to_json_code(None),
            "null",
        )
