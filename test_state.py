import unittest
import io
import os

from unittest.mock import patch, mock_open

from model import Issue
from features.state_analysis import StateAnalysis
import config

class TestState(unittest.TestCase):
    
    # Simple test case for state analysis
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_simple_state(self, mock_stdout, mock_json_load, mock_file):

        # json that will be returned from data_loader when called since below config path set to None
        mock_json_load.return_value = [
            {
                "state": "closed",
                "creator": "alice",
                "created_date": "2025-04-28T12:34:56Z",
                "updated_date": "2026-04-28T12:34:56Z",
                "labels": []
            },
            {
                "state": "open",
                "creator": "alice",
                "created_date": "2025-04-28T12:34:56Z",
                "updated_date": "2026-04-28T12:34:56Z",
                "labels": []
            },
        ]

        with patch("config._get_default_path", return_value=None):
            StateAnalysis().run()

        output = mock_stdout.getvalue()

        # Check to make sure the expected things are in the output
        self.assertIn("Found 2 issues", output)
        self.assertIn("open: 1", output)
        self.assertIn("closed: 1", output)

        self.assertIn("Top contributor: alice with 1 open issues", output)
        self.assertIn("alice: 1", output)

    # Test if no issues are loaded
    @patch('features.state_analysis.DataLoader')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_no_issues(self, mock_stdout, mock_loader):
        mock_loader.return_value.get_issues.return_value = []

        StateAnalysis().run()

        output = mock_stdout.getvalue()

        self.assertIn("Found 0 issues", output)
        self.assertIn("No users with open issues", output)

    # --- Tests to get coverage into config.py ---

    # Testing it can read json
    @patch("builtins.open", new_callable=mock_open, read_data='{"hello": "json", "file": 123}')
    @patch("os.path.isfile", return_value=True)
    @patch("os.getcwd", return_value="/fake/root")
    def test_config_file_loaded(self, mock_cwd, mock_isfile, mock_file):
        config._init_config()

        self.assertEqual(config.get_parameter("hello"), "json")
        self.assertEqual(config.get_parameter("file"), 123)
    
    # Testing it can read environment variables
    @patch("os.path.isfile", return_value=False)
    @patch("os.getcwd", return_value="/fake/root")
    def test_config_env_override(self, mock_cwd, mock_isfile):
        os.environ["TEST_PARAM"] = "hello"

        config._init_config()

        self.assertEqual(config.get_parameter("TEST_PARAM"), "hello")

    # Testing out the convert to type value parsing
    def test_config_json_env_value(self):
        os.environ["TEST_PARAM"] = 'json:{"a": 1, "b": 2}'

        config._init_config()

        self.assertEqual(config.get_parameter("TEST_PARAM"), {"a": 1, "b": 2})

    # Testing fallback option for if no path found
    @patch("os.path.isfile", return_value=False)
    @patch("os.getcwd", return_value="/fake/root")
    def test_config_default_fallback(self, mock_cwd, mock_isfile):
        config._init_config()

        self.assertEqual(config.get_parameter("missing", default="fallback"), "fallback")
        self.assertIsNone(config.get_parameter("missing_no_default"))

if __name__ == "__main__":
    unittest.main()