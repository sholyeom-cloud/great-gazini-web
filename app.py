from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI
import os, random

# --- Load environment variables ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Tarot deck (can be expanded to full 78) ---
TAROT = [
    "The Fool","The Magician","The High Priestess","The Empress","The Emperor",
    "The Hierophant","The Lovers","The Chariot","Strength","The Hermit",
    "Wheel of Fortune","Justice","The Hanged Man","Death","Temperance",
    "The Devil","The Tower","The Star","The Moon","The Sun","Judgement","The World"
]

ELEMENT_BY_SIGN = {
    "oven":"ogenj","lev":"ogenj","strelec":"ogenj",
    "bik":"zemlja","devica":"zemlja","kozorog":"zemlja",
    "dvojček":"zrak","tehtnica":"zrak","vodnar":"zrak",
    "rak":"voda","škorpijon":"voda","ribi":"voda",
}

# --- Serve card images from /cards ---
@app.route("/cards/<path:filename>")
def serve_card(filename):
    return send_from_directory("cards", filename)

@app.get("/")
def index():
    return render_template("index.html")

# --- Shared reading generator (used by both modes) ---
def generate_reading(name, sign, cards):
    element = ELEMENT_BY_SIGN.get(sign.lower(), "neznan element")

    prompt = f"""
Ti si 'Veliki Gazini', mistični psihik. Piši v slovenščini, toplo in magično.

Ime: {name}
Znamenje: {sign} (element: {element})
Tri karte: {', '.join(cards)}

Napiši 3–4 odstavke:
- kaj kombinacija treh kart pomeni kot celota,
- kaj se bo verjetno dogajalo v bližnji prihodnosti,
- na kaj naj bo oseba pozorna (opozorilo/lekcija),
- osebna nota glede znamenja in elementa,
- zaključi z eno spodbudno povedjo.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=700,
    )
    reading_text = resp.choices[0].message.content.strip()
    card_images = [f"/cards/{c.lower().replace(' ', '_')}.png" for c in cards]
    return {"cards": cards, "images": card_images, "reading": reading_text}

# --- AUTO reading ---
@app.post("/reading")
def reading():
    data = request.get_json(force=True)
    name = data.get("name", "Popotnik")
    sign = data.get("sign", "neznano")
    cards = random.sample(TAROT, 3)
    try:
        result = generate_reading(name, sign, cards)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MANUAL reading ---
@app.post("/manual_reading")
def manual_reading():
    data = request.get_json(force=True)
    name = data.get("name", "Popotnik")
    sign = data.get("sign", "neznano")
    cards = data.get("cards", [])
    if not cards or len(cards) < 3:
        return jsonify({"error": "Vnesi tri karte!"}), 400
    try:
        result = generate_reading(name, sign, cards)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
