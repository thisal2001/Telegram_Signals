package com.example.binance_trader.config;

import com.binance.connector.futures.client.impl.UMFuturesClientImpl;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class BinanceConfig {

    @Value("${BINANCE_API_KEY}")
    private String apiKey;

    @Value("${BINANCE_SECRET_KEY}")
    private String secretKey;

    @Value("${BINANCE_BASE_URL}")
    private String baseUrl;

    @Bean
    public UMFuturesClientImpl binanceFuturesClient() {
        return new UMFuturesClientImpl(apiKey, secretKey, baseUrl);
    }
}
