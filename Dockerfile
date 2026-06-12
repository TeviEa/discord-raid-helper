FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install production dependencies first (better layer caching)
COPY package*.json ./
RUN npm ci --omit=dev

# Copy source files
COPY --chown=node:node . .

# App listens on 3333 by default
EXPOSE 3333

# Run as non-root for better security
USER node

CMD ["sh", "-c", "node commands.js && exec node app.js"]
