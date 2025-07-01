import unittest
import importlib.machinery
import importlib.util
import sys
import os
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

                                                          
class DummyPag:
    def __init__(self):
        self.FAILSAFE = False
        self.PAUSE = 0
        self.ImageNotFoundException = Exception
        self._pos = [0, 0]
        self.easeInQuad = self.easeOutQuad = self.easeInOutQuad = (
            self.easeInCubic
        ) = self.easeOutCubic = self.easeInOutCubic = lambda x: x

    def locateOnScreen(self, *a, **k):
        raise ValueError('needle dimension(s) exceed the haystack image or region dimensions')

    def confirm(self, *a, **k):
        return 'Varrock'

                                      
    def moveTo(self, *a, **k):
        pass
    def moveRel(self, *a, **k):
        pass
    def position(self):
        return tuple(self._pos)
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

file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'EssayReview.pyw')
loader = importlib.machinery.SourceFileLoader('src.EssayReview', file_path)
spec = importlib.util.spec_from_loader('src.EssayReview', loader)
ER = importlib.util.module_from_spec(spec)
loader.exec_module(ER)

class SafeLocateTest(unittest.TestCase):
    def test_safe_locate_handles_value_error(self):
        self.assertIsNone(ER.safe_locate('dummy.png'))

if __name__ == '__main__':
    unittest.main()
