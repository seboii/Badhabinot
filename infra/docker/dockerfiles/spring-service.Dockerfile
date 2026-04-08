# syntax=docker/dockerfile:1.7

FROM maven:3.9.9-eclipse-temurin-21 AS build

WORKDIR /workspace/backend

COPY backend/pom.xml pom.xml

RUN --mount=type=cache,target=/root/.m2 mvn -B -ntp dependency:go-offline

COPY backend/src src

RUN --mount=type=cache,target=/root/.m2 mvn -B -ntp package -DskipTests

FROM eclipse-temurin:21-jre-jammy AS runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app app

COPY --from=build /workspace/backend/target/badhabinot-backend-0.1.0-SNAPSHOT.jar /app/app.jar

RUN chown -R app:app /app

USER app
ENV JAVA_OPTS=""

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
