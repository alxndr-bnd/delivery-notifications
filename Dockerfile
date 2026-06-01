# ---- Stage 0: serve the static landing (no Django yet) ----
# Switches to a Django+gunicorn image at Stage 1 (see SETUP_CICD.md).
FROM nginx:1.27-alpine

# Cloud Run sends traffic to $PORT (8080); nginx is configured to listen there.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY landing/ /usr/share/nginx/html/

EXPOSE 8080
