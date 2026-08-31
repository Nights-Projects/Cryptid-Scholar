plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.1.0" apply false
}

buildscript {
    val kotlinVersion = "2.1.0"
    val composeVersion = "2024.10.00"
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlinVersion")
        classpath("androidx.compose:compose-bom:$composeVersion")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
