FROM python:3.11-alpine

WORKDIR /action

COPY ./Pipfile* ./
RUN pip install pipenv && \
  pipenv install --system --deploy && \
  pipenv --clear

COPY ./bin .

ENTRYPOINT [ "python" ]
CMD [ "/action/main.py" ]
