"""
Test for Foo
"""
from mock import mock_open, patch
import pytest
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from filler import FormRenderer

@pytest.fixture
def form_data():
    return """
    [
        {
            "comment": "This thing.",
            "page": 1,
            "x": 137,
            "y": 111,
            "type": "text",
            "width": 400,
            "height": 50,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 24,
            "font_color": "0000FF",
            "rotation": 0,
            "data": "This Thing"
        },
        {
            "comment": "That thing.",
            "page": 2,
            "x": 337,
            "y": 511,
            "type": "image",
            "width": 100,
            "height": 100,
            "align_horizontal": "right",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 14,
            "font_color": "000000",
            "rotation": 45,
            "data": "image.jpg"
        }
    ] """

class TestFormRendererInitialization(object):
    """
    Class instantiation tests.
    """

    def test_basic_attrs(self, form_data):
        """
        Test basic attributes.
        """
        base_form = "base_form.pdf"
        output_file = "output_file.pdf"

        mo = mock_open(read_data=form_data)
        with patch('builtins.open', mo, create=True):
            fr = FormRenderer(base_form, form_data, output_file)
            assert fr.base_form == base_form
            assert fr.output_file == output_file
            assert fr.preview == None

    def test_form_data(self, form_data):
        """
        Test form data. Read form data. Confirm identical.
        """
        mo = mock_open(read_data=form_data)
        with patch('builtins.open', mo, create=True):
            fr = FormRenderer("base_form.pdf", "form_data.json",
                    "output_form.pdf")
            data = json.loads(form_data)
            fields = [x for x in data]
            fields.sort(key=lambda x: x['page'], reverse=False)
            assert fr.fields == fields

    def test_extra_data(self, form_data):
        """
        Test extra data. Combine form data and extra data. Confirm identical.
        """
        mo = mock_open(read_data=form_data)
        with patch('builtins.open', mo, create=True):
            fr = FormRenderer("base_form.pdf", "form_data.json",
                    "output_form.pdf", "extra_data.json")
            data = json.loads(form_data)
            fields = [x for x in data] + [x for x in data]
            fields.sort(key=lambda x: x['page'], reverse=False)
            assert fr.fields == fields

