from dateutil import parser
import logging
import os

import flask

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
    app.logger.info(f"Received event: {data}")
    if "date" not in data:
        return {"message": "Required 'date' parameter in body"}, 400
    sdt = data["date"]
    try:
        dt = parser.isoparse(sdt)
    except ValueError as err:
        app.logger.error(f"Failed to parse date format: {sdt}", err)
        return {"message": f"Invalid date format: {sdt}"}, 400
    lang = data.get("language", "en").lower()
    if lang not in list(WEEKDAY.keys()):
        return {"message": f"unsupported language: {lang}, supported languages: {list(WEEKDAY.keys())}"}, 400
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
    app.logger.info(f"Received event: {data}")
    s = int(data["size"])
    t = str(data.get("text", "%d"))
    rt = [{"current_iteration": i, "total_iteration_needed": s, "text": t % i} for i in range(s)]
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
    app.logger.info(f"Received event: {data}")
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(PORT))