FROM python

RUN mkdir metadata-organizer

COPY  . metadata-organizer/

RUN apt-get update && apt-get install -y \
    python3-pip

RUN pip install --upgrade pip

RUN pip3 install mkdocs>=1.1.2

RUN pip3 install PyYAML>=5.1

RUN pip3 install GitPython>=3.1.18

RUN pip3 install tabulate

RUN pip3 install pytz

ENTRYPOINT ["python", "metadata-organizer/fred/metaTools.py"]
