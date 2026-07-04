FROM python:3.12-alpine

ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN mkdir -p $APP_HOME ${HOME}/media ${HOME}/storage \
    && addgroup -S fast \
    && adduser -S fast -G fast

WORKDIR $HOME

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && chown -R fast:fast .

COPY app app
COPY migrations migrations
COPY alembic.ini .
COPY .env .

USER fast
