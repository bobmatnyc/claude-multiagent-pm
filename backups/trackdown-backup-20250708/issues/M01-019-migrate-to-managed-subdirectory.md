## **[M01-019]** Migrate git-portfolio-manager to ~/Projects/managed/ subdirectory

**Type:** Milestone Task  
**Milestone:** M01_Foundation  
**Epic:** FEP-001 Framework Infrastructure Setup  
**Priority:** High  
**Story Points:** 3  
**Assignee:** @claude  
**Status:** Done  
**Sprint:** S01  
**Projects Affected:** git-portfolio-manager

**Description:**
Properly migrate git-portfolio-manager to the new subdirectory organization model at `~/Projects/managed/git-portfolio-manager/`. This implements the correct Claude-PM framework architecture where managed projects are clearly separated from experimental and archived projects.

**Milestone Context:**
- Establishes the proper subdirectory organization model for all managed projects
- Corrects the previous integration-only approach to follow the actual migration process
- Sets the standard for all future M01 Foundation project migrations
- Enables framework operations to target managed projects specifically

**Acceptance Criteria:**
- [ ] Create `~/Projects/managed/` directory structure
- [ ] Move git-portfolio-manager from root to `~/Projects/managed/git-portfolio-manager/`
- [ ] Verify all relative paths still work correctly after move
- [ ] Update any absolute paths found in configuration files
- [ ] Run full test suite to ensure functionality preserved
- [ ] Run build process to verify compilation works in new location
- [ ] Test CLI functionality (`--version`, `--help`, core commands)
- [ ] Update Claude-PM integration mappings to reflect new path
- [ ] Update framework health monitoring to scan managed subdirectory
- [ ] Verify git history and repository integrity preserved

**Technical Notes:**
- Follow the original standard process: ticket → move → path updates → test/build verification
- Use `mv` command to preserve git history and file attributes
- Check for any hardcoded paths in:
  - `package.json` scripts
  - Configuration files
  - Documentation references
  - Binary/executable paths
- Ensure relative imports and requires continue working

**Cross-Project Dependencies:**
- [ ] Framework health monitoring scripts need path updates
- [ ] Project mapping in Claude-PM/integration/project-mapping.json requires update
- [ ] Any external references to the project path need updating

**Testing Strategy:**
- [ ] Pre-migration: Run tests and build to establish baseline
- [ ] Post-migration: Run identical tests to verify no regressions
- [ ] CLI functionality test: Verify all commands work from new location
- [ ] Integration test: Verify framework can discover and monitor project in new location
- [ ] Git operations test: Verify commits, pulls, pushes work normally

**Definition of Done:**
- [ ] Project successfully moved to `~/Projects/managed/git-portfolio-manager/`
- [ ] All build and test scripts pass successfully from new location
- [ ] CLI functionality fully operational (`git-portfolio-manager --version` works)
- [ ] No absolute paths broken by the move
- [ ] Git repository integrity maintained (history, remotes, branches intact)
- [ ] Framework health monitoring updated to scan managed directory
- [ ] Integration mappings updated in Claude-PM repository
- [ ] New directory structure documented for future project migrations
- [ ] Standard migration process validated and documented

**Migration Checklist:**
1. **Pre-migration verification:**
   - [x] Run `npm test` (5/5 tests passed)
   - [x] Run `npm run build` (TypeScript compilation successful)
   - [x] Test `node bin/git-portfolio-manager.js --version` (1.1.0)
   
2. **Directory creation:**
   - [x] Create `~/Projects/managed/` directory
   
3. **Move operation:**
   - [x] Move project: `mv ~/Projects/git-portfolio-manager ~/Projects/managed/`
   
4. **Path verification:**
   - [x] Check for absolute paths in config files (all relative paths used)
   - [x] Verify package.json scripts still work (verified)
   
5. **Post-migration verification:**
   - [x] Run `npm test` from new location (5/5 tests passed)
   - [x] Run `npm run build` from new location (successful)
   - [x] Test CLI functionality from new location (--version, --help working)
   
6. **Framework updates:**
   - [x] Update Claude-PM project mappings (status: migrated)
   - [x] Update health monitoring scripts (detects managed projects)
   - [x] Commit all changes

**Success Metrics:**
- Zero test failures after migration
- All CLI commands functional from new location
- Framework health monitoring successfully tracks project in managed directory
- Clean separation between managed and unmanaged projects established