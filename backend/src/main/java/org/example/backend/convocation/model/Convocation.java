package org.example.backend.convocation.model;

import jakarta.persistence.*;
import lombok.*;
import org.example.backend.convocation.enums.ConvocationStatus;
import org.example.backend.user.model.User;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "convocations")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Convocation {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "triggered_rule", nullable = false, length = 50)
    private String triggeredRule; // e.g. "3 in 7 days"

    @Column(name = "blocked_count", nullable = false)
    private int blockedCount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private ConvocationStatus status = ConvocationStatus.OPEN;

    @Column(name = "appointment_date")
    private Instant appointmentDate;

    @Column(length = 100)
    private String agency;

    @Column(name = "resolution_comment", columnDefinition = "TEXT")
    private String resolutionComment;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "resolved_by")
    private User resolvedBy;

    @Column(name = "resolved_at")
    private Instant resolvedAt;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}