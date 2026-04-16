
from typing import List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

from data_loader import DataLoader
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
        self.LABEL:str = config.get_parameter('label')
        self.labels = {}
    
    def run(self):
        issues:List[Issue] = DataLoader().get_issues()
        closed = 0

        ### BASIC STATISTICS
        # Calculate the average time it takes for an issue to close (complete) per label
        for i in issues:
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
        
        print("Average time for issue to close per label (seconds)")

        if self.LABEL is None:
            for l in self.labels:
                print(l + ": " + str(self.labels[l]) + " seconds")

            ### BAR CHART
            df = pd.DataFrame(list(self.labels.items()), columns=["label", "seconds"])
            df = df.sort_values(by="seconds", ascending=False)
            
            # Display a graph of the average times per label if no label specified
            df.plot(x="label", y="seconds", kind="bar", figsize=(14, 8), title="Average Time to Close Issue By Label")

            # X axis configs
            plt.xlabel("Label Names")
            plt.xticks(rotation=80) 

            # Y axis configs
            plt.ylabel("Average Time to Close (seconds)")
            plt.yscale('log')
            
            # Plot the chart
            plt.tight_layout()
            plt.show() 
        else:
            print(self.LABEL + ": " + str(self.labels[self.LABEL]) + " seconds")

if __name__ == '__main__':
    # Invoke run method when running this module directly
    LabelsAnalysis().run()