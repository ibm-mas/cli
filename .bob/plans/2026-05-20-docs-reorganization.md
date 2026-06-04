# Documentation Reorganization Plan

## Objective

Consolidate all documentation from `docs/commands/` into `docs/guides/`, ensuring each CLI function has a comprehensive guide. Review all documents for quality, consistency, and style using `docs/guides/install.md` as the exemplar. Split the existing backup-restore guide into separate backup and restore documents.

## Critical Rules

1. **Use install.md as the style exemplar** - All documents must follow the structure, formatting, and tone of `docs/guides/install.md`
2. **One page at a time** - Complete each document fully before moving to the next
3. **Configure redirects** - Add redirect mappings in `mkdocs.yml` for all moved/renamed pages
4. **Preserve content** - Do not delete information; reorganize and improve it
5. **Validate after each change** - Ensure mkdocs builds successfully after each document update

## Execution Plan

### Phase 1: Split Backup-Restore Guide

- [ ] **1.1** Create `docs/guides/backup.md` from backup-restore.md content
- [ ] **1.2** Create `docs/guides/restore.md` from backup-restore.md content
- [ ] **1.3** Update mkdocs.yml navigation and add redirects
- [ ] **1.4** Delete obsolete backup-restore.md and command files
- [ ] **1.5** Validate Phase 1

### Phase 2: Migrate Must-Gather Command

- [ ] **2.1** Create comprehensive `docs/guides/must-gather.md`
- [ ] **2.2** Update mkdocs.yml with navigation and redirect
- [ ] **2.3** Delete `docs/commands/must-gather.md`
- [ ] **2.4** Validate Phase 2

### Phase 3: Migrate Airgap Configuration

- [ ] **3.1** Create comprehensive `docs/guides/configure-airgap.md`
- [ ] **3.2** Update mkdocs.yml with navigation and redirect
- [ ] **3.3** Delete `docs/commands/configure-airgap.md`
- [ ] **3.4** Validate Phase 3

### Phase 4: Migrate Registry Commands

- [ ] **4.1** Create `docs/guides/setup-registry.md`
- [ ] **4.2** Create `docs/guides/teardown-registry.md`
- [ ] **4.3** Update mkdocs.yml with navigation and redirects
- [ ] **4.4** Delete obsolete command files
- [ ] **4.5** Validate Phase 4

### Phase 5: Migrate Provisioning Commands ✅ COMPLETED

- [x] **5.1** Create `docs/guides/provision-fyre.md`
- [x] **5.2** Create `docs/guides/provision-roks.md`
- [x] **5.3** Create `docs/guides/provision-rosa.md`
- [x] **5.4** Create `docs/guides/provision-aws.md`
- [x] **5.5** Update mkdocs.yml with navigation and redirects
- [x] **5.6** Delete obsolete provisioning command files
- [x] **5.7** Validate Phase 5 - mkdocs serving successfully

### Phase 6: Migrate Remaining Commands

- [ ] **6.1** Create `docs/guides/mirror-redhat-images.md`
- [ ] **6.2** Create `docs/guides/configtool-oidc.md`
- [ ] **6.3** Create `docs/guides/debug.md` if needed
- [ ] **6.4** Update mkdocs.yml and remove Command Reference section
- [ ] **6.5** Delete all remaining command files
- [ ] **6.6** Validate Phase 6

### Phase 7: Review Existing Guides

- [ ] **7.1** Review `docs/guides/install.md`
- [ ] **7.2** Review `docs/guides/update.md`
- [ ] **7.3** Review `docs/guides/upgrade.md`
- [ ] **7.4** Review `docs/guides/uninstall.md`
- [ ] **7.5** Review `docs/guides/aiservice-install.md`
- [ ] **7.6** Review `docs/guides/image-mirroring.md`
- [ ] **7.7** Review `docs/guides/image-validation.md`
- [ ] **7.8** Validate Phase 7

### Phase 8: Final Cleanup

- [ ] **8.1** Verify docs/commands directory is empty or removed
- [ ] **8.2** Review all redirects in mkdocs.yml
- [ ] **8.3** Review navigation structure
- [ ] **8.4** Build and test documentation
- [ ] **8.5** Create summary of changes

## Validation

After each phase run `mkdocs serve` and verify builds, navigation, and redirects work correctly.