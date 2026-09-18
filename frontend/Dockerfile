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

# --- Image de production : nginx sert la SPA et reverse-proxie /api et /admin vers le backend,
# en HTTP interne uniquement (pas de TLS ici : le Caddy partagé de l'hôte s'en charge, voir
# nginx.conf).
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /srv/app
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
