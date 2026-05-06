
from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

from features.data_loader import DataLoader
from model import Issue,Event
import config
from collections import defaultdict

class LabelsAnalysis:
    # Will calculate average time issue it takes for issue to close (complete) for each label
    
    def __init__(self):
        """
        Constructor
        """
        # Parameter is passed in via command line (--label)
        self.LABEL: Optional[str] = config.get_parameter('label')
        self.labels = {}
        self.label_count = {}
    
    def run(self):
        issues:List[Issue] = DataLoader().get_issues()
        closed = 0

        ### BASIC STATISTICS

        # Calculate the average time it takes for an issue to close (complete) per label
        # Keep track of how many of each label there is
        for i in issues:
            # Increment label count
            for l in i.labels:
                try:
                    self.label_count[l] += 1
                except KeyError:
                    self.label_count[l] = 1
            
            # If issue is closed then update time tracking
            if i.state == 'closed':
                closed += 1
                creation = i.created_date.timestamp()
                updated = i.updated_date.timestamp()
                length = updated - creation
                for l in i.labels:
                    try:
                        self.labels[l] += length
                    except KeyError:
                        self.labels[l] = length

        for l in self.labels:
            self.labels[l] = int(self.labels[l] // closed)
        
        print("\nLabel statistics:\n")

        if self.LABEL is None:
            for l in self.labels:
                print(l + " average time to close: " + str(self.labels[l]) + " seconds")
                print(l + " found in " + str(self.label_count[l]) + " issues")
                print("---------------------")

            ### BAR CHART
            
            # Averages dataframe
            df_averages = pd.DataFrame(list(self.labels.items()), columns=["label", "seconds"])
            df_averages = df_averages.sort_values(by="seconds", ascending=False)
            avg_fig, avg_axis = plt.subplots(figsize=(14, 8))
            df_averages.plot(x="label", y="seconds", kind="bar", ax=avg_axis, figsize=(14, 8), title="Average Time to Close Issue By Label")

            # X axis configs
            avg_axis.set_xlabel("Labels")
            avg_axis.tick_params(axis='x', rotation=80)

            # Y axis configs
            avg_axis.set_ylabel("Average Time to Close (seconds)")
            avg_axis.set_yscale('log')
            
            # Chart config
            avg_fig.tight_layout()

            # Count dataframe
            df_count = pd.DataFrame(list(self.label_count.items()), columns=["label", "count"])
            df_count = df_count.sort_values(by="count", ascending=False)
            count_fig, count_axis = plt.subplots(figsize=(14,8))
            df_count.plot(x="label", y="count", ax=count_axis, kind="bar", figsize=(14, 8), title="Label Occurences Across All Issues")
            
            # X axis configs
            count_axis.set_xlabel("Labels")
            count_axis.tick_params(axis='x', rotation=80)

            # Y axis configs
            count_axis.set_ylabel("Occurences")
            count_axis.set_yscale('log')
            
            # Chart config
            count_fig.tight_layout()
            
            plt.show() 
        else:
            try:
                print(self.LABEL + " average time to close: " + str(self.labels[self.LABEL]) + " seconds")
                print(self.LABEL + " found in " + str(self.label_count[self.LABEL]) + " issues")
            except KeyError:
                print('Label "' + self.LABEL + '" does not exist in issues')

if __name__ == '__main__':
    # Invoke run method when running this module directly
    LabelsAnalysis().run()
