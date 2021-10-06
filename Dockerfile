FROM python:3.9-alpine as base

# Build
FROM base as builder
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt /venv
RUN pip install -r /venv/requirements.txt

# Run
FROM base
COPY --from=builder /venv /venv
COPY . /app/
WORKDIR /app
ENV PATH="/venv/bin:$PATH"
CMD ["python3", "main.py"]
