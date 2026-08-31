buildscript {
    ext {
        compose_version = '2024.10.00'
        kotlin_version = '2.1.0'
    }
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
        classpath "androidx.compose:compose-bom:BOM_VERSION"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
