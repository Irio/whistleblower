FROM continuumio/anaconda3

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN adduser -S serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor

COPY . /usr/src/app
