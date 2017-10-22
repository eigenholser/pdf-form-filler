=====================
Fill PDF Form Example
=====================

This directory contains a full example of how to create a JSON template to
fill in data on a PDF document.

Given the source PDF document and JSON data, invoke like this::

    python ../filler.py --base-form=source.pdf --form-data=example.json \
        --extra-data=extra.json --output-file=filled_form.pdf --preview

The optional ``--extra-data`` argument solves the problem of completing many
forms containing common information with personalized differences. The data
common to all forms may be inserted into the ``extra-data`` file while the
individualized per-form data is in the ``example.json`` file.

If the optional ``--preview`` argument present, the text background will be
colored. This is helpful for positioning.

-----------------------------
Creating A Blank PDF Document
-----------------------------

Start by making a minimal PostScript document::

    %!PS
    showpage

That's it. You can preview it using GhostScript::

    $ gs source.ps

It will display a blank page. Add additional pages by adding more ``showpage``
lines.

Convert to PDF using ``ps2pdf``::

    $ ps2pdf source.ps

You will now have a file called ``source.pdf`` to play with. It will consist
of a single blank page.

