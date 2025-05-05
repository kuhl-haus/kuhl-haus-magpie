import os
import requests

from kuhl_haus.magpie.web.celery_app import app

CONFIG_API = os.environ.get("CONFIG_API")


@app.task
def endpoints():
    response = requests.get(f"{CONFIG_API}/endpoints/")
    json_data = response.json()
    return json_data


@app.task
def resolvers():
    response = requests.get(f"{CONFIG_API}/resolvers/")
    json_data = response.json()
    return json_data


@app.task
def resolver_lists():
    response = requests.get(f"{CONFIG_API}/resolver-lists/")
    json_data = response.json()
    return json_data


@app.task
def default_resolver_list():
    response = requests.get(f"{CONFIG_API}/resolver-lists/1/")
    json_data = response.json()
    return json_data
