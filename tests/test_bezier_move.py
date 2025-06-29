import unittest
import importlib.machinery
import importlib.util
import sys
import os
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Dummy pyautogui module to avoid GUI dependencies
class DummyPag:
    def __init__(self):
        self._pos = [0, 0]
        self.FAILSAFE = False
        self.PAUSE = 0
        self.ImageNotFoundException = Exception
        self.easeInQuad = self.easeOutQuad = self.easeInOutQuad = (
            self.easeInCubic
        ) = self.easeOutCubic = self.easeInOutCubic = lambda x: x

    def moveTo(self, x, y, duration=0, tween=None):
        self._pos = [x, y]

    def moveRel(self, dx, dy):
        self._pos[0] += dx
        self._pos[1] += dy

    def position(self):
        return tuple(self._pos)

    def confirm(self, *a, **k):
        return "Varrock"

    def locateOnScreen(self, *a, **k):
        return None

    def click(self, *a, **k):
        pass

    def size(self):
        return (800, 600)

    def press(self, *a, **k):
        pass

    def scroll(self, *a, **k):
        pass

pag = DummyPag()
sys.modules['pyautogui'] = pag
sys.modules['pygetwindow'] = SimpleNamespace()
sys.modules.setdefault('win32gui', SimpleNamespace())
sys.modules.setdefault('win32con', SimpleNamespace())

class DummyOverlay:
    def update_log(self, msg):
        pass
    def set_cape_scale(self, factor):
        pass

# Patch DraftTracker before import
import types
DraftTracker = types.ModuleType('src.DraftTracker')
DraftTracker.DraftTracker = DummyOverlay
sys.modules['src.DraftTracker'] = DraftTracker

file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'EssayReview.pyw')
loader = importlib.machinery.SourceFileLoader('src.EssayReview', file_path)
spec = importlib.util.spec_from_loader('src.EssayReview', loader)
ER = importlib.util.module_from_spec(spec)
loader.exec_module(ER)

class BezierMoveTest(unittest.TestCase):
    def test_final_position(self):
        ER.bezier_move(50, 60, jitter_prob=0, jitter_px=0)
        self.assertEqual(pag.position(), (50, 60))
        self.assertTrue(len(ER.last_move_velocities) > 0)

if __name__ == '__main__':
    unittest.main()
