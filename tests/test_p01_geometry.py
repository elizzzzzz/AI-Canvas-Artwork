"""Mechanical acceptance checks for the P01 rear-hinged medicine chest."""
import math
import unittest
try:
    from tools.p01_geometry import lid_corners, hinge_axis, lid_inner_normal
except ModuleNotFoundError:
    lid_corners = hinge_axis = lid_inner_normal = None


class P01GeometryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(lid_corners, 'The articulated P01 geometry is not implemented yet')

    def assertPoint(self, actual, expected):
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=7)

    def test_closed_lid_matches_box_footprint(self):
        v = lid_corners(0)
        self.assertPoint(v[0], (-18, 12, 18.2))
        self.assertPoint(v[2], (18, -12, 18.2))

    def test_ninety_degree_front_edge_is_above_the_hinge(self):
        v = lid_corners(90)
        self.assertPoint(v[2], (18, 12, 42.2))
        self.assertPoint(v[3], (-18, 12, 42.2))

    def test_rear_edge_stays_on_the_same_hinge(self):
        axis = hinge_axis()
        for angle in (0, 35, 90, 100):
            v = lid_corners(angle)
            self.assertPoint(v[0], axis[0])
            self.assertPoint(v[1], axis[1])

    def test_rotation_preserves_lid_size(self):
        v = lid_corners(100)
        self.assertAlmostEqual(math.dist(v[0], v[1]), 36)
        self.assertAlmostEqual(math.dist(v[1], v[2]), 24)
        self.assertAlmostEqual(math.dist(v[0], v[2]), math.sqrt(36**2 + 24**2))
        self.assertAlmostEqual(math.dist(v[0], v[4]), 1)

    def test_open_lid_is_not_a_horizontal_floating_slab(self):
        v = lid_corners(100)
        self.assertGreater(v[2][2] - v[0][2], 23)
        self.assertGreater(v[2][1], 12)
        self.assertTrue(all(p[2] >= 18 for p in v))

    def test_open_lid_inside_faces_towards_the_front(self):
        n = lid_inner_normal(100)
        self.assertGreater(-n[1], 0.98)
        self.assertGreater(n[2], 0)
        self.assertLess(n[2], 0.2)


if __name__ == '__main__':
    unittest.main()
