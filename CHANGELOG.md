<!-- SPDX-License-Identifier: MIT
Copyright (c) 2025 Perday CatalogLAB™ -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-09-23

### Added
- Initial release of music title parser
- Three-tier parsing system (strict/balanced/aggressive profiles)
- YouTube Official Artist Channel (OAC) support
- Garbage artist detection and prevention
- Policy-based confidence scoring with configurable thresholds
- Type-safe parsing results using Pydantic v2 models
- CLI tools for parsing and validation
- Comprehensive benchmarking suite
- Production-ready configuration with TTL and ownership
- Full type annotations and py.typed marker
- Medallion architecture support (Bronze/Silver/Gold)
- Performance optimizations (50,000+ titles/second)
- Comprehensive test suite with >90% coverage

### Security
- Input validation and sanitization
- Regex timeout protection
- Trusted PyPI publishing with OIDC
- CodeQL security scanning

[Unreleased]: https://github.com/perday/music-title-parser/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/perday/music-title-parser/releases/tag/v0.1.0
