FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/project

WORKDIR /project

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY /app/ /project/app/

RUN apt-get update && apt-get install -y --no-install-recommends gettext

RUN python app/manage.py compilemessages -l de
RUN python app/manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "settings.wsgi:application", "--chdir", "app", "--bind", "0.0.0.0:8000"]