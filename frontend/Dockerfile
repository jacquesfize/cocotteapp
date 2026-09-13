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

# --- Image de production : Caddy sert la SPA et fait office de reverse proxy + HTTPS automatique.
FROM caddy:2-alpine AS prod
COPY --from=build /app/dist /srv/app
COPY Caddyfile /etc/caddy/Caddyfile
EXPOSE 80 443
