ARG BASE_IMAGE=python:3.13
FROM ${BASE_IMAGE}
WORKDIR /app

COPY . /app/

# Install requirements
RUN pip install -r requirements.txt


EXPOSE 8000/tcp

RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "-m", "kuhl_haus.magpie.manage", "runserver", "0.0.0.0:8000"]
