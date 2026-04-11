---
name: Java Build Tools — Maven & Gradle
trigger: maven, gradle, pom.xml, build.gradle, dependency management, maven lifecycle, gradle task, maven plugin, gradle plugin, java build, mvn, artifactory, maven repository, gradle wrapper, multi-module
description: Build, test, and package Java projects with Maven and Gradle. Covers project structure, dependency management, lifecycle/tasks, plugins, multi-module projects, and the key differences between the two.
---

# ROLE
You are a senior Java engineer. Your job is to help developers set up and manage Java builds correctly using Maven or Gradle — resolving dependencies cleanly, running the right lifecycle phases, and avoiding dependency hell.

# MAVEN vs GRADLE AT A GLANCE
```
              MAVEN                      GRADLE
Structure     XML (pom.xml)              Groovy/Kotlin DSL (build.gradle)
Model         Declarative                Declarative + imperative (scripts)
Speed         Slower (no cache by default) Faster (incremental builds, build cache)
Flexibility   Convention-heavy           Very flexible
IDE Support   Excellent                  Excellent
Ecosystem     Mature, huge plugin library Large and growing
Spring Boot   Default in Spring Initializr  Also first-class supported
Android       Not used                   Official Android build tool

RULE: Both are fine for backend Java. Maven = less to learn, more predictable.
      Gradle = faster builds, preferred for large multi-module or Android projects.
```

# MAVEN

## Project Structure
```
my-project/
  pom.xml                  ← project descriptor
  src/
    main/
      java/                ← application source
      resources/           ← application resources (application.yml, etc.)
    test/
      java/                ← test source
      resources/           ← test resources
  target/                  ← compiled output (gitignored)
```

## pom.xml Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
             http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <!-- Spring Boot parent — manages all dependency versions -->
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>

    <properties>
        <java.version>21</java.version>
        <mapstruct.version>1.5.5.Final</mapstruct.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <!-- version managed by parent -->
        </dependency>

        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>   <!-- not transitive -->
        </dependency>

        <!-- Test scope — not included in final jar -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

## Maven Lifecycle & Commands
```bash
mvn validate          # validate project structure
mvn compile           # compile src/main/java
mvn test              # compile and run tests
mvn package           # compile, test, package into .jar/.war
mvn verify            # run integration tests
mvn install           # package + install to local ~/.m2 repo
mvn deploy            # install + deploy to remote repo

# Skipping tests (use sparingly)
mvn package -DskipTests
mvn package -Dmaven.test.skip=true   # skip compile AND run

# Profiles
mvn package -Pprod       # activate 'prod' profile
mvn package -Pdev,docker # multiple profiles

# Dependency commands
mvn dependency:tree                  # show full dependency tree
mvn dependency:tree -Dincludes=org.springframework  # filter
mvn dependency:analyze               # find unused declared / used undeclared
mvn versions:display-dependency-updates  # show available updates

# Clean (delete target/)
mvn clean package   # clean before build — always in CI
```

## Dependency Scopes
```
compile   → default, in classpath everywhere (compile, test, runtime, final jar)
provided  → available at compile time but provided by runtime (servlet-api — not in jar)
runtime   → not needed at compile, needed at runtime (JDBC driver)
test      → test code only, not in final jar (JUnit, Mockito)
optional  → not transitive to dependents (Lombok)
import    → used in <dependencyManagement> to import a BOM
```

## Multi-Module Maven Project
```xml
<!-- Parent pom.xml -->
<packaging>pom</packaging>
<modules>
    <module>common</module>
    <module>service</module>
    <module>api</module>
</modules>

<dependencyManagement>
    <dependencies>
        <!-- Pin versions centrally — child modules inherit without specifying version -->
        <dependency>
            <groupId>com.example</groupId>
            <artifactId>common</artifactId>
            <version>${project.version}</version>
        </dependency>
    </dependencies>
</dependencyManagement>

<!-- Child module pom.xml -->
<parent>
    <groupId>com.example</groupId>
    <artifactId>my-app-parent</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</parent>
<artifactId>service</artifactId>
```

# GRADLE

## Project Structure
```
my-project/
  build.gradle(.kts)       ← build script
  settings.gradle(.kts)    ← project name, subprojects
  gradle/
    wrapper/
      gradle-wrapper.jar
      gradle-wrapper.properties   ← Gradle version pinned here
  src/                     ← same as Maven
  build/                   ← output (gitignored)
```

## build.gradle (Kotlin DSL — modern, type-safe)
```kotlin
plugins {
    id("java")
    id("org.springframework.boot") version "3.2.0"
    id("io.spring.dependency-management") version "1.1.4"
}

group   = "com.example"
version = "1.0.0-SNAPSHOT"

java { sourceCompatibility = JavaVersion.VERSION_21 }

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")
    runtimeOnly("org.postgresql:postgresql")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

## Gradle Commands
```bash
./gradlew build           # compile, test, package
./gradlew test            # run tests only
./gradlew bootRun         # run Spring Boot app
./gradlew clean build     # clean then build
./gradlew dependencies    # dependency tree
./gradlew dependencyInsight --dependency spring-core  # why is this dep included?

# Task info
./gradlew tasks           # list available tasks
./gradlew help --task test

# Build scan (detailed report at scan.gradle.com)
./gradlew build --scan
```

## Gradle Dependency Configurations
```
implementation    → compile + runtime, NOT exposed to consumers (prefer over compile)
api               → exposed to consumers (for library projects)
compileOnly       → compile only, not runtime (like Maven 'provided')
runtimeOnly       → runtime only (JDBC driver)
testImplementation → test compile + runtime
annotationProcessor → annotation processor classpath (Lombok, MapStruct)
```

# AVOIDING DEPENDENCY HELL

## Version Conflicts
```bash
# Maven — find conflicting versions
mvn dependency:tree -Dverbose | grep "conflict"

# Gradle
./gradlew dependencies | grep " -> "   # shows version resolution

# Force a version in Maven (use sparingly)
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.16.1</version>
        </dependency>
    </dependencies>
</dependencyManagement>

# Force a version in Gradle
configurations.all {
    resolutionStrategy.force("com.fasterxml.jackson.core:jackson-databind:2.16.1")
}
```

## BOM (Bill of Materials) — Version Alignment
```xml
<!-- Maven — import Spring Cloud BOM -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-dependencies</artifactId>
            <version>2023.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

```kotlin
// Gradle — import BOM
implementation(platform("org.springframework.cloud:spring-cloud-dependencies:2023.0.0"))
implementation("org.springframework.cloud:spring-cloud-starter-openfeign")  // no version needed
```

# BEST PRACTICES CHECKLIST
```
[ ] Always use the Gradle wrapper (./gradlew) or Maven wrapper (./mvnw) — never system mvn/gradle
[ ] Pin the Gradle version in gradle-wrapper.properties
[ ] Use a Spring Boot parent POM or BOM — stop specifying library versions manually
[ ] Run mvn clean package or ./gradlew clean build in CI — always clean in CI
[ ] Never commit target/ or build/ directories — always gitignore them
[ ] Use dependency:tree / ./gradlew dependencies to diagnose conflict before adding exclusions
[ ] Use <dependencyManagement> or platform() BOM to align versions centrally
[ ] Set Java source/target version explicitly — don't rely on JDK default
[ ] Multi-module: pin all internal module versions in parent's dependencyManagement
[ ] Use -DskipTests only when you know the tests are irrelevant — never routinely
```
