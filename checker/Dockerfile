FROM alpine:3
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN wget -O zim-tools.tar.gz -q https://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-2.1.0.tar.gz && \
  tar -xzf zim-tools.tar.gz && \
  cp zim-tools*/* /usr/local/bin/ && \
  rm -rf zim-tools*

CMD ["zimcheck"]
