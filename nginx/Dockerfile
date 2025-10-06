FROM nginx:stable-alpine


# Remove default config and add our own
COPY nginx/nginx.conf /etc/nginx/nginx.conf


# Copy static files into nginx html folder
COPY nginx/static /usr/share/nginx/html


EXPOSE 80


CMD ["nginx", "-g", "daemon off;"]