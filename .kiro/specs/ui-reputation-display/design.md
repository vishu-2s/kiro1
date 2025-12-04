# Design Document

## Overview

This design enhances the web UI's report rendering logic to parse and display both vulnerability and reputation findings from the orchestrator's package-centric JSON output. The current implementation only extracts vulnerability data from the `security_findings.packages` array, ignoring reputation analysis results. This enhancement will extract both types of findings and display them in a unified, visually distinct manner.

## Architecture

The solution involves modifying the JavaScript `renderReport()` function in `templates/index.html` to:

1. Parse both vulnerability and reputation data from each package in `security_findings.packages`
2. Convert reputation findings into a standardized finding format
3. Display findings grouped by package with visual distinction between finding types
4. Update summary statistics to include reputation findings

### Current Architecture

```
Orchestrator Output (demo_ui_comprehensive_report.json)
  └─> security_findings.packages[] 
       ├─> Package with vulnerabilities[]
       └─> Package with reputation_score, risk_factors[]

Web UI (templates/index.html)
  └─> renderReport() function
       └─> Only extracts vulnerabilities
       └─> Ignores reputation data ❌
```

### Enhanced Architecture

```
Orchestrator Output (demo_ui_comprehensive_report.json)
  └─> security_findings.packages[] 
       ├─> Package with vulnerabilities[]
       └─> Package with reputation_score, risk_factors[]

Web UI (templates/index.html)
  └─> renderReport() function
       ├─> Extracts vulnerabilities ✓
       ├─> Extracts reputation findings ✓
       └─> Displays both types grouped by package ✓
```

## Components and Interfaces

### Input Data Structure

The orchestrator produces a JSON file with this structure:

```json
{
  "security_findings": {
    "packages": [
      {
        "package_name": "flatmap-stream",
        "package_version": "0.1.1",
        "ecosystem": "npm",
        "vulnerabilities": [
          {
            "id": "GHSA-9x64-5r7x-2q53",
            "summary": "Malicious Package in flatmap-stream",
            "severity": "critical",
            "cvss_score": 9.5
          }
        ],
        "vulnerability_count": 3,
        "combined_impact": {
          "overall_severity": "critical"
        }
      },
      {
        "package_name": "flatmap-stream",
        "ecosystem": "npm",
        "reputation_score": 0.55,
        "risk_level": "high",
        "factors": {
          "age_score": 1.0,
          "downloads_score": 0.5,
          "author_score": 0.3,
          "maintenance_score": 0.2
        },
        "risk_factors": [
          {
            "type": "unknown_author",
            "severity": "high",
            "description": "Package author is unknown or unverified"
          }
        ]
      }
    ]
  }
}
```

### Finding Format

Both vulnerability and reputation findings will be converted to a unified format:

```javascript
{
  package: "flatmap-stream",
  version: "0.1.1",
  finding_type: "vulnerability" | "reputation",
  severity: "critical" | "high" | "medium" | "low",
  confidence: 0.9,
  evidence: ["Description of the finding"],
  // Type-specific fields
  vulnerability_id: "GHSA-xxx",  // For vulnerabilities
  cvss_score: 9.5,               // For vulnerabilities
  reputation_score: 0.55,        // For reputation
  risk_factors: [...]            // For reputation
}
```

## Data Models

### Package Entry (from orchestrator)

```typescript
interface PackageEntry {
  // Common fields
  package_name: string;
  package_version?: string;
  ecosystem: string;
  confidence: number;
  reasoning: string;
  
  // Vulnerability-specific fields
  vulnerabilities?: Vulnerability[];
  vulnerability_count?: number;
  combined_impact?: {
    overall_severity: string;
    max_cvss_score: number;
  };
  
  // Reputation-specific fields
  reputation_score?: number;
  risk_level?: string;
  factors?: {
    age_score: number;
    downloads_score: number;
    author_score: number;
    maintenance_score: number;
  };
  risk_factors?: RiskFactor[];
  author_analysis?: {
    author_name: string | null;
    is_verified: boolean;
    suspicious_patterns: string[];
  };
}

interface Vulnerability {
  id: string;
  summary: string;
  details: string;
  severity: string;
  cvss_score: number;
  affected_versions: string[];
  fixed_versions: string[];
}

interface RiskFactor {
  type: string;
  severity: string;
  description: string;
  score: number;
}
```

### UI Finding (internal representation)

```typescript
interface UIFinding {
  package: string;
  version: string;
  finding_type: "vulnerability" | "reputation";
  severity: "critical" | "high" | "medium" | "low";
  confidence: number;
  evidence: string[];
  recommendations?: string[];
  
  // Vulnerability-specific
  vulnerability_id?: string;
  cvss_score?: number;
  
  // Reputation-specific
  reputation_score?: number;
  risk_level?: string;
  risk_factors?: RiskFactor[];
  factor_scores?: {
    age_score: number;
    downloads_score: number;
    author_score: number;
    maintenance_score: number;
  };
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Acceptance Criteria Testing Prework

1.1 WHEN the UI receives a report with packages containing vulnerability data THEN the system SHALL display all vulnerabilities with their severity, CVSS scores, and descriptions
Thoughts: This is about ensuring that for any package with vulnerability data, all vulnerabilities are extracted and displayed. We can test this by generating reports with varying numbers of vulnerabilities and ensuring all are displayed.
Testable: yes - property

1.2 WHEN the UI receives a report with packages containing reputation data THEN the system SHALL display reputation scores, risk levels, and risk factors
Thoughts: This is about ensuring that for any package with reputation data, the reputation information is extracted and displayed. We can test this by generating reports with reputation data and verifying all fields are shown.
Testable: yes - property

1.3 WHEN a package has both vulnerability and reputation data THEN the system SHALL display both types of findings grouped under that package
Thoughts: This is about ensuring that when both types of data exist, both are displayed. However, in the current JSON structure, vulnerability and reputation data come as separate package entries. This is more about the implementation detail of how we group them.
Testable: yes - example

1.4 WHEN displaying findings THEN the system SHALL show the package name and version prominently for each group of findings
Thoughts: This is about UI presentation - ensuring package name and version are visible. This is a visual requirement that's hard to test programmatically.
Testable: no

1.5 WHEN multiple packages are analyzed THEN the system SHALL display findings for all packages in the report
Thoughts: This is about ensuring no packages are skipped during parsing. We can test this by generating reports with multiple packages and verifying all are processed.
Testable: yes - property

2.1 WHEN displaying a reputation finding THEN the system SHALL use a distinct visual indicator to differentiate it from vulnerability findings
Thoughts: This is about visual styling - icons, colors, labels. This is a UI/UX requirement that's not easily testable programmatically.
Testable: no

2.2 WHEN displaying reputation risk factors THEN the system SHALL show each factor with its severity level and description
Thoughts: This is about ensuring all risk factors in the array are displayed with their properties. We can test this by generating reputation data with various risk factors.
Testable: yes - property

2.3 WHEN displaying reputation scores THEN the system SHALL show the overall score and individual component scores
Thoughts: This is about ensuring all score fields are extracted and displayed. We can test this by verifying the presence of these fields in the rendered output.
Testable: yes - property

2.4 WHEN a package has low reputation THEN the system SHALL highlight the specific risk factors that contributed to the low score
Thoughts: This is about conditional highlighting based on reputation score. This is a UI styling concern.
Testable: no

2.5 WHEN displaying findings THEN the system SHALL maintain consistent styling with the existing UI design
Thoughts: This is about visual consistency, which is subjective and not programmatically testable.
Testable: no

3.1 WHEN calculating total findings THEN the system SHALL count both vulnerability findings and reputation findings
Thoughts: This is about ensuring the count includes both types. We can test this by generating reports with known numbers of each type and verifying the total.
Testable: yes - property

3.2 WHEN calculating severity counts THEN the system SHALL map reputation risk levels to severity levels
Thoughts: This is about the mapping logic from risk_level to severity. We can test this with various risk levels and verify the mapping.
Testable: yes - property

3.3 WHEN displaying the findings count THEN the system SHALL show the total across all finding types
Thoughts: This is the same as 3.1, just stated differently.
Testable: yes - property (duplicate of 3.1)

3.4 WHEN a package has multiple findings of different types THEN the system SHALL count each finding separately in the totals
Thoughts: This is about ensuring we don't deduplicate findings of different types. We can test this with packages that have both types.
Testable: yes - property

3.5 WHEN the report contains no findings THEN the system SHALL display an appropriate message
Thoughts: This is a specific edge case - empty findings array.
Testable: yes - example

4.1 WHEN parsing package data THEN the system SHALL handle packages with only vulnerability data
Thoughts: This is about robustness - ensuring we don't crash when reputation fields are missing.
Testable: yes - property

4.2 WHEN parsing package data THEN the system SHALL handle packages with only reputation data
Thoughts: This is about robustness - ensuring we don't crash when vulnerability fields are missing.
Testable: yes - property

4.3 WHEN parsing package data THEN the system SHALL handle packages with both vulnerability and reputation data
Thoughts: This is about handling the complete case.
Testable: yes - property

4.4 WHEN parsing package data THEN the system SHALL handle missing or null fields without crashing
Thoughts: This is about defensive programming - handling undefined/null gracefully. This is an edge case concern.
Testable: edge-case

4.5 WHEN parsing fails for a specific package THEN the system SHALL log the error and continue processing other packages
Thoughts: This is about error handling - ensuring one bad package doesn't break the whole report.
Testable: yes - property

### Property Reflection

After reviewing all properties:
- Properties 3.1 and 3.3 are duplicates (both test that total count includes all finding types)
- Properties 4.1, 4.2, and 4.3 can be combined into one property about handling various package data combinations
- Property 1.5 and 4.5 are related (both about processing all packages even if some fail)

Consolidated properties:
- Combine 3.1 and 3.3 into one property
- Combine 4.1, 4.2, 4.3 into one comprehensive property about data format handling
- Keep 1.5 and 4.5 separate as they test different aspects (completeness vs error recovery)

### Correctness Properties

Property 1: Vulnerability extraction completeness
*For any* package entry with a vulnerabilities array, all vulnerabilities in that array should be extracted and converted to UI findings
**Validates: Requirements 1.1**

Property 2: Reputation extraction completeness
*For any* package entry with reputation_score and risk_factors fields, the reputation data should be extracted and converted to a UI finding
**Validates: Requirements 1.2**

Property 3: Multi-package processing completeness
*For any* report with N packages in security_findings.packages, the UI should process and display findings from all N packages
**Validates: Requirements 1.5**

Property 4: Risk factor display completeness
*For any* reputation finding with M risk factors, all M risk factors should be displayed with their severity and description
**Validates: Requirements 2.2**

Property 5: Score field completeness
*For any* reputation finding, both the overall reputation_score and all individual factor scores (age, downloads, author, maintenance) should be displayed
**Validates: Requirements 2.3**

Property 6: Total findings count accuracy
*For any* report with V vulnerability findings and R reputation findings, the total findings count should equal V + R
**Validates: Requirements 3.1, 3.3**

Property 7: Severity mapping consistency
*For any* reputation finding with risk_level, the mapped severity should follow the mapping: critical→critical, high→high, medium→medium, low→low
**Validates: Requirements 3.2**

Property 8: Individual finding counting
*For any* package with both vulnerability and reputation data, each type should contribute separately to the total count (not be deduplicated)
**Validates: Requirements 3.4**

Property 9: Data format robustness
*For any* package entry, the parsing logic should successfully handle cases where only vulnerability fields are present, only reputation fields are present, or both are present, without throwing errors
**Validates: Requirements 4.1, 4.2, 4.3**

Property 10: Error isolation
*For any* report where one package fails to parse, the remaining packages should still be processed and displayed
**Validates: Requirements 4.5**

## Error Handling

### Parsing Errors

1. **Missing Fields**: Use optional chaining (`?.`) and nullish coalescing (`??`) to handle missing fields gracefully
2. **Invalid Data Types**: Validate data types before processing (e.g., check if `vulnerabilities` is an array)
3. **Malformed JSON**: Wrap parsing logic in try-catch blocks
4. **Package-Level Errors**: Continue processing other packages if one fails

### Display Errors

1. **Missing Package Name**: Display "Unknown Package" as fallback
2. **Missing Version**: Display "Unknown Version" as fallback
3. **Invalid Severity**: Map to "unknown" severity with neutral styling
4. **Empty Findings**: Display "No security issues detected" message

### Logging

- Log parsing errors to console with package details
- Log skipped packages due to errors
- Log data format mismatches for debugging

## Testing Strategy

### Unit Tests

Unit tests will verify specific parsing and conversion logic:

1. **Test vulnerability extraction**: Verify that a package with 3 vulnerabilities produces 3 UI findings
2. **Test reputation extraction**: Verify that a package with reputation data produces 1 UI finding with all fields
3. **Test empty report**: Verify that an empty packages array displays appropriate message
4. **Test missing fields**: Verify that packages with missing optional fields don't crash
5. **Test severity mapping**: Verify risk_level to severity mapping is correct

### Property-Based Tests

Property-based tests will use Hypothesis (Python) or fast-check (JavaScript) to verify correctness properties across many randomly generated inputs. Each test will run a minimum of 100 iterations.

The testing framework will be **fast-check** for JavaScript, as the UI code is client-side JavaScript.

1. **Property 1 Test**: Generate packages with random numbers of vulnerabilities (0-10), verify all are extracted
   - **Feature: ui-reputation-display, Property 1: Vulnerability extraction completeness**

2. **Property 2 Test**: Generate packages with reputation data, verify reputation finding is created with all fields
   - **Feature: ui-reputation-display, Property 2: Reputation extraction completeness**

3. **Property 3 Test**: Generate reports with random numbers of packages (1-20), verify all are processed
   - **Feature: ui-reputation-display, Property 3: Multi-package processing completeness**

4. **Property 4 Test**: Generate reputation findings with random numbers of risk factors (0-10), verify all are displayed
   - **Feature: ui-reputation-display, Property 4: Risk factor display completeness**

5. **Property 5 Test**: Generate reputation findings, verify all score fields are present in output
   - **Feature: ui-reputation-display, Property 5: Score field completeness**

6. **Property 6 Test**: Generate reports with random V vulnerabilities and R reputation findings, verify total = V + R
   - **Feature: ui-reputation-display, Property 6: Total findings count accuracy**

7. **Property 7 Test**: Generate reputation findings with each risk_level value, verify severity mapping
   - **Feature: ui-reputation-display, Property 7: Severity mapping consistency**

8. **Property 8 Test**: Generate packages with both types of data, verify both contribute to count
   - **Feature: ui-reputation-display, Property 8: Individual finding counting**

9. **Property 9 Test**: Generate packages with various field combinations, verify no errors
   - **Feature: ui-reputation-display, Property 9: Data format robustness**

10. **Property 10 Test**: Generate reports where one package has invalid data, verify others still process
    - **Feature: ui-reputation-display, Property 10: Error isolation**

### Integration Tests

Integration tests will verify end-to-end functionality:

1. Load actual `demo_ui_comprehensive_report.json` file and verify UI renders correctly
2. Test with reports containing only vulnerabilities
3. Test with reports containing only reputation data
4. Test with reports containing both types
5. Test with empty reports

### Manual Testing

1. Visual inspection of rendered UI for proper styling
2. Verify visual distinction between vulnerability and reputation findings
3. Verify responsive design on different screen sizes
4. Verify accessibility (screen reader compatibility, keyboard navigation)

## Implementation Plan

### Phase 1: Parsing Enhancement

1. Modify `renderReport()` function to detect reputation data in packages
2. Add reputation-to-finding conversion logic
3. Update findings array to include both types

### Phase 2: Display Enhancement

1. Add visual indicators for reputation findings (icon, badge)
2. Create reputation-specific display template
3. Group findings by package name

### Phase 3: Statistics Update

1. Update severity counting to include reputation findings
2. Map risk_level to severity for counting
3. Update total findings calculation

### Phase 4: Error Handling

1. Add try-catch blocks around parsing logic
2. Add field validation
3. Add fallback values for missing data

### Phase 5: Testing

1. Write unit tests for parsing logic
2. Write property-based tests for correctness properties
3. Perform integration testing with real data
4. Conduct manual UI testing

## Performance Considerations

- Parsing is done client-side in JavaScript, so performance should be acceptable for reports with up to 1000 packages
- Use efficient array operations (map, filter, reduce) instead of nested loops
- Avoid DOM manipulation inside loops - build HTML string first, then insert once
- Consider pagination or virtual scrolling for very large reports (future enhancement)

## Security Considerations

- Sanitize all user-provided data before rendering (use `escapeHtml()` function)
- Avoid using `innerHTML` with unsanitized data
- Validate JSON structure before parsing
- Limit report size to prevent DoS attacks (future enhancement)

## Accessibility

- Use semantic HTML elements
- Provide ARIA labels for icons and badges
- Ensure sufficient color contrast for severity indicators
- Support keyboard navigation
- Provide text alternatives for visual indicators

## Future Enhancements

1. **Filtering**: Allow users to filter by finding type, severity, package
2. **Sorting**: Allow users to sort findings by various criteria
3. **Export**: Allow users to export filtered findings to CSV/PDF
4. **Comparison**: Allow users to compare reports over time
5. **Pagination**: Add pagination for large reports
6. **Search**: Add search functionality to find specific packages or findings
