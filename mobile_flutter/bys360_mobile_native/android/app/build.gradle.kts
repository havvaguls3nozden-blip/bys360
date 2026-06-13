// BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_GRADLE_BEGIN
import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

val bys360ReleaseKeystoreProperties = Properties()
val bys360ReleaseKeystorePropertiesFile = rootProject.file("key.properties")
if (bys360ReleaseKeystorePropertiesFile.exists()) {
    FileInputStream(bys360ReleaseKeystorePropertiesFile).use { stream ->
        bys360ReleaseKeystoreProperties.load(stream)
    }
}

if (file("google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
}


android {
    namespace = "tr.gov.canakkaletarihialan.bys360.mobile"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    defaultConfig {
        applicationId = "tr.gov.canakkaletarihialan.bys360.mobile"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            val storeFilePath = bys360ReleaseKeystoreProperties.getProperty("storeFile")
            if (!storeFilePath.isNullOrBlank()) {
                storeFile = rootProject.file(storeFilePath)
            }
            storePassword = bys360ReleaseKeystoreProperties.getProperty("storePassword")
            keyAlias = bys360ReleaseKeystoreProperties.getProperty("keyAlias")
            keyPassword = bys360ReleaseKeystoreProperties.getProperty("keyPassword")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            isShrinkResources = false
            if (bys360ReleaseKeystorePropertiesFile.exists()) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }
}

flutter {
    source = "../.."
}

// BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_GRADLE_END
