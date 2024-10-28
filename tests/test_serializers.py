import unittest

from soialib import (
    Timestamp,
    array_serializer,
    optional_serializer,
    primitive_serializer,
)


class TimestampTestCase(unittest.TestCase):
    def test_primitive_serializers(self):
        self.assertEqual(primitive_serializer("bool").to_json_code(True), "true")
        self.assertEqual(primitive_serializer("int32").to_json_code(7), "7")
        self.assertEqual(
            primitive_serializer("int64").to_json_code(2147483648), "2147483648"
        )
        self.assertEqual(
            primitive_serializer("uint64").to_json_code(2147483648),
            "2147483648",
        )
        self.assertEqual(primitive_serializer("float32").to_json_code(3.14), "3.14")
        self.assertEqual(primitive_serializer("float64").to_json_code(3.14), "3.14")
        self.assertEqual(
            primitive_serializer("timestamp").to_json_code(
                Timestamp.from_unix_millis(3)
            ),
            "3",
        )
        self.assertEqual(primitive_serializer("string").to_json_code("foo"), '"foo"')
        self.assertEqual(primitive_serializer("bytes").to_json_code(b"foo"), '"666f6f"')

    def test_array_serializer(self):
        self.assertEqual(
            array_serializer(primitive_serializer("bool")).to_json_code([True, False]),
            "[true, false]",
        )

    def test_optional_serializer(self):
        self.assertEqual(
            optional_serializer(primitive_serializer("bool")).to_json_code(True),
            "true",
        )
        self.assertEqual(
            optional_serializer(primitive_serializer("bool")).to_json_code(None),
            "null",
        )
