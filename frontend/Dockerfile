FROM node:22-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

# --- Image de développement : serveur Vite avec rechargement à chaud.
FROM base AS dev
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# --- Build statique de la SPA (Vue Router en mode history : nécessite try_files côté Caddy).
FROM base AS build
RUN npm run build

# --- Image de production : Caddy sert la SPA, reverse-proxie /api et /django-admin vers le backend, et
# (en mode standalone) termine le TLS lui-même via Let's Encrypt. Pas de Caddyfile embarqué ici :
# il est toujours fourni par bind-mount depuis docker-compose.prod.yml / .prod.proxy.yml (voir
# deploy/Caddyfile.standalone et deploy/Caddyfile.proxy) pour rester modifiable sans rebuild.
FROM caddy:2-alpine AS prod
COPY --from=build /app/dist /srv/app
EXPOSE 80 443
