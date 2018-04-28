FROM continuumio/anaconda3

RUN apt-get install -y \
  libmagickwand-dev \
  ghostscript \
  libgs-dev

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN adduser --system serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor

COPY . /usr/src/app
