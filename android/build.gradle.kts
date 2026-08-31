buildscript {
    val composeVersion = "2024.10.00"
    val kotlinVersion = "2.1.0"
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
