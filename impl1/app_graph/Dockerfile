FROM    python:3.11-alpine
WORKDIR /app
# RUN     mkdir -p /app/ontologies
# RUN     mkdir -p /app/rdf
# RUN     mkdir -p /app/sparql
# RUN     mkdir -p /app/tmp
# RUN     mkdir -p /app/uploads
RUN     apk add gcc python3-dev
RUN     apk add gcc musl-dev linux-headers python3-dev
COPY    . .
# COPY    .ontologies/ /app/
# COPY    .rdf/ /app/
# COPY    .sparql/ /app/
RUN     pip install --upgrade pip
RUN     pip install -r requirements.txt
RUN     pip list
EXPOSE  8001
CMD     ["uvicorn", "websvc:app", "--host", "0.0.0.0", "--port", "8001"]


# This file contains the instructions for building the Docker image.
# Chris Joakim, Microsoft
#
# Developer Notes:
# docker build -t cjoakim/caig_graph .
# docker image ls
# docker ps
# docker stop -t 2 008038664a58
#
# DockerHub:
# docker push cjoakim/caig_graph:latest
