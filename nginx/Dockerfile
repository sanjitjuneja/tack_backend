FROM nginx:1.23

RUN apt-get update -y && apt-get install -y apache2-utils && rm -rf /var/lib/apt/lists/*


RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

COPY run.sh ./
RUN chmod 0755 ./run.sh
CMD [ "./run.sh" ]