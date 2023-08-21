import boto3
import json
import torch
import random
from transformers import pipeline, set_seed
from flask import Flask, render_template, request, jsonify

# Replace 'your-aws-region' with the appropriate AWS region where your S3 bucket is located.
s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = 'qme-noodle-house'
file_key = 'noodlehouse.json'

# Load the GPT-Neo model
generator = pipeline('text-generation', model='EleutherAI/gpt-neo-2.7B',eos_token_id=50256,  device=0)
set_seed(42)

# Add a padding token to the tokenizer
generator.tokenizer.add_special_tokens({'pad_token': '[PAD]'})

dish = ""

def load_menu_data():
    # Load the JSON data from S3
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        menu_data = json.loads(content)
        return menu_data
    except Exception as e:
        print(f"Error reading the S3 file: {e}")
        exit(1)

def tokenize_menu(menu_data):
    # Combine all menu information (category, name, price, ingredients) into a single text
    menu_text = ""
    for item in menu_data:
        menu_text += f"{item['category']} {item['name']} {item['price']} {' '.join(item['ingredients'])} {item['description']} "
    
    # Tokenize the menu text
    menu_tokens = generator.tokenizer(menu_text, return_tensors='pt', padding=True)
    return menu_tokens

def generate_response(user_input, menu_tokens, menu_data):
    # Tokenize the user input
    user_input_tokens = generator.tokenizer(user_input, return_tensors='pt', padding=True)

    # Check if any input token matches any menu token
    matched_tokens = [token for token in user_input_tokens['input_ids'][0] if token in menu_tokens['input_ids'][0]]

    global dish

    if matched_tokens:
        # If matching tokens are found, suggest a relevant menu item
        matched_texts = [generator.tokenizer.decode(token) for token in matched_tokens]
        suggested_items = []
        for item in menu_data:
            item_text = f"{item['category']} {item['name']} {item['price']} {' '.join(item['ingredients'])} {item['description']}"
            if any(text in item_text for text in matched_texts):
                suggested_items.append(item)

        if suggested_items:
            suggested_item = random.choice(suggested_items)
            dish = suggested_item['name']
            response = f"Ok, I guess you would like trying our {suggested_item['name']} from {suggested_item['category']} category. It costs {suggested_item['price']} and contains {', '.join(suggested_item['ingredients'])}. Description: {suggested_item['description']}"
        else:
            response = "I couldn't find an exact match, but I suggest exploring our menu for more options."
    else:
        # If no matching token is found, generate a generic response
        suggested_items = random.sample(menu_data, min(1, len(menu_data)))
        response = "I think you might enjoy trying the following dishe: "
        for item in suggested_items:
            response += f"{item['name']} ({item['category']}), "
            dish = item['name']

    return response.strip()

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        menu_data = load_menu_data()
        menu_tokens = tokenize_menu(menu_data)

        inputValue = request.get_json()
        user_input = inputValue['input_value']

        global dish
        response = generate_response(user_input, menu_tokens, menu_data)
        return f"Q-bot: {response} <br> <img class=\"food-robot-img\" src=\"/static/{dish}.jpg\">"
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


