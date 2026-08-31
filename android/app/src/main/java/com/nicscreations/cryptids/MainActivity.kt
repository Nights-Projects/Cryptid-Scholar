package com.nicscreations.cryptids

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Environment
import android.util.Log
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

// --- Data Models ---
data class ApiStats(
    val total: Int,
    val aquatic: Int,
    val terrestrial: Int,
    val flying: Int,
    val countries: List<CountryCount>? = null,
    val types: List<TypeCount>? = null
)

data class CountryCount(val country: String, val cnt: Int)
data class TypeCount(val type: String, val cnt: Int)

data class CryptidList(val cryptids: List<Cryptid>, val total: Int, val page: Int, val per_page: Int, val pages: Int)
data class Cryptid(
    val id: Int,
    val name: String,
    val type: String,
    val country: String? = null,
    val location: String? = null,
    val other_names: String? = null,
    val description: String? = null,
    val fact: String? = null,
    val tips: String? = null,
    val image_url: String? = null,
    val source_url: String? = null
)

// --- API Service ---
interface CryptidApiService {
    @GET("stats")
    fun getStats(): Call<ApiStats>

    @GET("cryptids")
    fun getCryptids(
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 50,
        @Query("type") type: String? = null,
        @Query("search") search: String? = null
    ): Call<CryptidList>

    @GET("cryptids/all")
    fun getAllCryptids(): Call<CryptidList>

    @GET("cryptids/{id}")
    fun getCryptid(@Path("id") id: Int): Call<Cryptid>
}

// --- Retrofit Client ---
object RetrofitClient {
    val apiService: CryptidApiService by lazy {
        Retrofit.Builder()
            .baseUrl(CryptidApp.API_BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(CryptidApiService::class.java)
    }
}

// --- Debug Logger ---
/**
 * Rotating log file manager.
 * Writes logs to /documents/cryptid-scholar-logs/ directory.
 * Each log file is capped at 8MB with rotation across 3 files.
 * Only active when BuildConfig.ENABLE_DEBUG_LOGGING is true (debug builds).
 */
object AppLogger {
    private const val TAG = "CryptidScholar"
    private const val MAX_FILE_SIZE_BYTES: Long = 8 * 1024 * 1024  // 8MB
    private const val MAX_LOG_FILES = 3

    private val logExecutor = java.util.concurrent.Executors.newSingleThreadExecutor()

    fun log(message: String) {
        if (!BuildConfig.ENABLE_DEBUG_LOGGING) return

        Log.d(TAG, message)

        val timestamp = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date())
        val fullMessage = "[$timestamp] $message\n"

        logExecutor.execute {
            try {
                val docsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
                val logDir = java.io.File(docsDir, BuildConfig.LOG_DIR_NAME)
                if (!logDir.exists()) {
                    logDir.mkdirs()
                }

                val currentLog = java.io.File(logDir, "debug.log")
                val backup1 = java.io.File(logDir, "debug-1.log")
                val backup2 = java.io.File(logDir, "debug-2.log")

                // Rotate if current log exceeds max size
                if (currentLog.exists() && currentLog.length() > MAX_FILE_SIZE_BYTES) {
                    backup2.delete()
                    backup1.renameTo(backup2)
                    currentLog.renameTo(backup1)
                }

                // Limit total number of log files
                val files = logDir.listFiles { _, name -> name.startsWith("debug") && name.endsWith(".log") }
                files?.sortBy { it.name }
                if (files != null && files.size > MAX_LOG_FILES) {
                    for (i in 0 until files.size - MAX_LOG_FILES) {
                        files[i].delete()
                    }
                }

                java.io.FileOutputStream(currentLog, true).use { out ->
                    out.write(fullMessage.toByteArray(Charsets.UTF_8))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to write log: ${e.message}")
            }
        }
    }

    fun getLogFiles(): Array<java.io.File>? {
        if (!BuildConfig.ENABLE_DEBUG_LOGGING) return null
        val docsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
        val logDir = java.io.File(docsDir, BuildConfig.LOG_DIR_NAME)
        return logDir.listFiles { _, name -> name.startsWith("debug") && name.endsWith(".log") }
    }

    fun getLatestLogContent(): String {
        if (!BuildConfig.ENABLE_DEBUG_LOGGING) return "Debug logging not enabled"
        try {
            val docsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
            val logDir = java.io.File(docsDir, BuildConfig.LOG_DIR_NAME)
            val currentLog = java.io.File(logDir, "debug.log")
            if (!currentLog.exists()) return "No log file found"
            return currentLog.readText(Charsets.UTF_8)
        } catch (e: Exception) {
            return "Error reading log: ${e.message}"
        }
    }

    fun clearLogs() {
        logExecutor.execute {
            try {
                val docsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
                val logDir = java.io.File(docsDir, BuildConfig.LOG_DIR_NAME)
                logDir.listFiles()?.forEach { it.delete() }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to clear logs: ${e.message}")
            }
        }
    }
}

// --- Simple Adapter ---
class CryptidAdapter(private val cryptids: List<Cryptid>) : RecyclerView.Adapter<CryptidViewHolder>() {
    override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): CryptidViewHolder {
        val view = android.view.LayoutInflater.from(parent.context)
            .inflate(R.layout.item_cryptid, parent, false)
        return CryptidViewHolder(view)
    }

    override fun onBindViewHolder(holder: CryptidViewHolder, position: Int) {
        holder.bind(cryptids[position])
    }

    override fun getItemCount() = cryptids.size
}

class CryptidViewHolder(view: View) : RecyclerView.ViewHolder(view) {
    private val nameText: TextView = view.findViewById(R.id.cryptidName)
    private val typeText: TextView = view.findViewById(R.id.cryptidType)
    private val countryText: TextView = view.findViewById(R.id.cryptidCountry)
    private val descriptionText: TextView = view.findViewById(R.id.cryptidDescription)

    fun bind(cryptid: Cryptid) {
        nameText.text = cryptid.name
        
        // Determine habitat icon based on type
        val icon = when (cryptid.type.lowercase()) {
            "aquatic" -> "🌊"
            "flying" -> "🦇"
            "terrestrial" -> "🦖"
            else -> "🦕"
        }
        typeText.text = "$icon ${cryptid.type}"
        
        countryText.text = cryptid.country?.let { " • $it" } ?: ""
        
        descriptionText.text = cryptid.description ?: cryptid.fact ?: cryptid.tips ?: ""
    }
}

// --- MainActivity ---
class MainActivity : AppCompatActivity() {
    private lateinit var recyclerView: RecyclerView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var statsText: TextView
    private lateinit var adapter: CryptidAdapter
    private val cryptidList = mutableListOf<Cryptid>()
    private val PERMISSIONS_REQUEST_CODE = 100

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        recyclerView = findViewById(R.id.recyclerView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        statsText = findViewById(R.id.statsText)
        
        // Initialize debug logging for debug builds
        if (BuildConfig.ENABLE_DEBUG_LOGGING) {
            checkLogPermissionsAndInit()
        }

        AppLogger.log("MainActivity onCreate")

        adapter = CryptidAdapter(cryptidList)
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        swipeRefresh.setOnRefreshListener {
            fetchData()
        }

        fetchData()
    }

    private fun checkLogPermissionsAndInit() {
        // On Android 10+ (API 29+), scoped storage means we don't need WRITE_EXTERNAL_STORAGE
        // but for older devices, we request it for debug log writing
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            AppLogger.log("Skipping WRITE_EXTERNAL_STORAGE (Android 10+ scoped storage)")
            return
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE),
                PERMISSIONS_REQUEST_CODE
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSIONS_REQUEST_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                AppLogger.log("WRITE_EXTERNAL_STORAGE permission granted")
            } else {
                AppLogger.log("WRITE_EXTERNAL_STORAGE permission denied - logs will not be written to /documents")
            }
        }
    }

    private fun fetchData() {
        swipeRefresh.isRefreshing = true
        AppLogger.log("Fetching cryptid data...")

        // Fetch stats
        RetrofitClient.apiService.getStats().enqueue(object : Callback<ApiStats> {
            override fun onResponse(call: Call<ApiStats>, response: Response<ApiStats>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    statsText.text = "📊 ${stats.total} cryptids • 🌊 ${stats.aquatic} Aquatic • 🦖 ${stats.terrestrial} Terrestrial • 🦇 ${stats.flying} Flying"
                    AppLogger.log("Stats loaded: total=${stats.total}, aquatic=${stats.aquatic}, terrestrial=${stats.terrestrial}, flying=${stats.flying}")
                } else {
                    AppLogger.log("Failed to load stats: HTTP ${response.code()}")
                    Toast.makeText(this@MainActivity, "Failed to load stats", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<ApiStats>, t: Throwable) {
                AppLogger.log("Stats API error: ${t.message}")
                Toast.makeText(this@MainActivity, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })

        // Fetch cryptid list
        RetrofitClient.apiService.getAllCryptids().enqueue(object : Callback<CryptidList> {
            override fun onResponse(call: Call<CryptidList>, response: Response<CryptidList>) {
                swipeRefresh.isRefreshing = false
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    cryptidList.clear()
                    cryptidList.addAll(result.cryptids)
                    adapter.notifyDataSetChanged()
                    AppLogger.log("Cryptids loaded: ${result.cryptids.size} items (total: ${result.total})")
                } else {
                    AppLogger.log("Failed to load cryptids: HTTP ${response.code()}")
                    Toast.makeText(this@MainActivity, "Failed to load cryptids", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<CryptidList>, t: Throwable) {
                swipeRefresh.isRefreshing = false
                AppLogger.log("Cryptid API error: ${t.message}")
                Toast.makeText(this@MainActivity, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }
}