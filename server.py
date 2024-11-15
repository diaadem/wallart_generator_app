from flask import Flask, request, jsonify, render_template, session
import base64
import requests
from PIL import Image
import IPython
import os
import openai
import io
import json
from flask_cors import CORS
import time
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client

app = Flask(__name__)
CORS(app)

print(os.urandom(24))

#ENTER IN KEYS
app.secret_key = "you flask key"
api_key = "your OpenAI key"
openai.api_key = "your OpenAI key"
STABILITY_KEY = "your Stability AI key"

def send_generation_request(
        host,
        params,
):
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"
    }

    files = {}
    image = params.pop("image", None)
    mask = params.pop("mask", None)
    if image is not None and image != '':
        files["image"] = open(image, 'rb')
    if mask is not None and mask != '':
        files["mask"] = open(mask, 'rb')
    if len(files) == 0:
        files["none"] = ''

    print(f"Sending REST request to {host}...")
    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    return response


def send_async_generation_request(
        host,
        params,
):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {STABILITY_KEY}"
    }

    files = {}
    if "image" in params:
        image = params.pop("image")
        files = {"image": open(image, 'rb')}

    print(f"Sending REST request to {host}...")
    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    response_dict = json.loads(response.text)
    generation_id = response_dict.get("id", None)
    assert generation_id is not None, "Expected id in response"

    timeout = int(os.getenv("WORKER_TIMEOUT", 500))
    start = time.time()
    status_code = 202
    while status_code == 202:
        response = requests.get(
            f"{host}/result/{generation_id}",
            headers={
                **headers,
                "Accept": "image/*"
            },
        )

        if not response.ok:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        status_code = response.status_code
        time.sleep(10)
        if time.time() - start > timeout:
            raise Exception(f"Timeout after {timeout} seconds")

    return response


def resize_image(image, max_size=(800, 800)):
    with Image.open(image) as img:
        img.thumbnail(max_size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def encode_image(image_path):
    with open(image_path, "rb") as image:
        return base64.b64encode(image.read()).decode('utf-8')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
    image_file.save(image_path)

    absolute_image_path = os.path.abspath(image_path)
    base64_image = encode_image(absolute_image_path)

    # Get the room description and store it in session
    room_description = get_room_description(base64_image)
    if not room_description:
        return jsonify({"error": "Failed to generate room description"}), 500

    # store both room description/color analysis in session
    if isinstance(room_description, tuple):
        description_text = room_description[0]
        session['room_description'] = description_text
        session['color_analysis'] = description_text
    else:
        session['room_description'] = room_description
        session['color_analysis'] = room_description

    return jsonify({"color_analysis": session['color_analysis']}), 200


def get_room_description(base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text":
                            "Please analyze this room image and provide: \n"
                            "1. EXISTING COLORS\n"
                            "List the dominant colors in the room (walls, furniture, flooring)\n"
                            "Include both color names and hex codes\n"
                            "Note the approximate proportion of each color\n"
                            "Identify the undertones (warm/cool) of the main colors\n"
                            "2. COLOR RELATIONSHIPS\n"
                            "Identify the current color scheme (complementary, analogous, etc.)\n"
                            "Note which colors are serving as:\n"
                            "Dominant colors (60%)\n"
                            "Secondary colors (30%)\n"
                            "Accent colors (10%)\n"
                            "3. ARTWORK COLOR RECOMMENDATIONS\n"
                            "Suggest 3-4 color palettes that would complement the room, including:\n"
                            "Primary colors for the artwork\n"
                            "Accent colors that would create visual interest\n"
                            "Both bold and subtle options\n"
                            "Provide hex codes for each suggested color\n"
                            "Explain why each palette would work well with the existing room colors\n"
                            "4. PLACEMENT CONSIDERATIONS\n"
                            "- Note any areas where lighting might affect color perception\n"
                            "- Suggest which walls or areas would best showcase artwork in these colors\n"
                            "- Consider how the suggested colors will interact with natural and artificial lighting\n"
                            "Please provide specific color names and hex codes for all recommendations to ensure accuracy."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        text_response = response.json()
        return text_response["choices"][0]["message"]["content"].strip(), 200
    except requests.RequestException as e:
        print(f"Error fetching room description: {e}")
        return None


def generate_art_prompts(room_description, user_preferences=None):
    try:
        styles_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI interior design assistant."},
                {"role": "user", "content": f"""User preferences: {user_preferences}\n"
                        "Using the color palette analysis provided:\n"
                        f"{room_description}\n"
                        "please generate 6 art concepts prompts for stable diffusion AI that would work with the room:\n\n"
                        "Example:\n\n"
                        "ABSTRACT GEOMETRIC\n\n"
                        "CopyPrompt structure:\n"
                        "A high-end abstract geometric artwork featuring [primary color] and [secondary color] shapes, "
                        "with accents of [accent color]. Include [geometric elements] arranged in a [composition style].\n"
                        "Style: minimalist, precise, clean lines\n"
                         """
                 }],
            max_tokens=500,
            temperature=0.1,
        )

        styles_text = styles_response.choices[0].message['content'].strip()
        style_descriptions = styles_text.split("\n\n")

        return style_descriptions[:6]

    except openai.error.OpenAIError as e:
        print(f"Error fetching room styles: {e}")
        return None

# 3. User Selection and Fine Tuning (GPT Prompt 3)
def refine_art_prompts(liked_pieces, disliked_pieces, room_description, user_preferences):
    try:
        styles_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a personalized wall art creator."},
                {"role": "user", "content": f"User likes pieces: {', '.join(liked_pieces)}\n"
                    f"User dislikes pieces: {', '.join(disliked_pieces)}\n"
                    "Does the user want to generate more? Yes\n\n"
                    "If yes: considering the pieces that the user likes and dislikes, "
                    "the color palette analysis provided:\n"
                    f"{room_description}\n"
                    f"and user : {user_preferences}, please generate 3 art concepts prompts for stable diffusion AI that would work with the room:\n\n"
                    "Example:\n\n"
                    "ABSTRACT GEOMETRIC\n\n"
                    "CopyPrompt structure:\n"
                    "A high-end abstract geometric artwork featuring [primary color] and [secondary color] shapes, "
                    "with accents of [accent color]. Include [geometric elements] arranged in a [composition style].\n"
                    "Style: minimalist, precise, clean lines\n"
                    # "Quality tags: masterpiece, high quality, detailed\n"
                    # "Negative prompt: busy, cluttered, realistic, photographic"
                 }],
            max_tokens=500,
            temperature=0.1,
        )

        styles_text = styles_response.choices[0].message['content'].strip()
        style_descriptions = styles_text.split("\n\n")

        return style_descriptions[:3]

    except openai.error.OpenAIError as e:
        print(f"Error fetching room styles: {e}")
        return None

def generate_style_images(style_descriptions):
    images = []
    for description in style_descriptions:
        try:
            prompt = description
            host = "https://api.stability.ai/v2beta/stable-image/generate/core"
            params = {
                "prompt": prompt,
                "seed": 0,
                "output_format": "jpeg"
            }

            response = send_generation_request(host, params)

            output_image = response.content
            seed = response.headers.get("seed", "default_seed")
            generated_image_path = f"static/generated_{seed}.jpeg"

            with open(generated_image_path, "wb") as f:
                f.write(output_image)

            image_url = f"/static/generated_{seed}.jpeg"
            images.append({"description": description, "url": image_url})

        except Exception as e:
            print(f"Error generating image for style '{description}': {e}")
            continue

    return images

@app.route('/generate_art', methods=['POST'])
def generate_art():
    user_preferences = request.json.get('preferences')
    room_description = session.get('room_description')  # Just get room_description once

    # run prompt generation w/ room description
    prompts = generate_art_prompts(room_description, user_preferences)
    art_images = generate_art_images(prompts)

    return jsonify(art_images)

@app.route('/refine_art', methods=['POST'])
def refine_art():
    liked_pieces = request.json.get('liked_pieces', [])
    disliked_pieces = request.json.get('disliked_pieces', [])
    user_preferences = request.json.get('preferences', '')
    room_description = session.get('room_description')

    if not room_description:
        return jsonify({"error": "Please upload an image first"}), 400

    # storing liked pieces in session (if provided)
    if liked_pieces:
        session['liked_pieces'] = liked_pieces
        print(f"Liked pieces stored in session: {liked_pieces}")
    else:
        liked_pieces = session.get('liked_pieces', [])
        print(f"Liked pieces retrieved from session: {liked_pieces}")

    if disliked_pieces:
        session['disliked_pieces'] = disliked_pieces
        print(f"Disliked pieces stored in session: {disliked_pieces}")
    else:
        disliked_pieces = session.get('disliked_pieces', [])
        print(f"Disliked pieces retrieved from session: {disliked_pieces}")

    # generate refined prompts using the room description
    refined_prompts = refine_art_prompts(liked_pieces, disliked_pieces, room_description, user_preferences)
    if not refined_prompts:
        return jsonify({"error": "Failed to generate refined art prompts"}), 500

    # generate images for the refined prompts
    refined_images = generate_art_images(refined_prompts)
    if not refined_images:
        return jsonify({"error": "Failed to generate images for refined prompts"}), 500

    return jsonify(refined_images), 200

def generate_art_images(prompts):
    images = []
    for description in prompts:
        try:
            prompt = description
            host = "https://api.stability.ai/v2beta/stable-image/generate/core"
            params = {
                "prompt": prompt,
                "seed": 0,
                "output_format": "jpeg"
            }

            response = send_generation_request(host, params)
            output_image = response.content
            seed = response.headers.get("seed", "default_seed")
            generated_image_path = f"static/generated_{seed}.jpeg"

            with open(generated_image_path, "wb") as f:
                f.write(output_image)

            image_url = f"/static/generated_{seed}.jpeg"
            images.append({"description": description, "url": image_url})

        except Exception as e:
            print(f"Error generating image for style '{description}': {e}")
            continue

    return images

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)