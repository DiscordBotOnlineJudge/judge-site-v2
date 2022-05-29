FROM python:3

LABEL maintainer="Jimmy Liu <jimmyjcl753@gmail.com>"

WORKDIR /app

COPY requirements.txt /app/
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

COPY . /app/
EXPOSE 8000

CMD [ "gunicorn", "-b", "0.0.0.0:8000", "run:app"]
