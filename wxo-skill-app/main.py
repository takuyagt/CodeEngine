import logging
import os
import re
import secrets
from typing import TypedDict
import uuid

import flask
from dateutil import parser
import requests

# Enrichment task queue

app = flask.Flask(__name__)
app.logger.setLevel(logging.INFO)
app.logger.handlers[0].setFormatter(
    logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s (%(filename)s:%(lineno)d)"
    )
)
PORT = os.getenv("PORT", "8080")

WEEKDAY = {
    'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'ja': ['月', '火', '水', '木', '金', '土', '日'],
}

GENAI_API_URL = os.getenv("GENAI_API_URL")
GENAI_API_BEARER_TOKEN = os.getenv("GENAI_API_BEARER_TOKEN")
GENAI_PROJECT_ID = os.getenv("GENAI_PROJECT_ID")
GENAI_MODEL_ID = os.getenv("GENAI_MODEL_ID")


@app.route("/weekday", methods=["POST"])
def get_weekday():
    """returns weekday
    Request body:
        date: (required) date value in ISO format
        language: (optional) language code (Supported: 'en', 'ja')

    Returns:
        body: weekday: weekday label
        code: status code
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    if "date" not in data:
        return {"message": "Required 'date' parameter in body"}, 400
    sdt = data["date"]
    try:
        dt = parser.isoparse(sdt)
    except ValueError:
        app.logger.error("Failed to parse date format: %s", str(sdt), exc_info=True)
        return {"message": f"Invalid date format: {sdt}"}, 400
    lang = data.get("language", "en").lower()
    if lang not in WEEKDAY:
        return {
            "message": f"unsupported language: {lang}, supported languages: {list(WEEKDAY.keys())}"
        }, 400
    wd = WEEKDAY[lang][dt.weekday()]
    return {"weekday": wd}, 200


@app.route("/counter", methods=["POST"])
def loop_counter():
    """returns integer list
    Request body:
        size: (required) size of list
        text: (optional) default: "%d"

    Returns:
        body: loop: list of {"current_iteration": <int>, "total_iteration_needed": <int>}
        code: status code
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    s = int(data["size"])
    t = str(data.get("text", "%d"))
    rt = [
        {
            "current_iteration": i,
            "total_iteration_needed": s,
            "text": t % i
        } for i in range(s)
    ]
    return {"loop": rt}, 200


@app.route("/split", methods=["POST"])
def split_text():
    """returns integer list
    Request body:
        text: (required) text to be splitted
        delimiter: (optional) default: " "
    Returns:
        body: loop: list of {"current_iteration": <int>, "total_iteration_needed": <int>}
        code: status code
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    t = str(data["text"])
    d = str(data.get("delimiter", " "))
    parts = t.split(d)
    rt = [
        {
            "current_iteration": i,
            "total_iteration_needed": len(parts),
            "text": p
        } for i, p in enumerate(parts)
    ]
    return {"loop": rt}, 200


@app.route("/nested", methods=["POST"])
def nested_objects():
    """returns integer list
    Request body:
        message: any message

    Returns:
        message: str
        'nested_object.message': str
        'messages[0]': str
        'non.nested.object': str
        'expression[?aaaa]': str
        'has space': str
        '"double quated"': str
        nested_object: dict[str, str]
            message: float
            'non.nested.object': str
            'message[0]': str
            'has space': str
            '"double quated"': str
        messages: list[str]
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    message = data.get("message", "no mesage")
    child = {
        'message': 123.456,
        'non.nested.object': "in nest: " + message,
        'message[0]': "in nest: " + message,
        'has space': "in nest: " + message,
        '"double quated"': "in nest: " + message,
    }
    rt = {
        'message': message,
        'messages': ["list[0] " + message],
        'nested_object.message': message,
        'messages[0]': message,
        'non.nested.object': message,
        'expression[?aaaa]': message,
        'has space': message,
        '"double quated"': message,
        'nested_object': child,
    }
    return rt, 200


@app.route("/suggest_plans", methods=["POST"])
def suggest_plans():
    """suggest plans
    Request body:
        request: any message

    Returns:
        suggestions: list[str]
    """
    predefined = {
        1: [
            "1. Sushi at Tsukiji Outer Market: Start your evening with a sushi dinner at one of the many restaurants in the Tsukiji Outer Market. This is a great way to experience fresh, authentic sushi.",
            "2. Ramen at Ichiran: For a quick and delicious dinner, visit Ichiran Ramen. You can customize your ramen to your liking and enjoy it in a cozy, bustling atmosphere.",
            "3. Yakitori at Toriki: This popular yakitori (grilled chicken skewers) spot is a great place to try traditional Japanese street food. The atmosphere is lively and the food is delicious.",
            "4. Kaiseki at a traditional Japanese restaurant: For a more formal dining experience, consider a kaiseki meal at a traditional Japanese restaurant. This multi-course meal showcases the best of Japanese cuisine and is a great way to experience the country's culinary heritage.",
            "5. Izakaya hopping: Izakayas are Japanese pubs that serve small plates of food along with drinks. You can visit several izakayas in one night to try a variety of dishes and experience the lively atmosphere of Japanese nightlife.",
            "6. Dinner cruise: For a unique dining experience, consider a dinner cruise on the Sumida River. You can enjoy a delicious meal while taking in the sights of Tokyo's skyline.",
            "7. Street food at night markets: Tokyo has several night markets where you can find a variety of street food. This is a great way to try a little bit of everything and experience the energy of the city at night.",
            "8. Dinner at a Michelin-starred restaurant: If you're looking for a truly special dining experience, consider a meal at a Michelin-starred restaurant. Tokyo has many world-class restaurants that offer innovative and delicious cuisine.",
        ],
        2: [
            "- Sushi at Tsukiji Fish Market: Start your day early to visit the famous Tsukiji Fish Market. Enjoy fresh sushi at one of the many sushi restaurants in the area.",
            "- Ramen at Ichiran: This popular ramen chain offers a unique dining experience with individual booths and a self-service ticket machine. Try their tonkotsu ramen.",
            "- Tempura at Nodaiwa: Located in Asakusa, this restaurant is famous for its tempura. Enjoy the crispy fried dishes with a view of the Sumida River.",
            "- Okonomiyaki at Mizuno: Okonomiyaki is a savory pancake filled with various ingredients. Mizuno in Tsukishima is a popular spot to try this local specialty.",
            "- Curry at Coco Ichibanya: This curry house allows you to customize your curry dish. It's a great option if you're looking for a hearty meal.",
            "- Udon at Kagura: This udon noodle restaurant in Asakusa offers a variety of udon dishes. It's a great place to try traditional Japanese noodles.",
            "- Soba at Soba Noodles Kyubey: This soba noodle restaurant in Ginza offers a variety of soba dishes. It's a great place to try traditional Japanese noodles.",
            "- Shabu-shabu at Shabu-zen: This hot pot restaurant in Roppongi offers a variety of meats and vegetables. It's a great place to try this traditional Japanese dish.",
        ],
    }
    bullet_pattern = r'^(-|[1-9][0-9]*\.)\s*'
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    request = data.get("request")
    if "dinner" in request:
        res_plans = predefined[1]
    else:
        res_plans = predefined[2]
    suggestions = []
    for res_plan in res_plans:
        if not res_plan:
            continue
        plan = re.sub(bullet_pattern, "", res_plan)
        parts = plan.split(":")
        if len(parts) > 1:
            recommendation = parts[0]
            suggestions.append({
                "recommendation": recommendation,
                "plan": plan
            })
        else:
            suggestions.append({
                "recommendation": "",
                "plan": plan
            })
    return {"suggestions": suggestions}, 200


@app.route("/reserve_table", methods=["POST"])
def reserve_table():
    """reserve a table
    Request body:
        request: string
        time: date time
        no_people: int
        area: string

    Returns:
        result: string
        reservation_id: string
    """
    predefined = {
        "sushi": "Kyubei",
        "tempura": "Kondo",
        "okonomiyaki": "Moheji",
        "yakitori": "Torikizoku",
        "kaiseki": "Kitcho",
        "izakaya": "Uotami",
        "dinner cruise": "dinner cruise",
        "shabu-shabu": "Shabu-zen",
    }
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    request = str(data.get("request"))
    sdt = str(data.get("time"))
    dt = parser.isoparse(sdt)
    n = int(data.get("no_people"))
    restaurant = None
    for c, restaurant in predefined.items():
        if c in request.lower():
            break
    if not restaurant:
        result = "Sorry, not found a table at that time"
        res_id = ""
    else:
        result = f"Reserved a table at {restaurant} for {n} at {dt.strftime('%Y-%m-%d %H:%M')}"
        res_id = secrets.token_urlsafe(6)
    return {"result": result, "reservation_id": res_id}, 200


@app.route("/parrot_back", methods=["POST"])
def parrot_back():
    """return input
    Request body:
        any
    Returns:
        any
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    return data, 200


@app.route("/object_array", methods=["POST"])
def object_array():
    """return input
    Request body:
        any
    Returns:
        any
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    return data, 200


class CallbackInfo(TypedDict):
    """
    CallbackInfo class to store callback information.

    Attributes:
        key (str): key.
        callback_url (str): Callback URL.

    """
    key: str
    callback_url: str


CALLBACK_INFO_LIST: list[CallbackInfo] = []


@app.post("/async_requests")
def async_request():
    """return input
    Request body:
        key: string
    Returns:
        key: string
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Received event: %s", str(data))
    key = data.get("key")
    if key is None:
        key = uuid.uuid4()
    callback_url = flask.request.headers.get("callbackUrl")
    if callback_url is None:
        return {"message": "'callbackUrl' header is required."}, 400
    entry = {"key": key, "callback_url": callback_url}
    CALLBACK_INFO_LIST.append(entry)
    return entry, 202


@app.get("/async_requests")
def list_async_requests():
    """return input
    Request body:
    Returns:
       async_requests: list[dict[str, str]]
    """
    return {"async_requests": CALLBACK_INFO_LIST}, 200


@app.post('/callback')
def callback():
    """return input
    Request body:
        key: string
        message: string
    Returns:
        key: string
        message: string
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info("Callback: %s", str(data))
    key = data.get("key")
    message = data.get("message")
    url = None
    idx = 0
    for idx, info in enumerate(CALLBACK_INFO_LIST):
        if info["key"] == key:
            url = info["callback_url"]
            break

    if url is None:
        return {'message': f'Not found: {key}'}, 404

    payload = {'message': message}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers, timeout=10)

    if response.status_code > 299:
        return {
            'message': f"Failed to call back: {url}, [{response.status_code}] {response.content.decode('utf-8')}"
        }, 400

    payload['callback_info'] = CALLBACK_INFO_LIST.pop(idx)
    return payload, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(PORT))
