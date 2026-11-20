FROM node:22-alpine

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy all files
COPY . .

# Expose Vite default port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev", "--", "--host"]
