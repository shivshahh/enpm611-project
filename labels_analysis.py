
from typing import List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_loader import DataLoader
from model import Issue,Event
import config
from collections import defaultdict

class LabelsAnalysis:
    """
    Implements an example analysis of GitHub
    issues and outputs the result of that analysis.
    """
    
    def __init__(self):
        """
        Constructor
        """
        # Parameter is passed in via command line (--user)
        self.labels:str = config.get_parameter('labels')
        self.label_count = defaultdict(int)
        self.year        = defaultdict(int)
    
    def run(self, filter_on_year=False, year=2026):
        """
        Starting point for this analysis.
        
        Note: this is just an example analysis. You should replace the code here
        with your own implementation and then implement two more such analyses.
        """
        issues:List[Issue] = DataLoader().get_issues()
        
        ### BASIC STATISTICS
        # Calculate the total number of events for a specific user (if specified in command line args)

        for issue in issues:
            if filter_on_year:
                if issue.created_date.year != year:
                    continue 
                else:
                    for label in issue.labels:
                        self.label_count[label] += 1
                        self.year[issue.created_date.year] += 1
        output:str = f'Found {len(issues)} issues with the following label counts: \n'
        for label, count in self.label_count.items():
            output += f'\t{label}: {count}\n'
        print('\n\n'+output+'\n\n')

        ### BAR CHART
        # Display a graph of the top 50 labels of issues
        top_n:int = 50
        # Create a dataframe (with only the label's name) to make statistics a lot easier
        df = pd.DataFrame.from_records([{'label':label} for issue in issues for label in issue.labels])
        # Determine the number of issues for each label and generate a bar chart of the top N
        df_hist = df.groupby(df["label"]).value_counts().nlargest(top_n).plot(kind="bar", figsize=(14,8), title=f"Top {top_n} issue labels")
        # Set axes labels
        df_hist.set_xlabel("Label Names")
        df_hist.set_ylabel("# of issues with label")
        # Plot the chart
        plt.show() 
                        
    

if __name__ == '__main__':
    # Invoke run method when running this module directly
    LabelsAnalysis().run(filter_on_year=True, year=2026)