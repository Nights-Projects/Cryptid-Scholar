package com.nicscreations.cryptids

import android.os.Build
import android.os.Environment
import android.util.Log
import java.io.*
import java.text.SimpleDateFormat
import java.util.*

/**
 * Rotating debug log file handler.
 * Writes logs to /documents/cryptid-scholar-logs/debug.log with 8MB rotation.
 * Only active when BuildConfig.DEBUG is true.
 */
object DebugLogger {
    private const val TAG = "CryptidScholar-Debug"
    private const val LOG_DIR = "cryptid-scholar-logs"
    private const val LOG_FILE = "debug.log"
    private const val MAX_LOG_SIZE_BYTES = 8 * 1024 * 1024  // 8MB
    private const val MAX_BACKUP_FILES = 3

    private var logDir: File? = null

    fun init() {
        if (!BuildConfig.DEBUG) return

        logDir = File(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS),
            LOG_DIR
        ).apply { mkdirs() }

        val logFile = File(logDir, LOG_FILE)
        rotateIfNeeded(logFile)

        val writer = FileWriter(logFile, true)
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        write(writer, "[$timestamp] === Debug logging initialized ===")
        write(writer, "  Device: ${Build.MANUFACTURER} ${Build.MODEL}")
        write(writer, "  Android: ${Build.VERSION.RELEASE} (SDK ${Build.VERSION.SDK_INT})")
        write(writer, "  App versionCode: ${BuildConfig.VERSION_CODE}")
        writer.flush()
        writer.close()
    }

    fun log(tag: String, message: String) {
        if (!BuildConfig.DEBUG) return
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        val thread = Thread.currentThread().name
        writeFile("[$timestamp] [$thread] [$tag] $message")
        Log.d(TAG, message)
    }

    fun logError(tag: String, message: String, throwable: Throwable? = null) {
        if (!BuildConfig.DEBUG) return
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US).format(Date())
        val thread = Thread.currentThread().name
        val sb = StringBuilder()
        sb.append("[$timestamp] [$thread] [$tag] ERROR: $message")
        throwable?.let {
            sb.append("\n  Exception: ${it.javaClass.name}: ${it.message}")
            for (element in it.stackTrace) {
                sb.append("\n    at ${element.className}.${element.methodName}(${element.fileName}:${element.lineNumber})")
            }
        }
        writeFile(sb.toString())
        Log.e(TAG, message, throwable)
    }

    fun logNetwork(tag: String, url: String, method: String, responseCode: Int? = null, durationMs: Long? = null) {
        if (!BuildConfig.DEBUG) return
        val parts = mutableListOf<String>()
        parts.add("$method $url")
        responseCode?.let { parts.add("HTTP $it") }
        durationMs?.let { parts.add("${it}ms") }
        log(tag, parts.joinToString(" | "))
    }

    private fun writeFile(message: String) {
        val logFile = File(logDir, LOG_FILE)
        rotateIfNeeded(logFile)
        FileWriter(logFile, true).use { writer ->
            writer.write("$message\n")
            writer.flush()
        }
    }

    private fun rotateIfNeeded(logFile: File) {
        if (!logFile.exists()) return
        if (logFile.length() < MAX_LOG_SIZE_BYTES.toLong()) return

        for (i in MAX_BACKUP_FILES downTo 2) {
            val oldFile = File(logDir, "${LOG_FILE}.${i - 1}")
            val newFile = File(logDir, "${LOG_FILE}.$i")
            if (oldFile.exists()) {
                oldFile.delete()
            }
            if (i > 1) {
                val prevFile = File(logDir, "${LOG_FILE}.${i - 2}")
                if (prevFile.exists()) {
                    prevFile.renameTo(newFile)
                }
            }
        }

        val currentLog = File(logDir, LOG_FILE)
        val backup1 = File(logDir, "${LOG_FILE}.1")
        if (currentLog.exists()) {
            currentLog.renameTo(backup1)
        }
    }
}