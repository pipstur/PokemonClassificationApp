from flask import Flask, request, jsonify
import openai
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/get_pokemon_info": {"origins": "http://localhost:8000"}})

openai.api_key = 'API_KEY'

@app.route('/get_pokemon_info', methods=['POST'])
def get_pokemon_info():
    data = request.get_json()
    user_input = data['text'] + "which pokemon am I?Answer in a freindly tone :). Keep it concise and under 200 words. Format the answer like this: \nName of the pokemon: \nDescription: \nReasoning: "
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": user_input}
        ],
        temperature=0.2,  
        max_tokens=200   
    )

    response_text = response['choices'][0]['message']['content']
    name_start = "Name of the pokemon:"
    description_start = "Description:"
    reasoning_start = "Reasoning:"

    name_index = response_text.find(name_start)
    description_index = response_text.find(description_start)
    reasoning_index = response_text.find(reasoning_start)

    if name_index == -1 or description_index == -1 or reasoning_index == -1:
        response_data = {
            'pokemon_name': "None",
            'pokemon_description': "None",
            'reasoning': "None",
            'pokemon_image_url': "https://via.placeholder.com/150"
        }
    else:
        
        name = response_text[name_index + len(name_start):description_index].strip()
        description = response_text[description_index + len(description_start):reasoning_index].strip()
        reasoning = response_text[reasoning_index + len(reasoning_start):].strip()
        pokeapi_url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
        pokeapi_response = requests.get(pokeapi_url)
        if pokeapi_response.status_code == 200:
            pokemon_data = pokeapi_response.json()
            pokemon_image_url = pokemon_data['sprites']['front_default']
        else:
            description = "No description available."
            pokemon_image_url = "https://via.placeholder.com/150" #placeholder

        response_data = {
            'pokemon_name': name,
            'pokemon_description': description,
            'reasoning': reasoning,
            'pokemon_image_url': pokemon_image_url  
        }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
