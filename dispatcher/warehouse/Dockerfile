FROM ubuntu:16.04

RUN apt-get update && apt-get install -y openssh-server rsync
RUN mkdir /var/run/sshd
RUN echo 'root:uploading' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/Port 22/Port 27972/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN mkdir ~/.ssh/
ADD id_rsa.pub /id_rsa.pub
RUN touch ~/.ssh/authorized_keys
RUN cat /id_rsa.pub >> ~/.ssh/authorized_keys

EXPOSE 27972
CMD ["/usr/sbin/sshd", "-D"]