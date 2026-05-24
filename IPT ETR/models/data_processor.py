import pandas as pd

class DataProcessor:

    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None

    def load_data(self):
        self.df = pd.read_csv(self.filepath)

    def clean_data(self):

        # Remove empty values
        self.df.dropna(inplace=True)

        # Remove duplicates
        self.df.drop_duplicates(inplace=True)

    def get_data(self):
        return self.df