package org.example.backend.review.model;

import jakarta.persistence.*;
import lombok.*;
import org.example.backend.review.enums.ReviewDecision;
import org.example.backend.transaction.model.Transaction;
import org.example.backend.user.model.User;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "transaction_reviews")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TransactionReview {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    // unique = true: only one final decision per transaction
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "transaction_id", nullable = false, unique = true)
    private Transaction transaction;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "analyst_id", nullable = false)
    private User analyst;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private ReviewDecision decision;

    @Column(columnDefinition = "TEXT")
    private String comment;

    @CreationTimestamp
    @Column(name = "reviewed_at", nullable = false, updatable = false)
    private Instant reviewedAt;
}