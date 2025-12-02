# Implementation Plan

- [x] 1. Add npm script malicious pattern constants


  - Add lifecycle script names list to constants.py
  - Add malicious script patterns (remote code execution, pipe to shell, obfuscation)
  - Add benign script patterns (build tools, dev tools, safe file operations)
  - Add severity mapping for different pattern types
  - _Requirements: 1.2, 1.3, 1.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_


- [ ] 2. Implement script pattern detection function
  - Create `_detect_script_patterns()` function in sbom_tools.py
  - Implement regex matching for each malicious pattern type
  - Implement confidence score calculation based on pattern matches
  - Implement severity determination logic
  - Generate evidence strings for detected patterns
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.2, 2.3, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 2.1 Write property test for pattern detection
  - **Property 2: Network Pattern Detection**
  - **Property 3: Command Execution Detection**
  - **Property 4: Obfuscation Detection**
  - **Validates: Requirements 1.2, 1.3, 1.4**

- [ ] 2.2 Write property test for confidence calculation
  - **Property 5: Confidence Monotonicity**
  - **Property 9: Confidence Bounds**

  - **Validates: Requirements 1.5, 2.5**

- [ ] 3. Implement npm script analysis function
  - Create `_analyze_npm_scripts()` function in sbom_tools.py
  - Extract scripts field from package.json data
  - Filter for lifecycle scripts (preinstall, postinstall, etc.)
  - Call pattern detection for each script
  - Create SecurityFinding objects for malicious scripts
  - Add script name and content to evidence
  - Generate actionable recommendations
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 5.3, 5.4_

- [ ] 3.1 Write property test for script extraction
  - **Property 1: Complete Script Extraction**
  - **Validates: Requirements 1.1**

- [ ] 3.2 Write property test for finding structure
  - **Property 6: Evidence Completeness**
  - **Property 8: Recommendation Presence**


  - **Property 17: Finding Type Consistency**
  - **Validates: Requirements 2.1, 2.2, 2.4, 5.3**

- [ ] 4. Integrate script analysis into package extraction
  - Modify `_extract_npm_packages()` to return tuple of (packages, script_findings)
  - Call `_analyze_npm_scripts()` during package.json parsing
  - Update `extract_packages_from_file()` to handle script findings
  - Ensure script findings are added to the overall findings list
  - _Requirements: 1.1, 5.1, 5.2_

- [ ] 4.1 Write property test for severity assignment
  - **Property 7: Severity Assignment**
  - **Property 10: Encoded Command Severity**
  - **Property 11: System Modification Severity**
  - **Property 12: Suspicious Domain Severity**
  - **Property 13: Dynamic Execution Severity**
  - **Validates: Requirements 2.3, 3.1, 3.2, 3.3, 3.4, 3.5**

- [ ] 5. Implement false positive reduction
  - Add benign pattern detection to `_detect_script_patterns()`
  - Reduce confidence when benign patterns are present
  - Skip flagging scripts with only benign patterns
  - Add context-aware pattern matching
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 5.1 Write property test for false positive reduction
  - **Property 14: Benign Build Commands**
  - **Property 15: Development Tool Recognition**
  - **Property 16: Legitimate File Operations**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ] 6. Update local directory analysis
  - Ensure `analyze_local_directory()` includes script findings
  - Verify script findings appear in analysis results
  - Test with sample package.json containing malicious scripts
  - _Requirements: 5.1, 5.2_

- [ ] 6.1 Write property test for package association
  - **Property 18: Package Association**
  - **Validates: Requirements 5.2**

- [ ] 7. Update web interface for script findings
  - Verify script findings display correctly in report
  - Ensure findings are grouped by package name
  - Test that script name appears in finding display
  - Verify evidence formatting is readable
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 8. Add test fixtures and integration tests
  - Create sample package.json files with various malicious scripts
  - Create sample package.json files with benign scripts
  - Add integration test for end-to-end analysis
  - Verify findings appear in final report JSON
  - _Requirements: All_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 10. Documentation and examples
  - Add docstrings to all new functions
  - Update README with script analysis feature
  - Add example malicious scripts to documentation
  - Document pattern types and severity levels
  - _Requirements: All_
