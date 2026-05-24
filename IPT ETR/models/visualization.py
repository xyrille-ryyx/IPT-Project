import matplotlib.pyplot as plt
import os

class Visualization:

    def __init__(self, df):
        self.df = df

    def stress_chart(self):

        plt.figure(figsize=(6,4))

        self.df['stress_level'].value_counts().plot(
            kind='bar'
        )

        plt.title("Stress Level Distribution")
        plt.xlabel("Stress Level")
        plt.ylabel("Count")

        chart_path = 'static/charts/stress_chart.png'

        plt.savefig(chart_path)
        plt.close()

        return chart_path

    def sleep_chart(self):

        plt.figure(figsize=(6,4))

        self.df['sleep_hours'].plot(
            kind='hist',
            bins=10
        )

        plt.title("Sleep Hours Distribution")

        chart_path = 'static/charts/sleep_chart.png'

        plt.savefig(chart_path)
        plt.close()

        return chart_path