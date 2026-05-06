"""
state_analysis.py

Analyze Poetry GitHub issues, count total, and by state and display results in
the console.

Usage:
    python state_analysis.py
"""
from typing import List

from features.data_loader import DataLoader
from model import Issue
from collections import defaultdict

class StateAnalysis:
    """
    Implements an analysis of GitHub issues by state and outputs the result of
    to the console as plain text.
    """
    def run(self):
        """
        Starting point for the state analysis.

        Run this method to begin analyzing issue states and display the
        results in the console.
        """
        # Load issues from the data file
        issues: List[Issue] = DataLoader().get_issues()

        # Count the number of open and closed issues
        state_count = defaultdict(int)
        for issue in issues:
            state_count[issue.state] += 1

        # Print open and closed issues
        output = f'Found {len(issues)} issues with the following state counts: \n'
        for state, count in state_count.items():
            output += f'\t{state}: {count}\n'
        print(output)
        
        # For each user, count how many issues are open
        user_open_count = defaultdict(int)
        for issue in issues:
            if issue.creator and issue.state == 'open':
                user_open_count[issue.creator] += 1
        
        # Determine the top contributor
        if user_open_count:
            top_contributor = max(user_open_count, key=lambda u: user_open_count[u])
            top_count = user_open_count[top_contributor]
            print(f'Top contributor: {top_contributor} with {top_count} open issues\n')
        else:
            print('No users with open issues.\n')
        
        # Print open issue counts per user
        output = f'Open issue counts per user ({len(user_open_count)} users with open issues):\n'
        for creator, open_count in user_open_count.items():
            output += f'{creator}: {open_count}\n'
        print(output)

if __name__ == '__main__':
    # Invoke run method to start analyzing issue states and display results
    # in the console.
    StateAnalysis().run()