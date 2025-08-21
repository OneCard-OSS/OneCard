FROM node:20-alpine AS builder


WORKDIR /usr/src/app


COPY package*.json ./


RUN npm install

COPY . .


FROM node:20-alpine

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/node_modules ./node_modules


COPY --from=builder /usr/src/app ./

EXPOSE 5000

CMD [ "npm", "start" ]

