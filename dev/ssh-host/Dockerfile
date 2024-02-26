FROM alpine:3

# Install SSH server
RUN apk update && apk add --no-cache openssh-server

# Create SSH directory and set permissions
RUN mkdir /var/run/sshd
RUN chmod 0755 /var/run/sshd

# Copy SSH host keys to container
COPY ssh_host_rsa_key /etc/ssh/ssh_host_rsa_key

# Copy test client SSH public key to the container
COPY id_rsa.pub /root/.ssh/authorized_keys

RUN mkdir -p \
    /root/artifacts \
    /root/logs \
    /root/zims/freecodecamp \
    /root/zims/gutenberg \
    /root/zims/ifixit \
    /root/zims/mooc \
    /root/zims/other \
    /root/zims/phet \
    /root/zims/stack_exchange \
    /root/zims/ted \
    /root/zims/videos \
    /root/zims/vikidia \
    /root/zims/wikibooks \
    /root/zims/wikihow \
    /root/zims/wikinews \
    /root/zims/wikipedia \
    /root/zims/wikiquote \
    /root/zims/wikisource \
    /root/zims/wikiversity \
    /root/zims/wikivoyage \
    /root/zims/wiktionary \
    /root/zims/zimit

# Expose SSH port
EXPOSE 22

# Start SSH server
CMD ["/usr/sbin/sshd", "-D"]