package com.nicscreations.cryptids

import android.os.Bundle
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.bottomnavigation.BottomNavigationView
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
    val countries: List<CountryCount>?,
    val types: List<TypeCount>?
)

data class CountryCount(val country: String, val cnt: Int)
data class TypeCount(val type: String, val cnt: Int)

data class CryptidList(val cryptids: List<Cryptid>, val total: Int, val page: Int, val per_page: Int, val pages: Int)
data class Cryptid(
    val id: Int,
    val name: String,
    val type: String,
    val country: String?,
    val location: String?,
    val other_names: String?,
    val description: String?,
    val fact: String?,
    val tips: String?,
    val image_url: String?,
    val source_url: String?
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

    fun bind(cryptid: Cryptid) {
        nameText.text = cryptid.name
        typeText.text = cryptid.type
        countryText.text = cryptid.country ?: "Unknown"
    }
}

// --- MainActivity ---
class MainActivity : AppCompatActivity() {
    private lateinit var recyclerView: RecyclerView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var statsText: TextView
    private lateinit var adapter: CryptidAdapter
    private val cryptidList = mutableListOf<Cryptid>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        recyclerView = findViewById(R.id.recyclerView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        statsText = findViewById(R.id.statsText)

        adapter = CryptidAdapter(cryptidList)
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        swipeRefresh.setOnRefreshListener {
            fetchData()
        }

        fetchData()
    }

    private fun fetchData() {
        swipeRefresh.isRefreshing = true

        // Fetch stats
        RetrofitClient.apiService.getStats().enqueue(object : Callback<ApiStats> {
            override fun onResponse(call: Call<ApiStats>, response: Response<ApiStats>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    statsText.text = "📊 ${stats.total} cryptids • 🌊 ${stats.aquatic} Aquatic • 🦖 ${stats.terrestrial} Terrestrial • 🦇 ${stats.flying} Flying"
                } else {
                    Toast.makeText(this@MainActivity, "Failed to load stats", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<ApiStats>, t: Throwable) {
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
                } else {
                    Toast.makeText(this@MainActivity, "Failed to load cryptids", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<CryptidList>, t: Throwable) {
                swipeRefresh.isRefreshing = false
                Toast.makeText(this@MainActivity, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }
}
