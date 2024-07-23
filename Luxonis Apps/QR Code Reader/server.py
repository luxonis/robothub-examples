"""
    Example server for testing WebReporter node
"""
from flask import Flask, request, jsonify
import base64
import numpy as np
import cv2

app = Flask(__name__)


# Function to decode base64 to a NumPy array image
def decode_image_from_base64(base64_string):
    img_data = base64.b64decode(base64_string)
    np_arr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Extract the base64-encoded image from the JSON payload
    base64_image = data.get('crop_image')

    if base64_image is None:
        return jsonify({'error': 'No image provided'}), 400

    # Decode the image
    image = decode_image_from_base64(base64_image)
    # Save image
    cv2.imwrite('received_image.jpg', image)
    # Show received data
    print(f"Received data:\nlabel: {data.get('label')}\ncode_format: {data.get('code_format')}\ntimestamp: {data.get('timestamp')}\n")
    return jsonify({"status": "success", "data_received": data}), 200


if __name__ == "__main__":
    app.run(port=5000)
