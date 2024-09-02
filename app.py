from flask import Flask, request, jsonify
import openai
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/get_pokemon_info": {"origins": "http://localhost:8000"}})

llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Based on the input, which pokemon am I? Answer in a friendly tone and try to be as
            creative as possible, always try to find a pokemon. Keep it under 250 words. Don't use special characters. Be precise with the naming.
            If the prompt is in Serbian, you can reply in Serbian. Translate the words best as you can.
            Format the answer like this: \nName of the pokemon: \nDescription: \nReasoning:""",
        ),
        ("human", "{input}"),
    ]
)

def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "https://pipstur.github.io")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Origin, Content-Type, Accept")
    return response


@app.route("/get_pokemon_info", methods=["POST", "OPTIONS"])
def get_pokemon_info():
    # Handle preflight request
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight"})
        return add_cors_headers(response), 200

    try:
        data = request.get_json()
        if not data or "text" not in data:
            raise ValueError("Missing 'text' field in request")

        user_input = data["text"]
        # Generate response from model
        chain = prompt | llm | StrOutputParser()
        response_text = chain.invoke({"input": user_input})

        # Parse response
        name_start = "Name of the Pokémon:"
        description_start = "Description:"
        reasoning_start = "Reasoning:"

        name_index = response_text.find(name_start)
        description_index = response_text.find(description_start)
        reasoning_index = response_text.find(reasoning_start)

        if name_index == -1 or description_index == -1 or reasoning_index == -1:
            response_data = {
                "pokemon_name": "None",
                "pokemon_description": "None",
                "reasoning": "None",
                "pokemon_image_url": "https://via.placeholder.com/150",
            }
        else:
            name = response_text[name_index + len(name_start): description_index].strip()
            description = response_text[description_index + len(description_start): reasoning_index].strip()
            reasoning = response_text[reasoning_index + len(reasoning_start):].strip()

            pokeapi_url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
            pokeapi_response = requests.get(pokeapi_url)
            if pokeapi_response.status_code == 200:
                pokemon_data = pokeapi_response.json()
                pokemon_image_url = pokemon_data["sprites"]["front_default"]
            else:
                description = "No description available."
                description = response_text
                pokemon_image_url = "https://via.placeholder.com/150"

            response_data = {
                "pokemon_name": name,
                "pokemon_description": description,
                "reasoning": reasoning,
                "pokemon_image_url": pokemon_image_url,
            }

        response = jsonify(response_data)
        return add_cors_headers(response), 200

    except Exception as e:
        # Log detailed error message
        print(f"Error: {str(e)}")
        response = jsonify({"error": str(e)})
        return add_cors_headers(response), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
