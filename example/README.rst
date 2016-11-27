=====================
Fill PDF Form Example
=====================

This directory contains a full example of how to create a JSON template to
fill in data on a PDF document.

Given your base PDF document and JSON data, you can invoke like this::

    python ../filler.py --base-form=source.pdf --form-data=example.json \
        --output-file=filled_form.pdf --preview

The optional ``--extra-data`` argument solves the problem of completing many
forms containing common information with personalized differences. The data
common to all forms may be inserted into the ``extra-data`` file while the
individualized per-form data is in the ``example.json`` file.

If the optional ``--preview`` argument present, the text background will be
colored. This is helpful for positioning.

