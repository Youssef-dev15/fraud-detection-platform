package org.example.backend.transaction.model;

import jakarta.persistence.*;
import lombok.*;
import org.example.backend.account.model.Account;
import org.example.backend.transaction.enums.ScoringStatus;
import org.example.backend.transaction.enums.TransactionStatus;
import org.example.backend.transaction.enums.TransactionType;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "transactions", indexes = {
        // Analyst queue
        @Index(name = "idx_tx_status_created", columnList = "status, created_at"),
        // Sliding-window counts for convocations
        @Index(name = "idx_tx_origin_status_dt", columnList = "origin_account_id, status, created_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Transaction {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "origin_account_id", nullable = false)
    private Account originAccount;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "dest_account_id")
    private Account destAccount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private TransactionType type;

    @Column(nullable = false, precision = 15, scale = 3)
    private BigDecimal amount;

    @Column(nullable = false, length = 3)
    @Builder.Default
    private String currency = "TND";

    // Balance snapshot at scoring time. "new" values are PROJECTED:
    // real balances change only after the transaction is validated.
    @Column(name = "old_balance_orig", nullable = false, precision = 15, scale = 3)
    private BigDecimal oldBalanceOrig;

    @Column(name = "new_balance_orig", nullable = false, precision = 15, scale = 3)
    private BigDecimal newBalanceOrig;

    @Column(name = "old_balance_dest", nullable = false, precision = 15, scale = 3)
    @Builder.Default
    private BigDecimal oldBalanceDest = BigDecimal.ZERO;

    @Column(name = "new_balance_dest", nullable = false, precision = 15, scale = 3)
    @Builder.Default
    private BigDecimal newBalanceDest = BigDecimal.ZERO;

    // Scoring result (null when the scoring service is unavailable)
    @Column(name = "risk_score", precision = 5, scale = 4)
    private BigDecimal riskScore;

    @Enumerated(EnumType.STRING)
    @Column(name = "scoring_status", nullable = false, length = 20)
    @Builder.Default
    private ScoringStatus scoringStatus = ScoringStatus.OK;

    @Column(name = "model_version", length = 30)
    private String modelVersion;

    // Features sent to the model (audit + future retraining)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "features_snapshot", columnDefinition = "jsonb")
    private Map<String, Object> featuresSnapshot;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private TransactionStatus status;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "decided_at")
    private Instant decidedAt;
}