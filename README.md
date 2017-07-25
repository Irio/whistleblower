[![Build Status](https://travis-ci.org/datasciencebr/whistleblower.svg?branch=master)](https://travis-ci.org/datasciencebr/whistleblower)
[![Code Health](https://landscape.io/github/datasciencebr/whistleblower/master/landscape.svg?style=flat)](https://landscape.io/github/datasciencebr/whistleblower/master)
[![Coverage Status](https://coveralls.io/repos/github/gusttavoaguiarr/whistleblower/badge.svg?branch=master)](https://coveralls.io/github/gusttavoaguiarr/whistleblower?branch=master)

# Whistleblower

Follow [@RosieDaSerenata](https://twitter.com/RosieDaSerenata) to get Brazilian Chamber of Deputies' updates in your timeline.

## Setup

Install [Docker](https://www.docker.com) and [Docker Compose](https://docs.docker.com/compose/).

```console
$ git clone --recursive git@github.com:Irio/whistleblower.git
$ cd whistleblower
$ cp .env.example .env
$ docker-compose build
```

## Running

```console
$ docker-compose run worker python whistleblower/get_dataset.py
$ docker-compose run worker python rosie/rosie.py run chamber_of_deputies data
$ docker-compose up
```

## Testing

```console
$ docker-compose run worker python -m unittest discover tests
```
