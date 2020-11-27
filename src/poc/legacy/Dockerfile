FROM arm32v7/alpine
WORKDIR /code
RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk add python3
RUN apk add py3-pip
RUN apk add python3-dev
COPY . .
RUN pip install wheel
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt
CMD ["python3", "app.py"]
