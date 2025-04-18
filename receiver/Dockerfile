FROM python:3.12-slim-bookworm
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

# system dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends openssh-sftp-server openssh-server wget cron parallel build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# build and configure rssh
# we are keeping source here as it's small and hosted on sourceforge
WORKDIR /usr/src/
RUN wget -nv https://dev.kiwix.org/rssh-2.3.4.tar.gz
RUN tar -xvf rssh-2.3.4.tar.gz
WORKDIR /usr/src/rssh-2.3.4
RUN ./configure --prefix=/ && make && make install
RUN printf "allowscp\nallowsftp\n" > /etc/rssh.conf

WORKDIR /
# setup a chroot jail at /jail
RUN wget -nv https://olivier.sessink.nl/jailkit/jailkit-2.23.tar.gz
RUN tar xf jailkit-2.23.tar.gz
RUN cd jailkit-2.23 && ./configure && make && make install
RUN rm -rf /jailkit-2.23 && rm -f jailkit-2.23.tar.gz
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

ENV ZIM_TOOLS_URL https://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-3.5.0.tar.gz
ENV ZIM_SRC_DIR /jail/zim
ENV ZIM_DST_DIR /mnt/zim
ENV ZIM_QUAR_DIR /mnt/quarantine
ENV VALIDATION_LOG_DIR /mnt/check_logs
ENV ZIMCHECK_OPTION -A
ENV ZIMCHECK_PARALLEL_JOBS 2

RUN wget -nv -O zim-tools.tar.gz -q $ZIM_TOOLS_URL && \
  tar -xzf zim-tools.tar.gz && \
  cp zim-tools*/* /usr/local/bin/ && \
  rm -rf zim-tools*
COPY apps/check_zims.sh /usr/local/bin/
COPY apps/check_zim.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/check_zim.sh /usr/local/bin/check_zims.sh

# OpenSSH public-key auth relay
ENV ZIMFARM_WEBAPI https://api.farm.openzim.org/v1
ENV ZIMFARM_USERNAME uploader

COPY apps/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
COPY apps/get_zimfarm_key.py /usr/bin/get_zimfarm_keys

COPY entrypoint.sh /usr/bin/entrypoint.sh
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
CMD ["cron", "-f"]
