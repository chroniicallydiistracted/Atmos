FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* tsconfig.json tsconfig.node.json vite.config.ts vitest.setup.ts index.html ./
COPY public ./public
COPY src ./src

RUN npm install && npm run build

EXPOSE 4173
CMD ["npm", "run", "preview"]
