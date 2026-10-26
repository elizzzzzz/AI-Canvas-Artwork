"""Regression constraints for reported EP03 faults, not artistic approval."""
import unittest
import numpy as np
from tools.ep03_repair_v5 import make_stages,frame_pose,index,FPS
from tools.asset_library import world_transforms

class EpisodeThreeRepairTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.configs={s.key:(s,d,p) for s,d,p,_ in make_stages()}
 def test_stopped_cart_and_camera_have_no_jitter_across_all_frames(self):
  s,d,p=self.configs['EP03R5-STOP'];reference=s.model['nodes'][index(s.model,'cart_body')]['matrix']
  for f in range(d*FPS+1):
   sc,eye,target,obs=frame_pose(s,f/FPS,d,p)
   np.testing.assert_allclose(eye,s.camera['eye']);np.testing.assert_allclose(target,s.camera['target']);np.testing.assert_allclose(sc['nodes'][index(sc,'cart_body')]['matrix'],reference)
 def test_stamp_contacts_ink_before_paper_and_never_below_table(self):
  s,d,p=self.configs['EP03R5-STAMP'];contacts=[]
  for f in range(d*FPS+1):
   sc,_,_,obs=frame_pose(s,f/FPS,d,p);o=obs[0]
   self.assertGreaterEqual(o['paper_gap_m'],-1e-7)
   if o['ink_contact']:contacts.append(('ink',f))
   if o['paper_contact']:contacts.append(('paper',f));self.assertLess(abs(o['paper_gap_m']),1e-7)
  self.assertLess(min(f for k,f in contacts if k=='ink'),min(f for k,f in contacts if k=='paper'))
 def test_cart_travels_with_camera_and_wheels_roll_same_distance(self):
  s,d,p=self.configs['EP03R5-RIDE'];initial=s.model['nodes'][index(s.model,'cart_body')]['matrix']
  for f in range(0,d*FPS+1,12):
   sc,eye,_,obs=frame_pose(s,f/FPS,d,p);body=np.array(sc['nodes'][index(sc,'cart_body')]['matrix'])
   self.assertAlmostEqual(eye[1]-s.camera['eye'][1],body[1,3]-initial[1][3])
   o=next(x for x in obs if 'wheel_angle_rad' in x)
   self.assertAlmostEqual(-o['wheel_angle_rad']*.515,o['vehicle_distance_m'])
 def test_hoof_targets_lift_only_in_swing(self):
  s,d,p=self.configs['EP03R5-RIDE']
  for f in range(d*FPS+1):
   sc,_,_,obs=frame_pose(s,f/FPS,d,p)
   for o in (x for x in obs if 'stance' in x):
    if o['stance']:self.assertEqual(o['target_hoof_z'],0)
    else:self.assertGreaterEqual(o['target_hoof_z'],0)
   world=world_transforms(sc)
   for i,n in enumerate(sc['nodes']):
    if n['name'].startswith('hoof_'):
     points=np.c_[n['mesh'][0],np.ones(len(n['mesh'][0]))]@world[i].T
     self.assertGreaterEqual(float(points[:,2].min()),-1e-6)
 def test_item_movements_do_not_happen_simultaneously(self):
  s,d,p=self.configs['EP03R5-HANDOFF']
  for f in range(d*FPS+1):
   sc,_,_,obs=frame_pose(s,f/FPS,d,p)
   self.assertLessEqual(sum(0<o['move_fraction']<1 for o in obs),1)
