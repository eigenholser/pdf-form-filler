=============
Fill PDF Form
=============

Fill a PDF form with text data supplied in JSON file. Of course, the PDF
document does not need to be a form but that was the original premise. It can
be any PDF document for which you want to place text data.

The data is written to the PDF document supplied. Multi-page PDF documents
are supported. The meta data requires the page number to be supplied.


------------
Installation
------------

Clone the repository. Create a Python virtual environment. This program may
work with Python 2::

    cd pdf-form-filler
    mkvirtualenv --python=/usr/bin/python3 pdf-form-filler
    setvirtualenvproject
    pip install -r requirements.txt

Given your base PDF document and JSON data, you can invoke like this::

    python filler.py --base-form=myform.pdf --form-data=form_data.json \
        --extra-data=extra_data.json --output-file=filled_form.pdf \
        --preview

The optional `--extra-data` argument solves the problem of completing many
forms containing common information with personalized differences. The data
common to all forms may be inserted into the `extra-data` file while the
individualized per-form data is in the `form-data` file.

If the optional `--preview` argument present, the text background will be
colored. This is helpful for positioning.


----------------------
Structure of JSON Data
----------------------

The JSON data contains one attribute named `fields` that is an array of JSON
objects. Each JSON object in the array contains all the data needed to
position the text, set the font family, font size, and of course, the text to
be placed::

    [
        {
            "comment": "This thing.",
            "page": 1,
            "x": 337,
            "y": 711,
            "width": 10,
            "height": 10,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 14,
            "text": "This Thing"
        },
        {
            "comment": "That thing.",
            "page": 2,
            "x": 337,
            "y": 611,
            "width": 10,
            "height": 10,
            "align_horizontal": "center",
            "align_vertical": "center",
            "font_face": "Courier",
            "font_size": 14,
            "text": "That Thing"
        }
    ]
