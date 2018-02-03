FROM python:3.6.3-alpine

RUN apk add --no-cache --virtual build-base \
  && apk add --no-cache --virtual libxml2-dev \
  && apk add --no-cache --virtual libxslt-dev \
  && apk add --no-cache --virtual imagemagick \
  && apk add --no-cache --virtual imagemagick-dev \
  && mkdir -p /usr/include/libxml \
  && ln -s /usr/include/libxml2/libxml/xmlexports.h /usr/include/libxml/xmlexports.h \
  && ln -s /usr/include/libxml2/libxml/xmlversion.h /usr/include/libxml/xmlversion.h

# RUN mkdir rosie
# COPY rosie/config.ini.example ./config.ini
# COPY rosie/requirements.txt ./rosie
# RUN pip install -r rosie/requirements.txt

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN adduser -S serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor

COPY . /usr/src/app
