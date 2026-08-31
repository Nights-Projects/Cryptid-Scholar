package com.nicscreations.cryptids

import android.app.Application

class CryptidApp : Application() {
    companion object {
        const val API_BASE_URL = "https://cryptids.nicscreations.com/api/"
    }
}
