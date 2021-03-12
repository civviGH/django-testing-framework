
import django

django.setup()

from django.test import TestCase

from dtf.templatetags.dtf.custom_filters import create_html_representation

class ValueHtmlRepresentationTestCase(TestCase):

    def test_none(self):
        result = create_html_representation(None, None)
        self.assertEqual(result, "None")

    def test_integer(self):
        result = create_html_representation(123, 'integer')
        self.assertEqual(result, "123")

    def test_float(self):
        result = create_html_representation(1.23, 'float')
        self.assertEqual(result, "1.23")

        result = create_html_representation(1.234567891011121314e-9, 'float')
        self.assertEqual(result, "1.2345678910111213e-09")

    def test_float(self):
        result = create_html_representation(1.23, 'float')
        self.assertEqual(result, "1.23")

        result = create_html_representation(1.234567891011121314e-9, 'float')
        self.assertEqual(result, "1.2345678910111213e-09")

    def test_image(self):
        image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAVSURBVBhXY2BQ+/+fAQj+//9V8B8AJIUGjCXQWGcAAAAASUVORK5CYII="
        result = create_html_representation(image_base64, 'image')
        self.assertEqual(result, f"<img src='data:image/png;base64, {image_base64}' />")

    def test_ndarray_vector(self):
        data = {
            "shape" : [ 2 ],
            "entries" : [
                { "data" : 1.0, "type" : "float" },
                { "data" : 2.0, "type" : "float" },
            ]
        }
        result = create_html_representation(data, 'ndarray')
        self.assertEqual(result,
         '<table class="ndarray-value">'
         '<tr><td>1.0</td></tr>'
         '<tr><td>2.0</td></tr>'
         '</table>')

    def test_ndarray_matrix(self):
        data = {
            "shape" : [ 2, 3 ],
            "entries" : [
                { "data" : 1.0, "type" : "float" },
                { "data" : 2.0, "type" : "float" },
                { "data" : 3.0, "type" : "float" },
                { "data" : 4.0, "type" : "float" },
                { "data" : 5.0, "type" : "float" },
                { "data" : 6.0, "type" : "float" },
            ]
        }
        result = create_html_representation(data, 'ndarray')
        self.assertEqual(result,
         '<table class="ndarray-value">'
         '<tr><td>1.0</td><td>2.0</td><td>3.0</td></tr>'
         '<tr><td>4.0</td><td>5.0</td><td>6.0</td></tr>'
         '</table>')

    def test_ndarray_tensor_3(self):
        data = {
            "shape" : [ 2, 2, 2 ],
            "entries" : [
                { "data" : 1.0, "type" : "float" },
                { "data" : 2.0, "type" : "float" },
                { "data" : 3.0, "type" : "float" },
                { "data" : 4.0, "type" : "float" },
                { "data" : 5.0, "type" : "float" },
                { "data" : 6.0, "type" : "float" },
                { "data" : 7.0, "type" : "float" },
                { "data" : 8.0, "type" : "float" },
            ]
        }
        result = create_html_representation(data, 'ndarray')
        self.assertEqual(result,
         '<table class="ndarray-value">'
         '<tr><td>1.0</td><td>2.0</td></tr>'
         '<tr><td>3.0</td><td>4.0</td></tr>'
         '</table>'
         '<table class="ndarray-value">'
         '<tr><td>5.0</td><td>6.0</td></tr>'
         '<tr><td>7.0</td><td>8.0</td></tr>'
         '</table>')

    def test_ndarray_tensor_4(self):
        data = {
            "shape" : [ 2, 2, 2, 2 ],
            "entries" : [
                { "data" : 1.0, "type" : "float" },
                { "data" : 2.0, "type" : "float" },
                { "data" : 3.0, "type" : "float" },
                { "data" : 4.0, "type" : "float" },
                { "data" : 5.0, "type" : "float" },
                { "data" : 6.0, "type" : "float" },
                { "data" : 7.0, "type" : "float" },
                { "data" : 8.0, "type" : "float" },
                { "data" : 9.0, "type" : "float" },
                { "data" : 10.0, "type" : "float" },
                { "data" : 11.0, "type" : "float" },
                { "data" : 12.0, "type" : "float" },
                { "data" : 13.0, "type" : "float" },
                { "data" : 14.0, "type" : "float" },
                { "data" : 15.0, "type" : "float" },
                { "data" : 16.0, "type" : "float" },
            ]
        }
        result = create_html_representation(data, 'ndarray')
        self.assertEqual(result,
        'Tensor-4 [2, 2, 2, 2]:'
         '<table class="ndarray-value">'
         '<tr><td>1.0</td></tr>'
         '<tr><td>2.0</td></tr>'
         '<tr><td>3.0</td></tr>'
         '<tr><td>4.0</td></tr>'
         '<tr><td>5.0</td></tr>'
         '<tr><td>6.0</td></tr>'
         '<tr><td>7.0</td></tr>'
         '<tr><td>8.0</td></tr>'
         '<tr><td>9.0</td></tr>'
         '<tr><td>10.0</td></tr>'
         '<tr><td>11.0</td></tr>'
         '<tr><td>12.0</td></tr>'
         '<tr><td>13.0</td></tr>'
         '<tr><td>14.0</td></tr>'
         '<tr><td>15.0</td></tr>'
         '<tr><td>16.0</td></tr>'
         '</table>')

    def test_ndarray_invalid(self):
        data = {
            "shape" : [ 2, 3 ],
            "entries" : [
                { "data" : 1.0, "type" : "float" },
                { "data" : 2.0, "type" : "float" },
                { "data" : 3.0, "type" : "float" },
                { "data" : 4.0, "type" : "float" },
                # Missing two values
            ]
        }
        result = create_html_representation(data, 'ndarray')
        self.assertEqual(result,
        'Tensor-2 [2, 3]:'
         '<table class="ndarray-value">'
         '<tr><td>1.0</td></tr>'
         '<tr><td>2.0</td></tr>'
         '<tr><td>3.0</td></tr>'
         '<tr><td>4.0</td></tr>'
         '</table>')

    def test_list(self):
        result = create_html_representation(str([1.0, 2.0, 3.0]), 'list')
        result = "".join(result.split()) # remove all whitespace
        self.assertEqual(result, "1.0<br>2.0<br>3.0")
