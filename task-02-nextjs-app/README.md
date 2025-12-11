This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## To start in general way

Install dependencies:

```bash
npm install
or 
bun install
```

To run the development server:

```bash
npm run dev
# or
bun dev
```

For production build, run:

```bash
npm run build
# or
bun run build

# then start the server by running
npm start
or 
bun start
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## To start systemd service

## To run using docker

```sh
# Build the image
docker build -t nextjs-app .

# Run the container. NOTE: make sure the port is available.
docker run -p 3000:3000 nextjs-app:latest
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

