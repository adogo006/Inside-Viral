FROM nginx:latest
COPY ./Nginx/src /usr/share/nginx/html
COPY ./Nginx/nginx.conf /etc/nginx/nginx.conf 
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

