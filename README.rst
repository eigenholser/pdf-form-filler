=============
Fill PDF Form
=============

Fill a PDF form with text data supplied in JSON file. Of course, the PDF
document does not need to be a form but that was the original premise. It can
be any PDF document for which you want to place text data.

The data is written to the PDF document supplied. Multi-page PDF documents
are supported. The meta data requires the page number to be supplied.

------------
Dependencies
------------

On Ubuntu 16.04 install ``libjpeg-dev``::

    sudo apt install libjpeg-dev


------------
Installation
------------

Clone the repository. Create a Python virtual environment. This program may
work with Python 2::

    cd pdf-form-filler
    mkvirtualenv --python=/usr/bin/python3 pdf-form-filler
    setvirtualenvproject
    pip install -r requirements/install.txt

Given your base PDF document and JSON data, you can invoke like this::

    python filler.py --base-form=myform.pdf --form-data=form_data.json \
        --extra-data=extra_data.json --output-file=filled_form.pdf \
        --preview

The optional ``--extra-data`` argument solves the problem of completing many
forms containing common information with personalized differences. The data
common to all forms may be inserted into the ``extra-data`` file while the
individualized per-form data is in the ``form-data`` file.

If the optional ``--preview`` argument present, the text background will be
colored. This is helpful for positioning.


----------------------
Structure of JSON Data
----------------------

The JSON data is an array of objects, each representing a field. Each JSON
object in the array contains all the data needed to position the field. Not
all attributes are meaningful within the ``type`` context. For instance, font
attributes are ignored for image field types::

    [
        {
            "comment": "Text type",
            "page": 1,
            "x": 337,
            "y": 711,
            "type": "text",
            "width": 10,
            "height": 10,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 14,
            "font_color": "0000FF",
            "rotation": 90,
            "data": "This Thing"
        },
        {
            "comment": "Image type",
            "page": 2,
            "x": 337,
            "y": 611,
            "type": "image",
            "width": 10,
            "height": 10,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 14,
            "font_color": "000000",
            "rotation": 90,
            "data": "/path/to/image.png"
        }
        {
            "comment": "Outline type",
            "page": 3,
            "x": 50,
            "y": 30,
            "type": "outline",
            "width": 235,
            "height": 408,
            "line_width": 3,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 14,
            "font_color": "000000",
            "rotation": 0,
            "data": ""
        },
        {
            "comment": "Line type",
            "page": 4,
            "x": 50,
            "y": 30,
            "type": "line",
            "width": 235,
            "height": 0,
            "line_width": 3,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "",
            "font_size": 0,
            "font_color": "000000",
            "rotation": 0,
            "data": ""
        }
    ]

There are four types of fields: ``text``, ``image``, ``outline``, and ``line``
fields.  If the ``type`` attribute is ``text``, the value of the ``data``
attribute is handled as text data. If the ``type`` attribute is ``image``, the
value of the ``data`` attribute is handled as the path to an image. If the
``type`` attribute is ``outline`` or ``line``, the ``data`` attribute is
ignored.

There are some special considerations for ``line`` type fields. Set ``width``
or ``height`` to zero as needed or the drawn line will be diagonal. Because of
this, the preview box will not be visible.

``TODO:`` Various JSON attributes are ignored for different values of ``type``.
Required attributes for each type should be listed.


-------------
Running Tests
-------------

Install test dependencies::

    $ pip install -r requirements/test.txt

Run PyTest::

    $ pytest

Coverage report will be written to ``htmlcov/index.html``.

----------
References
----------

1. `ReportLab User Guide (PDF) <http://meteorite.unm.edu/site_media/pdf/reportlab-userguide.pdf>`_

