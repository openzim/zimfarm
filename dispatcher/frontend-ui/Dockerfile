FROM library/nginx:mainline

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY src /usr/share/nginx/html
RUN ln -s /usr/share/nginx/html/assets/favicon.ico /usr/share/nginx/html/favicon.ico

ENV ZIMFARM_WEBAPI https://api.farm.openzim.org

ENTRYPOINT ["entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
