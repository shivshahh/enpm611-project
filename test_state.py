import unittest
import io

from unittest.mock import patch

from model import Issue
from features.state_analysis import StateAnalysis

class TestState(unittest.TestCase):
    
    # Initial test on the state analysis run()
    @patch('features.state_analysis.DataLoader') # Control what data gets loaded in
    @patch('sys.stdout', new_callable=io.StringIO) # Let us retrieve stdout
    def test_simple_state(self, mock_stdout, mock_loader):
        # Mock a small issue to confirm the output
        mock_issues =  [
            Issue({
                "state": "closed",
                "creator": "alice",
                "created_date": "2025-04-28T12:34:56Z",
                "updated_date": "2026-04-28T12:34:56Z"
                }),
            Issue({
                "state": "open",
                "creator": "alice",
                "created_date": "2025-04-28T12:34:56Z",
                "updated_date": "2026-04-28T12:34:56Z"
            }),
        ]

        # Mock loading in the issue above
        mock_loader.return_value.get_issues.return_value = mock_issues

        # Actually run state analyis
        StateAnalysis().run()
        
        output = mock_stdout.getvalue()
    
        # Assertions that these lines are in the output
        # Chekcing the full string not neccessary
        self.assertIn("Found 2 issues", output)
        self.assertIn("open: 1", output)
        self.assertIn("closed: 1", output)

        self.assertIn("Top contributor: alice with 1 open issues", output)
        self.assertIn("alice: 1", output)

    # MORE TESTS HERE

if __name__ == "__main__":
    unittest.main()