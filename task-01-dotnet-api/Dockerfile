FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY ["testdotnet-webapi.csproj", "."] 
RUN dotnet restore

COPY . .
RUN dotnet publish "testdotnet-webapi.csproj" -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime

WORKDIR /app

COPY --from=build /app/publish .

RUN groupadd appgroup && useradd -G appgroup appuser
USER appuser

CMD ["dotnet", "testdotnet-webapi.dll"]

