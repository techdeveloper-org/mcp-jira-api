# Context Delivery Plan — mcp-jira-api Gap Closure
<!-- Author: context_engineering_agent | Date: 2026-05-29 | Phase: A.5 -->
<!-- Blueprint source: docs/blueprint.md (APPROVED by consensus_agent) -->

---

## Delta-GSD Chunk Registry

These are the named chunks used in agent context budgets below.

| Chunk ID | Content | Source | Size (est.) |
|----------|---------|--------|-------------|
| `gap1-ahp-wireup-spec` | jira_sprint_review current lines 1282-1428, ahp_score sig, Gap 1 change spec | server.py + blueprint §2,§4,§5 | ~2,500 tok |
| `gap2-epic-tools-spec` | 4 Epic tool signatures, endpoint table, error handling, fixture shapes | blueprint §2,§3,§4,§App | ~1,800 tok |
| `gap3-version-tools-spec` | 4 Version tool signatures, endpoint table, JQL injection note, fixture shapes | blueprint §2,§3,§4,§App | ~1,600 tok |
| `gap4-crossboard-tools-spec` | 3 Cross-board signatures, DSA choices, endpoint table | blueprint §2,§3,§7 | ~1,800 tok |
| `server-tool-pattern-delta` | jira_create_issue + jira_get_issue as canonical pattern reference | server.py lines 260-384 | ~2,000 tok |
| `agile-client-interface-delta` | _agile_request() full signature + docstring | agile_client.py lines 75-140 | ~600 tok |
| `scrum-calculator-ahp-delta` | ahp_score() full function body and return shape | scrum_calculator.py lines 745-851 | ~1,200 tok |
| `existing-test-patterns-delta` | _parse() helper, GROUP A/B/C structure, mock pattern | test_tools_integration_new.py lines 1-120 | ~1,500 tok |
| `conftest-fixture-loader-delta` | fixture_loader function, conftest setup | tests/conftest.py full | ~400 tok |
| `blueprint-adrs-delta` | All 5 ADRs (Chosen/Why/Rejected) | blueprint §9 | ~1,200 tok |
| `blueprint-interface-contracts-delta` | 5 interface contracts | blueprint §6 | ~800 tok |
| `blueprint-risk-register-delta` | 10 risks with mitigations | blueprint §8 | ~600 tok |
| `python_backend_output-delta` | Actual modified/new functions from server.py after Phase B | server.py (post-B) lines 1282-1428 + new sections | ~6,000 tok |
| `stride-threat-model-delta` | F.1 STRIDE findings | docs/security/stride_threat_model_gaps.md | ~1,500 tok |
| `f2-security-report-delta` | F.2 SAST+secrets+SCA findings | docs/security/f2_security_report.md | ~800 tok |
| `test-coverage-report-delta` | pytest-cov output (new lines covered) | Phase D.2 output | ~500 tok |

---

## Agent Context Budgets

---

### python_backend_engineer — 15,000 tokens

**Role in pipeline:** Implements all 11 new/modified tools in server.py (Phase B.1–B.4)

**Send these chunks (in priority order):**

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `gap1-ahp-wireup-spec` | 2,500 | Core of B.1 — current code + required change |
| 2 | `gap2-epic-tools-spec` | 1,800 | Full spec for B.2 |
| 3 | `gap3-version-tools-spec` | 1,600 | Full spec for B.3 |
| 4 | `gap4-crossboard-tools-spec` | 1,800 | Full spec for B.4 |
| 5 | `server-tool-pattern-delta` | 2,000 | Pattern reference (jira_create_issue) |
| 6 | `agile-client-interface-delta` | 600 | _agile_request() exact interface |
| 7 | `scrum-calculator-ahp-delta` | 1,200 | ahp_score() exact return shape |
| 8 | `blueprint-adrs-delta` | 1,200 | ADRs binding all implementation decisions |
| 9 | `blueprint-interface-contracts-delta` | 800 | 5 contracts to honor |
| 10 | `blueprint-risk-register-delta` | 600 | R-01/R-03/R-05/R-07/R-10 are critical |
| **Total** | | **14,100** | Within 15,000 budget |

**Exclude:** Test patterns, conftest, security reports, existing test files
**Compression:** Raw delta (all chunks are already minimal excerpts)

---

### test_management_agent — 8,000 tokens

**Role in pipeline:** IEEE 829 test strategy + risk matrix (Phase D.1)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `gap1-ahp-wireup-spec` | 2,500 | Must understand Gap 1 for risk scoring |
| 2 | `gap2-epic-tools-spec` | 1,800 | Understand tool shapes for risk matrix |
| 3 | `gap3-version-tools-spec` | 1,600 | JQL injection risk critical for strategy |
| 4 | `existing-test-patterns-delta` | 1,500 | Pattern for test method naming |
| **Total** | | **7,400** | Within 8,000 budget |

**Exclude:** agile_client details, scrum_calculator body, ADRs, security chunks
**Compression:** Raw

---

### unit_testing_specialist — 10,000 tokens

**Role in pipeline:** Write tests/test_tools_gaps.py (Phase D.2)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `existing-test-patterns-delta` | 1,500 | Must match existing test file structure exactly |
| 2 | `conftest-fixture-loader-delta` | 400 | fixture_loader usage |
| 3 | `python_backend_output-delta` | 6,000 | The actual implemented functions to test |
| 4 | `gap1-ahp-wireup-spec` | 1,200 | AHP test cases (consistent/inconsistent matrix) |
| **Total** | | **9,100** | Within 10,000 budget |

**Exclude:** Blueprint ADRs, security chunks, agile_client details, gap 2/3/4 specs
(the implemented code in python_backend_output-delta is sufficient)
**Compression:** Raw

---

### integration_testing_engineer — 10,000 tokens

**Role in pipeline:** Write tests/test_integration_gaps.py + Pact contracts (Phase D.2)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `python_backend_output-delta` | 6,000 | Implemented functions — need to verify flows |
| 2 | `blueprint-interface-contracts-delta` | 800 | 5 contracts to verify in integration |
| 3 | `existing-test-patterns-delta` | 1,500 | Match existing file structure |
| 4 | `conftest-fixture-loader-delta` | 400 | fixture_loader |
| 5 | `gap3-version-tools-spec` | 800 | JQL injection scenario spec |
| **Total** | | **9,500** | Within 10,000 budget |

**Exclude:** ADRs, risk register, scrum_calculator, agile_client
**Compression:** Raw

---

### hallucination_detector — 6,000 tokens

**Role in pipeline:** Verify implementation against specs (Phase C)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `python_backend_output-delta` | 4,000 (focused subset) | The code to verify |
| 2 | `gap2-epic-tools-spec` | 800 | API endpoints to cross-check |
| 3 | `gap3-version-tools-spec` | 800 | Includes JQL injection check |
| **Total** | | **5,600** | Within 6,000 budget |

**Exclude:** Test patterns, ADRs, all Gap 4 details, security chunks
**Compression:** LLMLingua-2 on python_backend_output-delta (compress 6,000 → 4,000)

---

### context_faithfulness_engineer — 6,000 tokens

**Role in pipeline:** Verify implementation faithfully follows blueprint + ADRs (Phase C)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `blueprint-adrs-delta` | 1,200 | All 5 ADRs to verify against |
| 2 | `blueprint-interface-contracts-delta` | 800 | 5 contracts to verify |
| 3 | `python_backend_output-delta` | 3,800 (compressed) | Implementation to score |
| **Total** | | **5,800** | Within 6,000 budget |

**Exclude:** Gap specs, test patterns, conftest, agile_client
**Compression:** LLMLingua-2 on python_backend_output-delta (compress 6,000 → 3,800)

---

### reliability_auditor — 8,000 tokens

**Role in pipeline:** Compute RS = (NLI×FactScore×DRE×Coverage)^(1/4) (Phase E)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | Phase C hallucination report (NLI, FactScore) | 1,000 | Direct RS inputs |
| 2 | Phase D.2 pytest-cov output (`test-coverage-report-delta`) | 500 | Coverage input |
| 3 | Phase F.6 verdict (APPROVED + all counts=0) | 300 | CVSS modifier |
| 4 | `blueprint-adrs-delta` | 1,200 | For output contract validation check |
| 5 | `python_backend_output-delta` | 4,000 (compressed) | POMDP output contract audit |
| **Total** | | **7,000** | Within 8,000 budget |

**Exclude:** Gap specs, test code, agile_client, fixture details
**Compression:** LLMLingua-2 on python_backend_output-delta

---

### security_defense_architect — 6,000 tokens

**Role in pipeline:** STRIDE threat model for 11 new/modified tools (Phase F.1)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `python_backend_output-delta` | 4,000 (compressed) | API surface to threat-model |
| 2 | `blueprint-risk-register-delta` | 600 | Pre-identified risks to verify |
| 3 | `gap3-version-tools-spec` | 800 | JQL injection attack vector spec |
| **Total** | | **5,400** | Within 6,000 budget |

**Exclude:** Test patterns, ADRs, agile_client, scrum_calculator
**Compression:** LLMLingua-2 on python_backend_output-delta

---

### devsecops_engineer — 5,000 tokens

**Role in pipeline:** SAST + secrets detection + SCA (Phase F.2)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `python_backend_output-delta` | 3,500 (compressed) | Code to SAST-scan |
| 2 | `stride-threat-model-delta` | 1,500 | F.1 findings to cross-reference |
| **Total** | | **5,000** | At budget limit |

**Exclude:** All other chunks — F.2 only needs code + F.1 threat context
**Compression:** LLMLingua-2 on python_backend_output-delta (compress 6,000 → 3,500)

---

### security_compliance_auditor — 8,000 tokens

**Role in pipeline:** Aggregate F.1+F.2, issue BINARY verdict (Phase F.6)

| Priority | Chunk | Tokens | Why |
|----------|-------|--------|-----|
| 1 | `stride-threat-model-delta` | 1,500 | All F.1 findings |
| 2 | `f2-security-report-delta` | 800 | All F.2 findings |
| 3 | `blueprint-risk-register-delta` | 600 | Pre-identified risks for cross-ref |
| **Total** | | **2,900** | Well within 8,000 — no extra chunks needed |

**Exclude:** Code, test patterns, ADRs, gap specs
**Compression:** Raw (all chunks already minimal)

---

## POMDP Routing Policy

```
State: {phase, last_agent_output, retry_count}

Transitions:
  Phase A    → Phase A.5 when: consensus_agent emits APPROVED
  Phase A.5  → Phase B    when: context_delivery_plan.md saved
  Phase B.1  → Phase B.2  when: grep "dod_criteria_weights" server.py returns match
  Phase B.2  → Phase B.3  when: grep "def jira_create_epic" server.py returns match
  Phase B.3  → Phase B.4  when: grep "def jira_create_version" server.py returns match
  Phase B.4  → Phase C    when: tool count in server.py == 52
  Phase C    → Phase D.1  when: BOTH agents emit PASS (NLI=1.0, FactScore=1.0)
  Phase C    → Phase B    when: EITHER agent emits FAIL (retry_count++)
  Phase D.1  → Phase D.2  when: TEST_PLAN_GAPS.md saved
  Phase D.2  → Phase F.1  when: pytest --cov-fail-under=100 exits 0
  Phase D.2  → Phase B    when: pytest fails (retry_count++)
  Phase F.1  → Phase F.2  when: F.1_COMPLETE emitted
  Phase F.1  → Phase B    when: F.1_BLOCKED_CRITICAL emitted
  Phase F.2  → Phase F.6  when: F.2_PASS or F.2_FAIL (both feed F.6)
  Phase F.6  → Phase E    when: SECURITY AUDIT VERDICT: APPROVED
  Phase F.6  → Phase B    when: SECURITY AUDIT VERDICT: REJECTED (retry_count++)
  Phase E    → Phase G    when: RS = 1.0
  Phase E    → {phase}    when: RS < 1.0 (return to component phase)
  Phase G    → DONE       when: PHASE_G_COMPLETE

Max retry_count per phase: 3 (escalate to user if exceeded)
```

---

**Context Delivery Plan complete. Phase B is now UNBLOCKED.**
