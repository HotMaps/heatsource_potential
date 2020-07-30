FROM hotmaps/grass-py3-pdal:7.8
MAINTAINER Pietro Zambelli <pietro.zambelli@eurac.edu>
ENV PACKAGES="\
    ca-certificates \
    supervisor \
    " \
    GRASSBIN="grass78"

# Setup app server
WORKDIR /
RUN mkdir -p /data

# Install required python modules
COPY ./requirements.txt /cm/
RUN pip3 install --upgrade pip && \
    pip3 install --upgrade numpy scipy grass-session && \
    pip3 install -r /cm/requirements.txt

# Copy app source code
COPY . /cm
WORKDIR /cm

RUN chmod u+x /cm/wait-for-it.sh

# Start server
EXPOSE 80

RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start processes
CMD ["/cm/wait-for-it.sh","rabbit:5672","--strict","--timeout=360","--","/usr/bin/supervisord"]

