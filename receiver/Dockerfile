FROM python:3.8-buster

# system dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends openssh-sftp-server openssh-server wget cron parallel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# build and configure rssh
# we are keeping source here as it's small and hosted on sourceforge
WORKDIR /usr/src/
RUN wget https://download.kiwix.org/dev/rssh-2.3.4.tar.gz
RUN tar -xvf rssh-2.3.4.tar.gz
WORKDIR /usr/src/rssh-2.3.4
RUN ./configure --prefix=/ && make && make install
RUN printf "allowscp\nallowsftp\n" > /etc/rssh.conf

WORKDIR /
# setup a chroot jail at /jail
RUN wget https://olivier.sessink.nl/jailkit/jailkit-2.21.tar.gz
RUN tar xf jailkit-2.21.tar.gz
RUN cd jailkit-2.21 && ./configure && make && make install
RUN rm -rf /jailkit-2.21 && rm -f jailkit-2.21.tar.gz
# patch ini file
RUN sed -i.bak -e '116d' /etc/jailkit/jk_init.ini
RUN printf "\n[rssh]\npaths = /bin/rssh, /etc/rssh.conf\n" >> /etc/jailkit/jk_init.ini
RUN mkdir -p /jail
RUN chown root:root /jail
RUN jk_init -v -j /jail rssh ssh scp sftp
RUN useradd -M -N -r -s /bin/rssh uploader
RUN jk_jailuser -m -j /jail -s /bin/rssh uploader
# fix shell for user
RUN sed -i 's/usr\/sbin\/jk_chrootsh/bin\/rssh/' /etc/passwd
RUN mkdir -p /jail/zim
RUN mkdir -p /jail/logs
RUN chmod 777 /jail/zim
RUN chmod 777 /jail/logs

# OpenSSH server
COPY sshd_config /etc/ssh/sshd_config
VOLUME /jail/zim
VOLUME /jail/logs

# Quarantine
VOLUME /mnt/quarantine
VOLUME /mnt/zim
VOLUME /mnt/check_logs

ENV ZIM_TOOLS_URL http://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-1.0.4.tar.gz
ENV ZIM_SRC_DIR /jail/zim
ENV ZIM_DST_DIR /mnt/zim
ENV ZIM_QUAR_DIR /mnt/quarantine
ENV VALIDATION_LOG_DIR /mnt/check_logs
ENV ZIMCHECK_OPTION -A

RUN wget -O zim-tools.tar.gz -q $ZIM_TOOLS_URL && \
  tar -xzf zim-tools.tar.gz && \
  cp zim-tools*/* /usr/local/bin/ && \
  rm -rf zim-tools*
COPY apps/check_zim.sh /usr/local/bin/

# OpenSSH public-key auth relay
ENV ZIMFARM_WEBAPI https://api.farm.openzim.org/v1
ENV ZIMFARM_USERNAME uploader

COPY apps/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
COPY apps/get_zimfarm_key.py /usr/bin/get_zimfarm_keys

COPY entrypoint.sh /usr/bin/entrypoint.sh
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
CMD ["cron", "-f"]
