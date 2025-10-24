package com.example.binance_trader.Service;

import com.example.binance_trader.model.Signal;
import com.example.binance_trader.repository.SignalRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class TradeExecutor {

    private final SignalRepository signalRepository;
    private final BinanceService binanceService;

    // Track the last executed signal ID in memory
    private Long lastExecutedSignalId = null;

    public TradeExecutor(SignalRepository signalRepository, BinanceService binanceService) {
        this.signalRepository = signalRepository;
        this.binanceService = binanceService;
    }

    // Scheduled task: runs every 1 minute
    @Scheduled(fixedRate = 60000)
    public void executeLatestSignal() {
        try {
            // Fetch the latest signal from the database
            Signal signal = signalRepository.findTopByOrderByTimestampDesc();

            // Check if a new signal exists and hasn't been executed yet
            if (signal != null && !signal.getId().equals(lastExecutedSignalId)) {
                log.info("Executing signal: {} {} at {}",
                        signal.getSetupType(), signal.getPair(), signal.getTimestamp());

                // Place the order through BinanceService
                binanceService.placeFuturesOrder(signal);

                // Remember last executed signal so it won't repeat
                lastExecutedSignalId = signal.getId();
            } else {
                log.debug("No new signals found or already executed.");
            }
        } catch (Exception e) {
            log.error("Error in scheduled task: ", e);
        }
    }
}
