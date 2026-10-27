# Build context is the repo root so the mock client can read shared/fixtures.
FROM node:20-slim
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY shared /app/shared
COPY frontend .
EXPOSE 5173
CMD ["npm", "run", "dev"]
