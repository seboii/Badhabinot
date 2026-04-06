# syntax=docker/dockerfile:1.7

FROM maven:3.9.9-eclipse-temurin-21 AS build
ARG SERVICE_MODULE
ARG SERVICE_ARTIFACT

WORKDIR /workspace

COPY pom.xml pom.xml
COPY apps/backend/api-gateway/pom.xml apps/backend/api-gateway/pom.xml
COPY apps/backend/auth-service/pom.xml apps/backend/auth-service/pom.xml
COPY apps/backend/user-service/pom.xml apps/backend/user-service/pom.xml
COPY apps/backend/monitoring-service/pom.xml apps/backend/monitoring-service/pom.xml

RUN --mount=type=cache,target=/root/.m2 mvn -B -ntp -pl ${SERVICE_MODULE} -am dependency:go-offline

COPY apps/backend apps/backend

RUN --mount=type=cache,target=/root/.m2 mvn -B -ntp -pl ${SERVICE_MODULE} -am package -DskipTests

FROM eclipse-temurin:21-jre-jammy AS runtime
ARG SERVICE_MODULE
ARG SERVICE_ARTIFACT

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app app

COPY --from=build /workspace/${SERVICE_MODULE}/target/${SERVICE_ARTIFACT}-0.1.0-SNAPSHOT.jar /app/app.jar

RUN chown -R app:app /app

USER app
ENV JAVA_OPTS=""

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
