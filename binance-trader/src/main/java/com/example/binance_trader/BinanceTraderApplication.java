package com.example.binance_trader;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class BinanceTraderApplication {

	public static void main(String[] args) {
		SpringApplication.run(BinanceTraderApplication.class, args);
	}

}
