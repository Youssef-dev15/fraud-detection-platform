package org.example.backend.review.repository;

import org.example.backend.review.model.TransactionReview;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface TransactionReviewRepository extends JpaRepository<TransactionReview, UUID> {}