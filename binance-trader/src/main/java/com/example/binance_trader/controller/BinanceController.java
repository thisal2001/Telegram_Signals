package com.example.binance_trader.controller;

import com.example.binance_trader.Service.BinanceService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/binance")
@RequiredArgsConstructor
@Slf4j
public class BinanceController {

    @Autowired
    private BinanceService binanceService;

//    // Get user trades
//    @GetMapping("/userTrades")
//    public Object getUserTrades(String symbol) {
//        return binanceService.getUserTrades(symbol);
//    }
//
//    @GetMapping("/positionRisk")
//    public Object getPositionRisk(String symbol) {
//        return binanceService.getPositionRisk(symbol);
//    }
//
//    // Get account balance
//    @GetMapping("/account")
//    public double getAccount() {
//        return binanceService.checkBalance();
//    }
//
//    @GetMapping("/executionInfo")
//    public Object getExecutionInfo(String symbol) {
//        return binanceService.getOpenOrders(symbol);
//    }
//
//    @GetMapping("/accountInfo")
//    public Object getAccountInfo() {
//        return binanceService.getAccountInfo();
//    }

}