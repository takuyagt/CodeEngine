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
    sdt = data["date"]
    dt = parser.isoparse(sdt)
    lang = data.get("language", "en").lower()
    if lang not in list(WEEKDAY.keys()):
        return {"message": f"unsupported language: {lang}, supported languages: {list(WEEKDAY.keys())}"}
    wd = WEEKDAY[lang][dt.weekday()]
    return {"weekday": wd}, 200

@app.route("/counter", methods=["POST"])
def loop_counter():
    """returns integer list
    Request body:
        size: (required) size of list

    Returns:
        body: loop: list of {"current_iteration": <int>, "total_iteration_needed": <int>}
        code: status code
    """
    data = flask.json.loads(flask.request.data)
    app.logger.info(f"Received event: {data}")
    s = int(data["size"])
    rt = [{"current_iteration": i, "total_iteration_needed": s} for i in range(s)]
    return {"loop": rt}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(PORT))