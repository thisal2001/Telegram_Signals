package com.example.binance_trader.repository;

import com.example.binance_trader.model.Signal;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SignalRepository extends JpaRepository<Signal, Long> {
    Signal findTopByOrderByTimestampDesc();
}
