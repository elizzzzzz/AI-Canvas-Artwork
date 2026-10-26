"""Fail-closed production evidence preflight; does not simulate physics or inspect AI pixels.

Every approval must point to immutable model, scene, camera and review artifacts.
Reports are produced by actual modeling/review work, never by this checker.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

BASE_CHECKS = ('scale_units', 'entity_transforms', 'facing_direction', 'joint_limits',
               'contact_support', 'no_unintended_intersections', 'critical_visibility',
               'safe_frame', 'subjective_pov', 'prop_state_continuity')
VIDEO_CHECKS = ('camera_clearance', 'temporal_continuity', 'motion_path', 'full_frame_review')
EVIDENCE_KEYS = ('model', 'scene', 'camera', 'preview', 'depth', 'object_ids')
POLICY_VERSION = 'mandatory-3d-v1'


def source_hash(record, blueprint):
    # Source poses must be tied to the current entire asset context, not a stale picture.
    payload = {'policy': POLICY_VERSION, 'record': record, 'asset_manifest': blueprint['asset_manifest'],
               'asset_library': blueprint.get('asset_library'),
               'scene_blockouts': blueprint.get('scene_blockouts'),
               'action_coverage': blueprint.get('action_coverage'),
               'motion_blockouts': blueprint.get('motion_blockouts'),
               'motion_evidence': blueprint.get('motion_evidence')}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def expected_sources(blueprint, library=None):
    result = {'ASSET:' + a['key']: source_hash(a, blueprint) for a in blueprint['asset_manifest']}
    for shot in blueprint['shots']:
        for clip in shot['clips']:
            result[clip['key']] = source_hash({'shot': shot, 'clip': clip}, blueprint)
    result['PILOT:EP01S08-5S'] = source_hash(blueprint['pilot'], blueprint)
    for asset in (library or {}).get('assets', []):
        result['LIB:' + asset['id']] = source_hash(asset, blueprint)
    return result


def checked_file(ref, root, label, errors):
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str) or not ref.get('path'):
        errors.append(label + ': missing artifact'); return None
    relative = Path(ref['path'])
    path = (root / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(root.resolve()):
        errors.append(label + ': must stay inside project'); return None
    if not path.is_file():
        errors.append(label + ': file absent'); return None
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if ref.get('sha256') != actual:
        errors.append(label + ': file changed or SHA-256 missing'); return None
    return path


def load_asset_library(blueprint, root):
    """Fail closed if any declared library source or actual mesh has changed."""
    root = root.resolve()
    refs = blueprint.get('asset_library')
    if not isinstance(refs, dict):
        raise ValueError('asset_library references missing')
    errors = []
    catalog_path = checked_file(refs.get('catalog'), root, 'library catalog', errors)
    mapping_path = checked_file(refs.get('shot_map'), root, 'library shot map', errors)
    if errors:
        raise ValueError('; '.join(errors))
    catalog = json.loads(catalog_path.read_text())
    mapping = json.loads(mapping_path.read_text())
    assets = catalog.get('assets', [])
    ids = [a['id'] for a in assets]
    if len(set(ids)) != len(ids) or len(ids) != catalog.get('asset_count') or not ids:
        raise ValueError('library asset count or IDs invalid')
    for asset in assets:
        checked_file({'path': str(catalog_path.parent.relative_to(root) / asset['file']),
                      'sha256': asset['sha256']}, root, asset['id'], errors)
    actual_clips = [c for s in mapping.get('shots', []) for c in s.get('clip_keys', [])]
    expected_clips = [c['key'] for s in blueprint['shots'] for c in s['clips']]
    if sorted(actual_clips) != sorted(expected_clips):
        errors.append('library shot mapping does not cover exact production clips')
    for shot in mapping.get('shots', []):
        if not set(shot.get('asset_ids', [])) <= set(ids):
            errors.append('library shot uses unknown asset')
    if errors:
        raise ValueError('; '.join(errors))
    return catalog


def load_scene_blockouts(blueprint, root):
    """Verify draft evidence freshness, without asserting physical validity."""
    refs = blueprint.get('scene_blockouts')
    if refs is None:
        return None
    errors = []
    path = checked_file(refs.get('manifest'), root, 'scene manifest', errors)
    if errors:
        raise ValueError('; '.join(errors))
    manifest = json.loads(path.read_text())
    scenes = manifest.get('scenes', [])
    keys = [item.get('scene_key') for item in scenes]
    if len(keys) != 7 or set(keys) != {'SC0' + str(i) for i in range(1, 8)}:
        raise ValueError('scene manifest must contain seven unique canonical scenes')
    for item in scenes:
        files = item.get('files', {})
        if not isinstance(files, dict) or not set(EVIDENCE_KEYS) <= set(files):
            raise ValueError('scene draft missing required evidence references')
        for label, artifact in files.items():
            checked_file(artifact, root, item['scene_key'] + ':' + label, errors)
        for asset, source in item.get('source_assets', {}).items():
            checked_file(source, root, item['scene_key'] + ':' + asset, errors)
    if errors:
        raise ValueError('; '.join(errors))
    return manifest


def load_action_coverage(blueprint, root):
    refs = blueprint.get('action_coverage')
    if refs is None:
        return None
    errors=[]
    path=checked_file(refs.get('manifest'), root, 'action coverage manifest', errors)
    if errors: raise ValueError('; '.join(errors))
    manifest=json.loads(path.read_text())
    episodes=manifest.get('episodes', [])
    if len(episodes)!=3 or any(e.get('ratio',0)<manifest.get('minimum_ratio',0.5) for e in episodes):
        raise ValueError('action coverage is below the required per-episode ratio')
    expected={s['episode']:sum(c['duration'] for c in [clip for shot in blueprint['shots'] if shot['episode']==s['episode'] for clip in shot['clips']]) for s in episodes}
    for e in episodes:
        if e.get('total_seconds') != expected[e['episode']]:
            raise ValueError('action coverage duration does not match storyboard')
    return manifest


def load_motion_blockouts(blueprint, root):
    refs=blueprint.get('motion_blockouts')
    if refs is None: return None
    errors=[]; path=checked_file(refs.get('manifest'),root,'motion manifest',errors)
    if errors: raise ValueError('; '.join(errors))
    manifest=json.loads(path.read_text()); clips=manifest.get('clips',[])
    expected={c['key'] for shot in blueprint['shots'] if shot.get('action_scene') for c in shot['clips']}
    actual={c.get('clip_key') for c in clips}
    if actual != expected or len(clips)!=42: raise ValueError('motion manifest does not cover exact 42 action clips')
    for item in clips:
        if item.get('target_fps') != 24 or item.get('sample_count') != int(round(item['duration_seconds']*24))+1:
            raise ValueError('motion clip frame sampling is not 24fps plus ending boundary')
        if item.get('camera',{}).get('mode') != 'first_person' or not item.get('camera',{}).get('path_points'):
            raise ValueError('motion clip lacks first-person camera path')
        for label,artifact in item.get('evidence',{}).items(): checked_file(artifact,root,item['clip_key']+':'+label,errors)
    if errors: raise ValueError('; '.join(errors))
    return manifest


def load_motion_evidence(blueprint, root):
    refs=blueprint.get('motion_evidence')
    if refs is None:return None
    errors=[];path=checked_file(refs.get('manifest'),root,'motion evidence manifest',errors)
    if errors:raise ValueError('; '.join(errors))
    manifest=json.loads(path.read_text());clips=manifest.get('clips',[])
    if not clips or any(not isinstance(c.get('sample_count'),int) for c in clips):raise ValueError('motion evidence manifest invalid')
    for summary in clips:
        child=checked_file(summary.get('manifest'),root,summary.get('clip_key','motion')+':manifest',errors)
        if not child:continue
        entry=json.loads(child.read_text());samples=entry.get('samples',[])
        if entry.get('target_fps')!=24 or len(samples)!=entry.get('sample_count') or entry.get('approved_for_generation') is not False:
            errors.append(entry.get('clip_key','motion')+': sample coverage or approval state invalid')
        for frame,sample in enumerate(samples):
            if sample.get('frame')!=frame or abs(sample.get('time_seconds',-1)-frame/24)>1e-6:errors.append(entry.get('clip_key','motion')+': frame order invalid')
            for label,artifact in sample.items():
                if label in ('rgb','depth_mm','object_ids','object_id_map'):checked_file(artifact,root,entry.get('clip_key','motion')+':'+label+':'+str(frame),errors)
    if errors:raise ValueError('; '.join(errors))
    return manifest


def load_repair_source_refs(blueprint, root):
    """Validate actual revision sources, including nested frame/texture references.

    Hashing a declared JSON reference alone does not catch a changed child model.
    This verifies files only; it does not grant geometry or human approval.
    """
    seen=set();errors=[]
    def visit(value):
        if isinstance(value,list):
            for child in value: visit(child)
        elif isinstance(value,dict):
            if isinstance(value.get('path'),str) and 'sha256' in value:
                key=(value['path'],value.get('sha256'))
                if key in seen: return
                seen.add(key)
                path=checked_file(value,root,'repair source '+value['path'],errors)
                if path and path.suffix.lower()=='.json':
                    try: visit(json.loads(path.read_text()))
                    except (OSError,ValueError) as exc: errors.append(str(exc))
            else:
                for child in value.values(): visit(child)
    for shot in blueprint.get('shots',[]):
        revision=shot.get('repair_v5')
        if revision:
            refs=revision.get('source_files')
            if not isinstance(refs,dict) or not refs: errors.append('repair source files missing')
            else: visit(refs)
    if errors: raise ValueError('; '.join(errors))
    return len(seen)


def artifact_set_hash(entry):
    payload = {'evidence': entry.get('evidence'), 'report': entry.get('report')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def assess_internal_review(entry, expected_source):
    """Internal test gate: user review is sufficient; formal evidence remains optional."""
    errors=[]
    if not isinstance(entry, dict): return ['invalid entry']
    if expected_source is None or entry.get('source_sha256') != expected_source:
        errors.append('current source not matched')
    review=entry.get('human_review') or entry.get('internal_approval')
    if not isinstance(review, dict) or not review.get('reviewer') or not review.get('reviewed_at'):
        errors.append('internal human review declaration absent')
    return errors


def assess_entry(entry, root, expected_source):
    errors = []
    if not isinstance(entry, dict): return ['invalid entry']
    if expected_source is None or entry.get('source_sha256') != expected_source:
        errors.append('current source not matched')
    if entry.get('status') != 'approved': errors.append('3D package not approved')
    revision = entry.get('revision')
    if not isinstance(revision, str) or not revision.strip(): errors.append('revision missing')
    approval = entry.get('approval')
    if not isinstance(approval, dict) or not approval.get('reviewer') or not approval.get('approved_at'):
        errors.append('named human review absent')
    elif approval.get('revision') != revision or approval.get('source_sha256') != expected_source:
        errors.append('approval stale')
    if isinstance(approval, dict) and approval.get('artifact_set_sha256') != artifact_set_hash(entry):
        errors.append('approval not bound to exact evidence and report hashes')
    evidence = entry.get('evidence')
    if not isinstance(evidence, dict): evidence = {}
    for key in EVIDENCE_KEYS: checked_file(evidence.get(key), root, key, errors)
    report_path = checked_file(entry.get('report'), root, 'report', errors)
    if not report_path: return errors
    try:
        report = json.loads(report_path.read_text())
    except (ValueError, OSError): return errors + ['report unreadable']
    if not isinstance(report, dict): return errors + ['report must be an object']
    if (report.get('scope'), report.get('revision'), report.get('source_sha256')) != (entry.get('key'), revision, expected_source):
        errors.append('report scope/revision/source mismatch')
    if report.get('files') != evidence: errors.append('report not bound to this exact artifact set')
    checks = BASE_CHECKS + (VIDEO_CHECKS if entry.get('kind') in ('clip', 'pilot') else ())
    def validate_checks(values, label):
        if not isinstance(values, dict) or any(values.get(k) is not True for k in checks):
            errors.append(label + ': required geometry check missing or failed')
    validate_checks(report.get('checks'), 'report')
    if entry.get('kind') in ('clip', 'pilot'):
        fps, duration = entry.get('target_fps'), entry.get('duration')
        if (isinstance(fps, bool) or isinstance(duration, bool) or not isinstance(fps, int)
            or not 1 <= fps <= 120 or not isinstance(duration, (int, float))
            or not math.isfinite(duration) or not 0 < duration <= 1800):
            return errors + ['invalid planned frame rate or duration']
        count = math.ceil(duration * fps) + 1
        samples = report.get('samples')
        if report.get('sample_fps') != fps or report.get('sample_count') != count:
            errors.append('report frame coverage metadata incorrect')
        if not isinstance(samples, list) or len(samples) != count:
            return errors + ['full frame coverage missing (including final boundary)']
        for frame, sample in enumerate(samples):
            if not isinstance(sample, dict): errors.append('invalid sample'); continue
            t = sample.get('time_seconds')
            if (sample.get('frame') != frame or isinstance(t, bool) or not isinstance(t, (int, float))
                or not math.isfinite(t) or abs(t - min(frame / fps, duration)) > 1e-6):
                errors.append(f'frame {frame}: order or timing mismatch')
            validate_checks(sample.get('checks'), f'frame {frame}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('production/geometry/coverage-v1.json'))
    parser.add_argument('--scope', help='Exact asset, clip, pilot or repair scope; omit to audit all')
    parser.add_argument('--internal-review', action='store_true', help='Internal test gate: user human review is sufficient; evidence/report are optional')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / args.manifest).read_text())
    blueprint = json.loads((root / 'production/workflow-v1.json').read_text())
    try:
        library = load_asset_library(blueprint, root)
        load_scene_blockouts(blueprint, root)
        load_action_coverage(blueprint, root)
        load_motion_blockouts(blueprint, root)
        load_motion_evidence(blueprint, root)
        load_repair_source_refs(blueprint, root)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(json.dumps({'allowed': False, 'error': str(exc)}, ensure_ascii=False)); return 2
    expected = expected_sources(blueprint, library)
    repair = json.loads((root / 'production/p01-lid-repair-v2/repair-plan.json').read_text())
    expected['REPAIR:P01-v2'] = source_hash({'prompt': repair['prompt'], 'guide_sha256': repair['guide_sha256']}, blueprint)
    entries = manifest.get('entries', [])
    keys = [e.get('key') for e in entries]
    if len(set(keys)) != len(keys) or set(keys) != set(expected):
        print(json.dumps({'allowed': False, 'error': 'coverage missing, duplicated or stale scopes'}, ensure_ascii=False)); return 2
    selected = [e for e in entries if args.scope is None or e['key'] == args.scope]
    if not selected:
        print(json.dumps({'allowed': False, 'error': 'scope not found'})); return 2
    blocked = []
    for entry in selected:
        errors = assess_internal_review(entry, expected[entry['key']]) if args.internal_review else assess_entry(entry, root, expected[entry['key']])
        if errors: blocked.append({'key': entry['key'], 'reasons': errors})
    print(json.dumps({'allowed': not blocked, 'policy': POLICY_VERSION, 'checked': len(selected),
                      'blocked': len(blocked), 'mode': 'internal_review' if args.internal_review else 'formal_evidence', 'results': blocked if args.scope else [],
                      'limitation': ('Internal test gate uses user human review only; it does not prove geometry or AI media correctness.' if args.internal_review else 'Checks evidence completeness and freshness; does not itself prove geometry or AI media correctness.')},
                     ensure_ascii=False, indent=2))
    return 1 if blocked else 0


if __name__ == '__main__':
    raise SystemExit(main())
