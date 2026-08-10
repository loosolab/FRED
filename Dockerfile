FROM python

RUN mkdir metadata-organizer

COPY  . metadata-organizer/

RUN apt-get update && apt-get install -y \
    python3-pip

RUN pip install --upgrade pip

RUN pip install ./metadata-organizer

ENTRYPOINT ["fred"]
