"""Atlas Report Builder — Flask entry point.

Routes:
  GET  /        the report-request form (client + period + cadence)
  POST /report  build and render a client-ready report
"""

import os

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, abort, render_template, request

import config
from atlas import clients as clients_mod
from atlas.mock_api import _gen
from atlas.report.builder import build_report

app = Flask(__name__)


# --- Jinja formatting filters -------------------------------------------

@app.template_filter("thousands")
def thousands(value):
    try:
        return f"{int(round(float(value))):,}"
    except (TypeError, ValueError):
        return value


@app.template_filter("pct")
def pct(value, places=1):
    try:
        return f"{float(value) * 100:.{places}f}%"
    except (TypeError, ValueError):
        return value


@app.template_filter("money")
def money(value):
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return value


@app.template_filter("signed")
def signed(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    return f"+{v:g}" if v > 0 else f"{v:g}"


# --- helpers -------------------------------------------------------------

def _period_options():
    options = []
    period = config.LATEST_PERIOD
    for _ in range(config.PERIOD_CHOICES):
        options.append({"value": period, "label": _gen.period_label(period)})
        period = _gen.shift_period(period, 1)
    return options


def _form_context(**extra):
    ctx = {
        "clients": clients_mod.all_clients(),
        "periods": _period_options(),
        "cadences": list(config.CADENCES.keys()),
        "default_cadence": "Monthly",
    }
    ctx.update(extra)
    return ctx


# --- routes --------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", **_form_context())


@app.route("/report", methods=["POST"])
def report():
    client_id = request.form.get("client")
    period = request.form.get("period")
    cadence = request.form.get("cadence", "Monthly")

    if clients_mod.get_client(client_id) is None:
        abort(404)

    try:
        data = build_report(client_id, period, cadence)
    except RuntimeError as exc:
        return render_template("index.html", **_form_context(error=str(exc))), 400

    return render_template("report.html", report=data)


if __name__ == "__main__":
    app.run(debug=bool(os.environ.get("FLASK_DEBUG")), port=5001)
