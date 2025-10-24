package com.example.binance_trader.Service;

import com.binance.connector.futures.client.impl.UMFuturesClientImpl;
import com.example.binance_trader.model.Signal;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONObject;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.math.BigDecimal;
import java.util.concurrent.ConcurrentHashMap;

@Service
@Slf4j
public class BinanceService {

    private final UMFuturesClientImpl futuresClient;

    // dedupe map: symbol -> lastOrderEpochMillis
    private final ConcurrentHashMap<String, Long> lastOrderTimestamp = new ConcurrentHashMap<>();
    private final long DEDUP_TTL_MS = 30_000L; // block duplicates for 30 seconds

    public BinanceService(UMFuturesClientImpl futuresClient) {
        this.futuresClient = futuresClient;
    }

    /** ✅ Get USDT balance */
    public double getBalance() {
        try {
            LinkedHashMap<String, Object> params = new LinkedHashMap<>();
            params.put("recvWindow", 60000); // add recvWindow
            String result = futuresClient.account().futuresAccountBalance(params);
            var balances = new org.json.JSONArray(result);
            for (int i = 0; i < balances.length(); i++) {
                var balance = balances.getJSONObject(i);
                if ("USDT".equals(balance.getString("asset"))) {
                    double available = balance.getDouble("availableBalance");
                    log.info("USDT Balance: {}", available);
                    return available;
                }
            }
        } catch (Exception e) {
            log.error("Error fetching balance: ", e);
        }
        return 0.0;
    }

    /** ✅ Place a MARKET futures order with SL and TP according to signal */
    public void placeFuturesOrder(Signal signal) {
        try {
            double balance = getBalance();
            if (balance <= 0.5) {
                log.error("Not enough balance to trade. USDT={}", balance);
                return;
            }

            String symbol = signal.getPair().replace(".P", "");
            String side = signal.getSetupType().equalsIgnoreCase("LONG") ? "BUY" : "SELL";

            // simple in-memory dedupe: prevent re-processing the same symbol within TTL
            long now = System.currentTimeMillis();
            Long last = lastOrderTimestamp.get(symbol);
            if (last != null && (now - last) < DEDUP_TTL_MS) {
                log.warn("Duplicate order prevented for {} (last placed {} ms ago)", symbol, now - last);
                return;
            }
            
            // 1️⃣ Set leverage
            LinkedHashMap<String, Object> leverageParams = new LinkedHashMap<>();
            leverageParams.put("symbol", symbol);
            leverageParams.put("leverage", signal.getLeverage());
            leverageParams.put("recvWindow", 60000);
            futuresClient.account().changeInitialLeverage(leverageParams);
            log.info("Leverage set to {}x for {}", signal.getLeverage(), symbol);

            // 2️⃣ Calculate quantity with fixed $0.5 risk per trade
            // Use fixed position size (notional) instead of risk-based sizing
            double positionSizeUsd = 10.0; // $10 notional value
            if (signal.getEntry() <= 0) {
                log.error("Invalid entry price: {}", signal.getEntry());
                return;
            }

            // Get symbol info first (exchangeInfo() is parameterless in this SDK)
            String symbolInfo = futuresClient.market().exchangeInfo();
            JSONObject info = new JSONObject(symbolInfo);

            // Find the symbol object
            var symbolsArray = info.getJSONArray("symbols");
            JSONObject symbolObj = null;
            for (int i = 0; i < symbolsArray.length(); i++) {
                var s = symbolsArray.getJSONObject(i);
                if (symbol.equals(s.getString("symbol"))) {
                    symbolObj = s;
                    break;
                }
            }
            if (symbolObj == null) {
                log.error("Symbol info not found for {}", symbol);
                return;
            }

            // Determine quantity precision and minQty from LOT_SIZE filter if quantityPrecision not present
            int quantityPrecision;
            double minQty = 0.0;

            if (symbolObj.has("quantityPrecision")) {
                quantityPrecision = symbolObj.getInt("quantityPrecision");
            } else {
                // fallback: look for LOT_SIZE filter
                var filters = symbolObj.getJSONArray("filters");
                String stepSize = null;
                for (int i = 0; i < filters.length(); i++) {
                    var f = filters.getJSONObject(i);
                    if ("LOT_SIZE".equalsIgnoreCase(f.optString("filterType"))) {
                        stepSize = f.optString("stepSize", null);
                        minQty = f.optDouble("minQty", 0.0);
                        break;
                    }
                }
                if (stepSize != null) {
                    BigDecimal step = new BigDecimal(stepSize);
                    quantityPrecision = Math.max(0, step.stripTrailingZeros().scale());
                } else {
                    // safe default if nothing found
                    quantityPrecision = 3;
                }
            }

            // Calculate quantity with correct precision
            double rawQty = positionSizeUsd / signal.getEntry();
            double qty = Math.floor(rawQty * Math.pow(10, quantityPrecision)) / Math.pow(10, quantityPrecision);

            log.info("Using quantity precision: {} decimals (minQty={})", quantityPrecision, minQty);

            // Enforce minQty if available
            if (minQty > 0 && qty < minQty) {
                qty = minQty;
                log.warn("Quantity adjusted to symbol minQty: {}", qty);
            }

            // Some pairs may still require a small minimum (sensible fallback)
            if (qty < 0.000001) { // very small fallback
                qty = 0.000001;
                log.warn("Quantity adjusted to very small fallback: {}", qty);
            }

            if (qty <= 0) {
                log.error("Quantity too small to trade. Qty={}", qty);
                return;
            }

            log.info("Calculated quantity: {} (based on fixed ${} risk)", qty, positionSizeUsd);

            // 🧮 Calculate and log position size and margin size
            double positionSize = signal.getEntry() * qty;
            double marginSize = positionSize / signal.getLeverage();

            log.info("Position Size (Notional): ${}", positionSize);
            log.info("Required Margin (with {}x): ${}", signal.getLeverage(), marginSize);


            // 3️⃣ Place MARKET order
            LinkedHashMap<String, Object> orderParams = new LinkedHashMap<>();
            orderParams.put("symbol", symbol);
            orderParams.put("side", side);
            orderParams.put("type", "MARKET");
            orderParams.put("quantity", qty);
            orderParams.put("recvWindow", 60000);

            String orderResponse = futuresClient.account().newOrder(orderParams);
            JSONObject resp = new JSONObject(orderResponse);
            double executedQty = resp.optDouble("executedQty", 0.0);
            String status = resp.getString("status");

            log.info("Order placed: {} {} Qty={} Status={}", side, symbol, qty, status);

            if ("NEW".equals(status) && executedQty == 0.0) {
                log.warn("MARKET order not executed yet. Qty={}, consider retrying or using LIMIT.", qty);
                return;
            }

            // mark successful placement time for dedupe
            lastOrderTimestamp.put(symbol, System.currentTimeMillis());
            
            // 4️⃣ Place Stop-Loss
            if (!placeStopLoss(symbol, side, executedQty, signal.getStopLoss())) {
                log.error("SL failed, manual intervention required for {}", symbol);
                return;
            }

            // 5️⃣ Place Take-Profits
            if (signal.getTp1() > 0) placeTakeProfit(symbol, side, executedQty, signal.getTp1(), "TP1");
            if (signal.getTp2() > 0) placeTakeProfit(symbol, side, executedQty, signal.getTp2(), "TP2");
            if (signal.getTp3() > 0) placeTakeProfit(symbol, side, executedQty, signal.getTp3(), "TP3");
            if (signal.getTp4() > 0) placeTakeProfit(symbol, side, executedQty, signal.getTp4(), "TP4");

            log.info("✅ All orders placed for {}", symbol);

        } catch (Exception e) {
            log.error("Error placing order for {}: {}", signal.getPair(), e.getMessage());
        }
    }

    /** ✅ Place Stop-Loss order */
    private boolean placeStopLoss(String symbol, String side, double qty, double stopPrice) {
        try {
            String slSide = side.equals("BUY") ? "SELL" : "BUY";
            LinkedHashMap<String, Object> slParams = new LinkedHashMap<>();
            slParams.put("symbol", symbol);
            slParams.put("side", slSide);
            slParams.put("type", "STOP_MARKET");
            slParams.put("quantity", qty);
            slParams.put("stopPrice", stopPrice);
            slParams.put("timeInForce", "GTC");
            slParams.put("recvWindow", 60000);

            String resp = futuresClient.account().newOrder(slParams);
            log.info("Stop-Loss placed: {}", resp);
            return true;
        } catch (Exception e) {
            log.error("Error placing Stop-Loss for {}: {}", symbol, e.getMessage());
            return false;
        }
    }

    /** ✅ Place Take-Profit order */
    private void placeTakeProfit(String symbol, String side, double qty, double tpPrice, String label) {
        try {
            String tpSide = side.equals("BUY") ? "SELL" : "BUY";
            LinkedHashMap<String, Object> tpParams = new LinkedHashMap<>();
            tpParams.put("symbol", symbol);
            tpParams.put("side", tpSide);
            tpParams.put("type", "TAKE_PROFIT_MARKET");
            tpParams.put("quantity", qty);
            tpParams.put("stopPrice", tpPrice);
            tpParams.put("timeInForce", "GTC");
            tpParams.put("recvWindow", 60000);

            String resp = futuresClient.account().newOrder(tpParams);
            log.info("{} placed: {}", label, resp);
        } catch (Exception e) {
            log.error("Error placing {} for {}: {}", label, symbol, e.getMessage());
        }
    }
}
