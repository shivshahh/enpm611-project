import unittest
import io

from unittest.mock import patch

from model import Issue
from labels_analysis import LabelsAnalysis

class TestLabels(unittest.TestCase):
    
    # Initial test on the labels analysis run()
    @patch('labels_analysis.plt.show') # Stop the graph from showing up
    @patch('labels_analysis.DataLoader') # Control what data gets loaded in
    @patch('labels_analysis.config.get_parameter', return_value=None) # Simulate no label arg passed
    @patch('sys.stdout', new_callable=io.StringIO) # Let us retrieve stdout
    def test_simple_labels(self, mock_stdout, mock_config, mock_loader, mock_show):
        # Mock a small issue to confirm the output
        mock_issue = Issue({
            "labels": ["bug"],
            "state": "closed",
            "created_date": "2025-04-28T12:34:56Z",
            "updated_date": "2026-04-28T12:34:56Z"
        })

        # Mock loading in the issue above
        mock_loader.return_value.get_issues.return_value = [mock_issue]

        # Actually run labels analyis
        LabelsAnalysis().run()
        
        output = mock_stdout.getvalue()
    
        self.assertIn("bug average time to close:", output)

    # MORE TESTS HERE

if __name__ == "__main__":
    unittest.main()