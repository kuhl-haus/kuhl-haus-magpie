from kuhl_haus.magpie.web.celery_app import app


@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)


@app.task
def floor_div(x, y):
    return x // y
