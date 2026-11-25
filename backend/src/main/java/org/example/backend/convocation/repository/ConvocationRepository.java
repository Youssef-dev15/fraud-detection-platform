package org.example.backend.convocation.repository;

import org.example.backend.convocation.model.Convocation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface ConvocationRepository extends JpaRepository<Convocation, UUID> {
}
