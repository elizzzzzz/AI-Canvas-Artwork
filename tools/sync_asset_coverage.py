"""Link actual library meshes to production coverage without granting approval."""
import hashlib
import json
from pathlib import Path
from tools.geometry_preflight import expected_sources, source_hash

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, data):
    (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def ref(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    catalog_path = 'production/asset-library/catalog-v1.json'
    library = read(catalog_path)
    blueprint = read('production/workflow-v1.json')
    blueprint['asset_library'] = {
        'version': 1, 'status': 'proxy_meshes_built_not_approved',
        'catalog': ref(catalog_path),
        'shot_map': ref('production/asset-library/shot-asset-map-v1.json'),
        'policy': 'Every visible entity requires a reusable asset and explicit scene instance; proxy creation never grants production approval.'}
    scene_manifest = read('production/scene-blockouts/manifest-v1.json') if (ROOT / 'production/scene-blockouts/manifest-v1.json').is_file() else None
    if scene_manifest:
        blueprint['scene_blockouts'] = {'version': 1, 'status': 'seven_representative_static_drafts_not_approved',
            'manifest': ref('production/scene-blockouts/manifest-v1.json')}
    action_manifest = read('production/action-coverage-v1.json') if (ROOT / 'production/action-coverage-v1.json').is_file() else None
    if action_manifest:
        blueprint['action_coverage'] = {'version': 1, 'status': action_manifest.get('status'),
            'manifest': ref('production/action-coverage-v1.json')}
    write('production/workflow-v1.json', blueprint)
    expected = expected_sources(blueprint, library)
    repair = read('production/p01-lid-repair-v2/repair-plan.json')
    expected['REPAIR:P01-v2'] = source_hash({'prompt': repair['prompt'], 'guide_sha256': repair['guide_sha256']}, blueprint)
    manifest = read('production/geometry/coverage-v1.json')
    old = {e['key']: e for e in manifest['entries']}
    for asset in library['assets']:
        key = 'LIB:' + asset['id']
        entry = old.setdefault(key, {'key': key, 'kind': 'library_asset',
             'status': 'proxy_built_pending_review', 'revision': 'proxy-v1',
             'evidence': {}, 'report': None, 'approval': None})
        entry.update(asset_id=asset['id'], name=asset['name'],
                     evidence={**entry['evidence'], 'model': ref('production/asset-library/' + asset['file'])})
    if set(old) != set(expected):
        raise ValueError('Unexpected or missing production scopes; resolve explicitly')
    for key, entry in old.items():
        if entry.get('source_sha256') != expected[key] and (entry.get('approval') or entry.get('status') == 'approved'):
            entry['status'] = 'source_changed_pending_review'
            entry['approval'] = None
        entry['source_sha256'] = expected[key]
    for draft in (scene_manifest or {}).get('scenes', []):
        entry = old['ASSET:' + draft['scene_key']]
        if entry.get('status') != 'approved':
            entry.update(status='blockout_built_pending_review', revision='scene-blockout-v1',
                evidence={k: v for k, v in draft['files'].items() if k in ('model', 'scene', 'camera', 'preview', 'depth', 'object_ids')})
    manifest.update(entries=list(old.values()), scope_count=len(old),
                    approved_count=sum(e['status'] == 'approved' for e in old.values()),
                    note='100 real reusable proxy models plus 92 production scopes. Proxies and the P01 assembly are unapproved; seven representative static scenes remain unapproved; no completed scene or motion reviews implied.')
    write('production/geometry/coverage-v1.json', manifest)
    inventory = read('production/geometry/scene-inventory-v1.json')
    for scene in inventory['scenes']:
        scene['available_proxy_asset_ids'] = [a['id'] for a in library['assets'] if scene['key'] in a['scene_keys']]
        scene['complete_scene_package_status'] = 'not_assembled_or_reviewed'
        for draft in (scene_manifest or {}).get('scenes', []):
            if draft['scene_key'] == scene['key']:
                metadata = read(draft['files']['scene']['path'])
                scene.update(status='assembled_proxy_draft_pending_review',
                    source_scene=draft['files']['scene']['path'],
                    entity_transforms=metadata['instances'], cameras=[draft['files']['camera']['path']],
                    dimensions_status='designed_metre_dimensions_not_surveyed',
                    complete_scene_package_status='representative_setup_only_remaining_subspaces_and_motion_pending')
    inventory['partial_assembly_drafts'] = [{'key': 'P01', 'scene': 'production/asset-library/scenes/P01-assembly-v1.json',
                                           'status': 'draft_unapproved_hand_contact_and_occlusion_pending'}]
    write('production/geometry/scene-inventory-v1.json', inventory)
    print(json.dumps({'scope_count': len(old), 'approved_count': manifest['approved_count'], 'library_assets': len(library['assets'])}))


if __name__ == '__main__':
    main()
