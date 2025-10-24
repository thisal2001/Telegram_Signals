# ----------------------------
# 1️⃣ Build stage
# ----------------------------
FROM maven:3.9.9-eclipse-temurin-17 AS build

WORKDIR /app

# Copy Maven project files
COPY pom.xml ./
COPY src ./src

# Build the Spring Boot app (skip tests for faster deploy)
RUN mvn clean package -DskipTests


# ----------------------------
# 2️⃣ Runtime stage
# ----------------------------
FROM openjdk:17-jdk-slim

WORKDIR /app

# Copy the built JAR from the previous stage
COPY --from=build /app/target/*.jar app.jar

# Set the runtime port
ENV PORT=8080
EXPOSE 8080

# Run the app
ENTRYPOINT ["java", "-jar", "app.jar"]
