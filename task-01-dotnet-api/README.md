This is a [ASP.NET Core WebAPI](https://dotnet.microsoft.com/en-us/apps/aspnet/apis) project bootstrapped with `dotnet` cli.

## To start in general way

Install dependencies:

```bash
dotnet restore
```

To run the development server:

```bash
dotnet run
```

For production build, run:

```bash
# Build in release mode
dotnet publish -c Release

# Run the app
dotnet ./bin/Release/net10.0/publish/testdotnet-webapi.dll
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## To start systemd service

## To run using docker

```sh
# Build the image
docker build -t dotnet-webapi .

# Run the container. NOTE: make sure the port is available.
docker run -p 5000:8080 dotnet-webapi:latest
```

Open [http://localhost:5000](http://localhost:3000) with your browser to see the result.
