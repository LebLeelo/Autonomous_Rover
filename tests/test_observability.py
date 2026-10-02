import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.common.logger import EventLogger


class ObservabilityTests(unittest.TestCase):
    def test_event_logger_persists_timestamped_state_fault_and_result(self):
        with TemporaryDirectory() as log_dir:
            logger = EventLogger("verification", log_dir=log_dir)
            try:
                logger.state("BOOT -> SELF_TEST")
                logger.error("fault detected: MOTOR_FAILURE")
                logger.info("mission result: SAFE")
            finally:
                logger.close()

            log_path = next(Path(log_dir).glob("*.log"))
            lines = log_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 3)
        self.assertIn("[STATE] BOOT -> SELF_TEST", lines[0])
        self.assertIn("[ERROR] fault detected: MOTOR_FAILURE", lines[1])
        self.assertIn("[INFO] mission result: SAFE", lines[2])
        self.assertTrue(lines[0].startswith("["))


if __name__ == "__main__":
    unittest.main()