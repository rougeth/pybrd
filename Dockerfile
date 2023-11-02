FROM python:3.11-slim
RUN pip install poetry
WORKDIR /pybrd
COPY . /pybrd/
COPY poetry.lock pyproject.toml /pybrd/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi
CMD python src/main.py