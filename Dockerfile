FROM python:3.6.3-alpine

RUN apk add --no-cache --virtual build-base \
  && apk add --no-cache --virtual libxml2-dev \
  && apk add --no-cache --virtual libxslt-dev \
  && apk add --no-cache --virtual imagemagick \
  && apk add --no-cache --virtual imagemagick-dev \
  && apk add --no-cache --virtual ghostscript \
  && mkdir -p /usr/include/libxml \
  && ln -s /usr/include/libxml2/libxml/xmlexports.h /usr/include/libxml/xmlexports.h \
  && ln -s /usr/include/libxml2/libxml/xmlversion.h /usr/include/libxml/xmlversion.h

# RUN mkdir rosie
# COPY rosie/config.ini.example ./config.ini
# COPY rosie/requirements.txt ./rosie
# RUN pip install -r rosie/requirements.txt
RUN echo -e '@edgunity http://nl.alpinelinux.org/alpine/edge/community\n\
@edge http://nl.alpinelinux.org/alpine/edge/main\n\
@testing http://nl.alpinelinux.org/alpine/edge/testing\n\
@community http://dl-cdn.alpinelinux.org/alpine/edge/community'\
  >> /etc/apk/repositories

RUN apk add --no-cache --virtual openblas-dev \
  && apk add --no-cache --virtual unzip \
  && apk add --no-cache --virtual wget \
  && apk add --no-cache --virtual cmake \
  && apk add --no-cache --virtual libtbb@testing \
  && apk add --no-cache --virtual libtbb-dev@testing \
  && apk add --no-cache --virtual libjpeg \
  && apk add --no-cache --virtual libjpeg-turbo-dev \
  && apk add --no-cache --virtual libpng-dev \
  && apk add --no-cache --virtual jasper-dev \
  && apk add --no-cache --virtual tiff-dev \
  && apk add --no-cache --virtual libwebp-dev \
  && apk add --no-cache --virtual clang-dev \
  && apk add --no-cache --virtual linux-headers \
  && apk add --no-cache --virtual clang \
  && pip install numpy

ENV CC /usr/bin/clang
ENV CXX /usr/bin/clang++

ENV OPENCV_VERSION=3.1.0

RUN mkdir /opt && cd /opt && \
  wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip && \
  unzip ${OPENCV_VERSION}.zip && \
  rm -rf ${OPENCV_VERSION}.zip

RUN mkdir -p /opt/opencv-${OPENCV_VERSION}/build && \
  cd /opt/opencv-${OPENCV_VERSION}/build && \
  cmake \
  -D CMAKE_BUILD_TYPE=RELEASE \
  -D CMAKE_INSTALL_PREFIX=/usr/local \
  -D WITH_FFMPEG=NO \
  -D WITH_IPP=NO \
  -D WITH_OPENEXR=NO \
  -D WITH_TBB=YES \
  -D BUILD_EXAMPLES=NO \
  -D BUILD_ANDROID_EXAMPLES=NO \
  -D INSTALL_PYTHON_EXAMPLES=NO \
  -D BUILD_DOCS=NO \
  -D BUILD_opencv_python2=NO \
  -D BUILD_opencv_python3=ON \
  -D PYTHON3_EXECUTABLE=/usr/local/bin/python \
  -D PYTHON3_INCLUDE_DIR=/usr/local/include/python3.6m/ \
  -D PYTHON3_LIBRARY=/usr/local/lib/libpython3.so \
  -D PYTHON_LIBRARY=/usr/local/lib/libpython3.so \
  -D PYTHON3_PACKAGES_PATH=/usr/local/lib/python3.6/site-packages/ \
  -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.6/site-packages/numpy/core/include/ \
  .. && \
  make VERBOSE=1 && \
  make && \
  make install && \
  rm -rf /opt/opencv-${OPENCV_VERSION}

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN adduser -S serenata_de_amor
RUN chown -hR serenata_de_amor .
USER serenata_de_amor

COPY . /usr/src/app
