package com.example.binance_trader.model;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "signal_messages")
public class Signal {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String pair;
    private String setupType;
    private Double entry;
    private Integer leverage;

    @Column(name = "stop_loss")
    private Double stopLoss;

    @Column(name = "tp1")
    private Double tp1;

    @Column(name = "tp2")
    private Double tp2;

    @Column(name = "tp3")
    private Double tp3;

    @Column(name = "tp4")
    private Double tp4;

    private LocalDateTime timestamp;
    private Double quantity;

    private String fullMessage;   // maps full_message
}
