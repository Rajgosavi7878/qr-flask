from flask import Flask, request, jsonify, render_template, send_file
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from qrcode import QRCode
import random
import matplotlib.colors as mcolors
import validators

app = Flask(__name__)

def get_random_border_color():
    return random.choice(list(mcolors.CSS4_COLORS.values()))

def add_border_to_qr(img, border_color):
    border_size = 30
    img = img.convert("RGB")
    new_img = Image.new("RGB", (img.size[0] + 2*border_size, img.size[1] + 2*border_size), border_color)
    new_img.paste(img, (border_size, border_size))
    return new_img

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    url = request.form.get('url', '').strip()
    custom_text = request.form.get('custom_text', '').strip()
    logo_file = request.files.get('logo', None)

    if not url:
        return jsonify({'error': 'URL is required'}), 400
    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), 400

    try:
        fg_color = "black"
        bg_color = "white"
        border_color = get_random_border_color()

        qr = QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fg_color, back_color=bg_color)
        img = add_border_to_qr(img, border_color)

        img_with_text = Image.new('RGB', (img.size[0], img.size[1] + 100), color="lightblue")
        img_with_text.paste(img, (0, 0))

        if custom_text:
            try:
                font = ImageFont.truetype("Arial.ttf", size=40)
            except IOError:
                font = ImageFont.load_default()
            draw = ImageDraw.Draw(img_with_text)
            text_width = draw.textlength(custom_text, font=font)
            text_position = ((img_with_text.size[0] - text_width) // 2, img.size[1] + 20)
            draw.text(text_position, custom_text, font=font, fill=fg_color)

        final_image = img_with_text

        if logo_file:
            logo = Image.open(logo_file.stream).convert("RGBA")
            logo_size = min(img.size[0], img.size[1]) // 5
            logo = logo.resize((logo_size, logo_size))

            mask = Image.new("L", (logo_size, logo_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, logo_size, logo_size), fill=255)
            logo.putalpha(mask)

            logo_position = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
            final_image.paste(logo, logo_position, mask=logo)

        buffer = BytesIO()
        final_image.save(buffer, format='PNG')
        buffer.seek(0)

        return send_file(buffer, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
