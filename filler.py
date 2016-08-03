import json
from pprint import pprint
import argparse
import sys

# An attempt at Python2/Python3 compat.
try:
    from StringIO import StringIO as CharIO
except ImportError:
    from io import BytesIO as CharIO

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'

class FormRenderer(object):
    """
    Render JSON defined fields on PDF document.
    """

    def __init__(self, base_form, form_data_file, output_file,
            extra_data_file=None, preview=None):
        # XXX: We don't validate these files...
        self.base_form = base_form
        self.output_file = output_file
        self.preview = preview

        with open(form_data_file) as f:
            form_data = json.load(f)
        if extra_data_file:
            with open(extra_data_file) as f:
                extra_data = json.load(f)

        self.fields = [x for x in form_data]
        if extra_data_file:
            self.fields += extra_data

        self.fields.sort(key=lambda x: x['page'], reverse=False)

    def render(self):
        """
        Render text on PDF document.
        """
        with open(self.base_form, 'rb') as f:
            self.docbuf = CharIO(f.read())
        self.overlaybuf = CharIO()
        self.filledbuf = CharIO()
        self.form = PdfFileReader(self.docbuf) #.getPage(0)
        self.pages = self.form.getNumPages()
        self.pagesize = self.form.getPage(0).mediaBox.upperRight
        self.overlay = canvas.Canvas(self.overlaybuf, pagesize=self.pagesize)
        fields = [x for x in self.fields]

        for page_num in range(1, self.pages+1):
            for i, field in enumerate(fields):
                # Do not consider fields that belong to subsequent pages.
                if field['page'] > page_num or field['page'] < page_num:
                    break

                # Get correct coordinates at which to draw text.
                draw_point = self.calculate_draw_point(field)

                # Render field on current canvas page.
                self.render_field(field, draw_point)

            # Remove fields that have already been placed on page.
            fields = fields[i:]

            # Next page
            self.overlay.showPage()

        self.overlay.save()
        self.overlaybuf.seek(0)
        self.final = PdfFileReader(self.overlaybuf)
        self.output = PdfFileWriter()

        # Merge text overlay pages onto original document pages.
        for i in range(self.pages):
            page = self.form.getPage(i)
            page.mergePage(self.final.getPage(i))
            self.output.addPage(page)

        # Write to buffer and write to file.
        self.output.write(self.filledbuf)
        self.write_to_file(self.output_file)

    def write_to_file(self, filename):
        """
        Write the completed PDF to file.
        """
        # XXX No error checkinng on the write...
        output_file = open(filename, 'wb')
        output_file.write(self.filledbuf.getvalue())
        output_file.close()

    def render_field(self, field, draw_point):
        """
        Render text or image field.
        """
        if self.preview:
            self.render_preview_box(field)
        if (field['type'] == "image"):
            draw_fnct=self.render_image
        if (field['type'] == "text"):
            draw_fnct=self.render_text
        draw_fnct(field, draw_point)

    def render_image(self, field, draw_point):
        """
        Render image field.
        """
        x, y = draw_point
        width = field['width']
        height = field['height']

        # TODO: validate file?
        img_file = field['data']
        self.overlay.drawImage(img_file, x, y, width, height,
                preserveAspectRatio=True)

    def render_text(self, field, draw_point):
        """
        Resolve the field value and draw left, right, or center.
        """
        x, y = draw_point

        # Support 'data' and 'text' attributes. Preference for 'data'.
        if 'data' in field:
            field_value = field['data']
        else:
            field_value = field['text']

        self.overlay.setFont(field['font_face'], int(field['font_size']))

        # Always vertically center text within field.
        field_height = float(field['height'])
        font_face = pdfmetrics.getFont(field['font_face']).face
        font_size = float(field['font_size'])
        ascent = (font_face.ascent * font_size) / 1000.0
        voffset = (field_height - ascent) / 2
        y += voffset

        # Shrink text by 1 character until it fits.
        # XXX: Danger, this will result if a single char won't fit.
        while (pdfmetrics.stringWidth(field_value, field['font_face'],
                field['font_size']) > float(field['width'])):
            if (len(field_value) > 1):
                field_value = field_value[:len(field_value)-1]
            if (len(field_value) == 1):
                raise Exception("Single character won't fit. You should "
                        "fix that. Stubbornly refusing to continue")

        if field['align_horizontal'] == LEFT:
            self.overlay.drawString(x, y, "{}".format(field_value))

        if field['align_horizontal'] == RIGHT:
            self.overlay.drawRightString(x, y, "{}".format(field_value))

        if field['align_horizontal'] == CENTER:
            self.overlay.drawCentredString(x, y, "{}".format(field_value))

    def render_preview_box(self, field):
        x, y = float(field['x']), float(field['y'])
        field_width, field_height = float(field['width']), float(field['height'])
        canvas = self.overlay

        red, green, blue = (0x20, 0xF0, 0x90,)
        red = float(red) / 255
        green = float(green) / 255
        blue = float(blue) / 255

        canvas.setFillColorRGB(red, green, blue)
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(0.5)
        canvas.rect(x, y, field_width, field_height, fill=1)
        canvas.setFillColorRGB(0, 0, 0)

    def calculate_draw_point(self, field):
        """
        Calculate correct coordinates to draw text.
        """
        x = float(field['x'])
        y = float(field['y'])

        if field['align_horizontal'] == RIGHT:
            x += float(field['width'])

        if field['align_horizontal'] == CENTER:
            x += float(field['width']) / 2

        return (x, y)


class FormArgumentParser(argparse.ArgumentParser):
    """
    Custom argparser.
    """
    def error(self, message):
        sys.stderr.write('error: {}\n'.format(message))
        self.print_help()
        sys.exit(2)


def usage_message(parser):
    """
    Print a message and exit.
    """
    sys.stderr.write("error: Missing required arguments.\n")
    parser.print_help()
    sys.exit(3)


def main():
    """
    Parse command-line arguments. Process form.
    """
    parser = FormArgumentParser()
    parser.add_argument("-f", "--base-form",
            help="The form to which the data will be applied.")
    parser.add_argument("-d", "--form-data",
            help="Data to be applied to the form.")
    parser.add_argument("-e", "--extra-data",
            help="Extra data to be applied to the form.")
    parser.add_argument("-o", "--output-file",
            help="Write completed form to this file.")
    parser.add_argument("-p", "--preview", action='store_true',
            help="Background coloring to help position fields.")
    args = parser.parse_args()

    # Let extra-data be optional. The remainder cannot be optional.
    for arg in [args.base_form, args.form_data, args.output_file]:
        if not arg:
            usage_message(parser)

    renderer = FormRenderer(args.base_form, args.form_data, args.output_file,
            args.extra_data, args.preview)
    renderer.render()


if __name__ == "__main__":
    main()
