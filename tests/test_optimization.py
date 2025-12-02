
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock dependencies before importing rl_env_realtime
sys.modules['mss'] = MagicMock()
sys.modules['keyboard'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()

from src.rl_env_realtime import RealtimeGameEnv

class TestRealtimeOptimization(unittest.TestCase):
    def setUp(self):
        # Mock config loader
        with patch('src.rl_env_realtime.load_config') as mock_load:
            mock_load.return_value = {}
            
            # Mock cv2.imread to return None (so no templates are loaded)
            with patch('cv2.imread', return_value=None):
                self.env = RealtimeGameEnv(game="TEST", frame_skip=4)
    
    def test_frame_skip_logic(self):
        """Test if step() executes action frame_skip times"""
        
        # Mock methods
        self.env._execute_action = MagicMock()
        self.env._check_danger_monster = MagicMock()
        self.env._calculate_reward = MagicMock(return_value=1.0)
        self.env._preprocess_frame = MagicMock(return_value=np.zeros((84, 84), dtype=np.uint8))
        self.env._get_observation = MagicMock(return_value=np.zeros((4, 84, 84), dtype=np.uint8))
        
        # Mock sct.grab
        self.env.sct.grab = MagicMock(return_value=np.zeros((100, 100, 3), dtype=np.uint8))
        
        # Run step
        obs, reward, done, truncated, info = self.env.step(1)
        
        # Verify _execute_action was called 4 times
        self.assertEqual(self.env._execute_action.call_count, 4)
        
        # Verify reward is accumulated (1.0 * 4 = 4.0)
        self.assertEqual(reward, 4.0)
        
        print("✅ Frame skip logic verified: Action executed 4 times, Reward accumulated.")

if __name__ == '__main__':
    unittest.main()
