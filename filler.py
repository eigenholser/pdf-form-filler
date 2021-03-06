import json
from pprint import pprint
import argparse
from math import sin, cos
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
PREVIEW_COLOR = (0x20, 0xF0, 0x90,)
PI = 3.14159

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
        self.form = PdfFileReader(self.docbuf, strict=False) #.getPage(0)
        self.pages = self.form.getNumPages()
        self.pagesize = self.form.getPage(0).mediaBox.upperRight
        self.overlay = canvas.Canvas(self.overlaybuf, pagesize=self.pagesize)
        fields = [x for x in self.fields]

        for page_num in range(1, self.pages+1):
            for i, field in enumerate(fields):
                # Do not consider fields that belong to subsequent pages.
                if field['page'] > page_num or field['page'] < page_num:
                    break

                # Render field on current canvas page.
                self.render_field(field)

            # Remove fields that have already been placed on page.
            fields = fields[i:]

            # Next page
            self.overlay.showPage()

        self.overlay.save()
        self.overlaybuf.seek(0)
        self.final = PdfFileReader(self.overlaybuf, strict=False)
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

    def render_field(self, field):
        """
        Render text or image field.
        """
        if self.preview:
            self.render_preview_box(field)
        if (field.get('type', 'text') == "image"):
            draw_point = self.calculate_image_draw_point(field)
            draw_fnct = self.render_image
        if (field.get('type', 'text') == "text"):
            draw_point = self.calculate_text_draw_point(field)
            draw_fnct = self.render_text
        if (field.get('type', 'text') == "outline"):
            draw_point = self.calculate_image_draw_point(field)
            draw_fnct = self.render_outline
        if (field.get('type', 'text') == "line"):
            draw_point = self.calculate_image_draw_point(field)
            draw_fnct = self.render_line
        draw_fnct(field, draw_point)

    def render_line(self, field, draw_point):
        """
        Render outline rectangle with hard-wired radius.
        """
        c = self.overlay    # Canvas

        x, y = draw_point
        _, _, width, height = self.get_position_and_size(field)
        x2 = x + width
        y2 = y + height

        c.saveState()
        c.translate(x, y)

        if 'rotation' in field:
            c.rotate(int(field['rotation']))

        if 'line_width' in field:
            c.setLineWidth(int(field['line_width']))

        (r, g, b) = self.calculate_rgb_values(field)
        c.setStrokeColorRGB(r, g, b)

        c.line(0, 0, width, height)
        c.restoreState()

    def render_outline(self, field, draw_point):
        """
        Render outline rectangle with hard-wired radius.
        """
        c = self.overlay    # Canvas

        x, y = draw_point
        _, _, width, height = self.get_position_and_size(field)
        radius = 5          # Hard-wired radius.

        c.saveState()
        c.translate(x, y)

        if 'rotation' in field:
            c.rotate(int(field['rotation']))

        if 'line_width' in field:
            c.setLineWidth(int(field['line_width']))

        (r, g, b) = self.calculate_rgb_values(field)
        c.setStrokeColorRGB(r, g, b)

        c.roundRect(0, 0, width, height, radius, stroke=True, fill=False)
        c.restoreState()

    def render_image(self, field, draw_point):
        """
        Render image field.
        """
        c = self.overlay    # Canvas

        x, y = draw_point
        _, _, width, height = self.get_position_and_size(field)

        # TODO: validate file?
        img_file = field['data']
        c.saveState()
        c.translate(x, y)
        if 'rotation' in field:
            c.rotate(int(field['rotation']))
        c.drawImage(img_file, 0, 0, width, height, preserveAspectRatio=True)
        c.restoreState()

    def render_text(self, field, draw_point):
        """
        Resolve the field value and draw left, right, or center.
        """
        c = self.overlay    # Canvas

        x, y = draw_point

        # Support 'data' and 'text' attributes. Preference for 'data'.
        if 'data' in field:
            field_value = field['data']
        else:
            field_value = field['text']

        # Shrink text by 1 character until it fits.
        # XXX: Danger, this will result if a single char won't fit.
        while (pdfmetrics.stringWidth(field_value, field['font_face'],
                field['font_size']) > float(field['width'])):
            if (len(field_value) > 1):
                field_value = field_value[:len(field_value)-1]
            if (len(field_value) == 1):
                raise Exception("Single character won't fit. You should "
                        "fix that. Stubbornly refusing to continue")

        c.saveState()
        c.translate(x, y)

        if 'rotation' in field:
            c.rotate(int(field['rotation']))

        (r, g, b) = self.calculate_rgb_values(field)
        c.setFillColorRGB(r, g, b)

        if field['align_horizontal'] == LEFT:
            c.drawString(0, 0, "{}".format(field_value))

        if field['align_horizontal'] == RIGHT:
            c.drawRightString(0, 0, "{}".format(field_value))

        if field['align_horizontal'] == CENTER:
            c.drawCentredString(0, 0, "{}".format(field_value))

        c.restoreState()

    def render_preview_box(self, field):
        """
        Render the preview box.
        """
        c = self.overlay    # Canvas

        # (x, y), field width, field height
        x, y, width, height = self.get_position_and_size(field)

        red, green, blue = PREVIEW_COLOR
        red = float(red) / 255
        green = float(green) / 255
        blue = float(blue) / 255

        c.saveState()
        c.translate(x, y)
        c.setFillColorRGB(red, green, blue)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        if 'rotation' in field:
            c.rotate(int(field['rotation']))
        c.rect(0, 0, width, height, fill=1)
        c.restoreState()

    def get_position_and_size(self, field):
        """
        Extract position, field width, and field height. Return as tuple.
        """
        # These are all required. If not present, don't handle error.
        x, y = float(field['x']), float(field['y'])
        w, h = float(field['width']), float(field['height'])
        return (x, y, w, h,)

    def calculate_image_draw_point(self, field):
        """
        Calculate correct coordinates to draw image.
        """
        x = float(field['x'])
        y = float(field['y'])

        return (x, y)

    def calculate_text_draw_point(self, field):
        """
        Calculate correct coordinates to draw text.
        """
        c = self.overlay    # Canvas

        x = float(field['x'])
        y = float(field['y'])

        field_height = float(field['height'])
        # Always vertically center text within field.
        c.setFont(field['font_face'], int(field['font_size']))
        font_face = pdfmetrics.getFont(field['font_face']).face
        font_size = float(field['font_size'])
        ascent = (font_face.ascent * font_size) / 1000.0
        voffset = (field_height - ascent) / 2

        # Radians
        rot = 0
        if 'rotation' in field:
            rot += float(field['rotation']) * PI / 180

        xoffset = voffset * sin(rot)
        yoffset = voffset * cos(rot)

        if field['align_horizontal'] == LEFT:
            x -= xoffset
            y += yoffset

        if field['align_horizontal'] == RIGHT:
            x += float(field['width']) * cos(rot) - xoffset
            y += float(field['width']) * sin(rot) + yoffset

        if field['align_horizontal'] == CENTER:
            x += (float(field['width']) / 2) * cos(rot) - xoffset
            y += (float(field['width']) / 2) * sin(rot) + yoffset

        return (x, y)

    def calculate_rgb_values(self, field):
        """
        Calculate R, G, B values from hexadecimal color value if present.
        Default to black.
        """
        (r, g, b,) = (0, 0, 0,)
        if 'font_color' in field:
            color = field['font_color']
            if len(color) != 6:
                raise Exception("Requires hex RGB colors in format 112233.")
            r = int("0x{}".format("".join(list(color)[:2])), 16) / 255.0
            g = int("0x{}".format("".join(list(color)[2:4])), 16) / 255.0
            b = int("0x{}".format("".join(list(color)[4:6])), 16) / 255.0
        return (r, g, b,)


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


if __name__ == "__main__": # pragma: no cover
    main()
