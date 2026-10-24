# Project production rules

The user's 2026-10-24 instruction makes 3D modeling mandatory before **every image or video generation**, including character/scene/prop references, keyframes, image edits, retries and video pilots. This instruction supersedes earlier plans that allowed image generation before graybox review.

- Follow `docs/MANDATORY-3D-PRODUCTION.md` and `production/geometry/coverage-v1.json`.
- Before a paid generation submission, run `python3 tools/geometry_preflight.py --scope <exact_scope>` from the repository root. Exit 0 is required, plus the existing artistic review, current model capability and budget approval. Never bypass the preflight using another API, a direct media call, a native node run or an unreviewed manual flag.
- Each scope needs a real model/scene/camera package, depth and object-ID outputs, previews, actual check report, and a named human approval tied to current source and artifact hashes. Pending/missing/stale packages block generation. Test fixtures do not count as production evidence.
- Images need reviewed scale, poses, occlusion, facing, support/contact and articulated prop state. Videos additionally need camera/motion review at the output frame rate for the full segment. Sample all planned frames plus the ending boundary, and adaptive contact/hinge/collision checkpoints where needed; don't approve only start/end poses.
- All actual storytelling shots remain first-person. Layout/side/top diagnostic views are production evidence, not insert shots.
- The first 8 raster assets remain concept candidates, with no retroactive 3D approval. P01 v1 is rejected for lid geometry; the existing P01 hinge mesh is only partial prop geometry, not approval of a complete scene.
- Changes to models, transforms, props, poses, camera/path, action timing or source prompts invalidate affected approvals. Update hashes/coverage and re-review before rerunning.
- After AI generation compare actual frames with the approved 3D references; inspect geometry and temporal continuity again. 3D input never proves AI output is defect-free.
- Do not mark coverage entries approved, set native clearance fields true, fabricate geometry reports, or claim scenes built without evidence. Native boolean fields implement a runtime stop; the local preflight validates evidence and freshness, not physics or pixel quality.
- Existing cost approval does not waive these requirements. Do not spend newly proposed repair/video budgets without the required confirmation. Persist task state with the AICanvas shared helper; never store credentials or temporary signed media URLs in Git.

Current state: 100 actual reusable GLB proxy models are built, with 34 logical-shot / 67 clip assembly plans. The P01/table/hand/camera assembly is a draft. Seven representative static scene drafts are assembled with portrait/depth/ID exports; full subspaces, 67 clip paths and complete scene reviews are pending; 192 production scopes remain blocked, and 10 existing generation nodes have false 3D clearance conditions. Continue detailed modeling and scene assembly; there is no approval needed for non-generative local modeling work within the project.

- Register visible people, hands/sleeves, animals, equipment, props, buildings, furniture, roads and environment geometry in `production/asset-library/catalog-v1.json` with stable IDs. Reuse the asset via explicit scene instances; do not silently change proportions between shots.
- Distinguish proxy geometry, assembled scene, reviewed evidence and generated final media. Independent clothing/components must not be double-layered over an already clothed proxy by accident.
- After rebuilding the library run `python3 tools/build_asset_registry.py` and `python3 -m tools.sync_asset_coverage`; source changes invalidate existing approvals. The preflight hashes catalog, shot mapping and actual GLBs. Never manufacture pass reports from catalog completeness.

- After changing canonical scene drafts run `python3 -m tools.scene_blockouts` then `python3 -m tools.sync_asset_coverage`. The preflight hashes the scene manifest, all its declared artifacts and source GLBs. Static representative cameras never count as full clip motion review.

- Action coverage is tracked in `production/action-coverage-v1.json`; every episode must remain at or above 50% action seconds while preserving first-person camera rules. This planning ratio never substitutes for 3D motion evidence.
