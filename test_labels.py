import unittest
import io

from unittest.mock import patch

from model import Issue
from features.labels_analysis import LabelsAnalysis

class TestLabels(unittest.TestCase):
    
    # Initial test on the labels analysis run()
    @patch('features.labels_analysis.plt.show') # Stop the graph from showing up
    @patch('features.labels_analysis.DataLoader') # Control what data gets loaded in
    @patch('features.labels_analysis.config.get_parameter', return_value=None) # Simulate no label arg passed
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

    # Duplicate label increment (+=1 paths)
    @patch('features.labels_analysis.plt.show') # stop the graph from showing up
    @patch('features.labels_analysis.DataLoader') # control what data gets loaded
    @patch('features.labels_analysis.config.get_parameter', return_value=None) # simulate no label arg passed
    @patch('sys.stdout', new_callable=io.StringIO) # get stdout
    def test_duplicate_label_increments(self, mock_stdout, mock_config, mock_loader, mock_show):
        # Mock issue to confirm the output
        mock_issues = [
            Issue({
                "labels": ["bug"],
                "state": "closed",
                "created_date": "2026-01-23T08:12:56Z",
                "updated_date": "2026-04-28T09:34:56Z"
            }),
            Issue({
                "labels": ["bug"],
                "state": "closed",
                "created_date": "2025-02-15T10:00:00Z",
                "updated_date": "2025-12-28T11:00:00Z"
            })
        
        ]

        # mock loading the issue
        mock_loader.return_value.get_issues.return_value = [mock_issues[0], mock_issues[1]]

        # run label analyis
        analysis = LabelsAnalysis()
        analysis.run()
    
        # ensure the label_count for bug is 2 and not something else
        self.assertEqual(analysis.label_count["bug"], 2)

        # ensure the "bug avaerage time to close:" is in the stdout output
        self.assertIn("bug average time to close:", mock_stdout.getvalue())

if __name__ == "__main__":
    unittest.main()