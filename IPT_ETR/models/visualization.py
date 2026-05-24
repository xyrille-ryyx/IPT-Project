import os
from uuid import uuid4

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt


class Visualization:

    def __init__(self, df, output_dir='static/charts'):
        self.df = df
        self.output_dir = output_dir
        self.chart_id = uuid4().hex[:8]
        os.makedirs(self.output_dir, exist_ok=True)

    def stress_chart(self, filename=None):
        filename = filename or f'stress_chart_{self.chart_id}.png'
        chart_path = os.path.join(self.output_dir, filename)

        plt.figure(figsize=(8, 5))
        stress_counts = self.df['stress_level'].value_counts().sort_index()

        if stress_counts.empty:
            self._empty_chart("Stress Level Distribution", chart_path)
            return chart_path

        stress_counts.plot(kind='bar', color='#0C4498', edgecolor='#082F6B')
        plt.title("Stress Level Distribution")
        plt.xlabel("Stress Level")
        plt.ylabel("Count")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(chart_path, dpi=130)
        plt.close()

        return chart_path

    def sleep_chart(self, filename=None):
        filename = filename or f'sleep_chart_{self.chart_id}.png'
        chart_path = os.path.join(self.output_dir, filename)
        sleep_by_age = self.df.groupby('age')['sleep_hours'].mean().sort_index()

        if sleep_by_age.empty:
            self._empty_chart("Average Sleep by Age", chart_path)
            return chart_path

        plt.figure(figsize=(8, 5))
        plt.plot(sleep_by_age.index, sleep_by_age.values, marker='o', linewidth=2.5, color='#0C4498')
        plt.fill_between(sleep_by_age.index, sleep_by_age.values, color='#0C4498', alpha=0.15)
        plt.title("Average Sleep Hours by Age")
        plt.xlabel("Age")
        plt.ylabel("Average Sleep Hours")
        plt.grid(axis='y', alpha=0.25)
        plt.tight_layout()
        plt.savefig(chart_path, dpi=130)
        plt.close()

        return chart_path

    def social_media_chart(self, filename=None):
        filename = filename or f'social_media_chart_{self.chart_id}.png'
        chart_path = os.path.join(self.output_dir, filename)
        platform_usage = self.df['platform_usage'].value_counts().head(8)

        if platform_usage.empty:
            self._empty_chart("Platform Usage", chart_path)
            return chart_path

        plt.figure(figsize=(8, 5))
        platform_usage.sort_values().plot(kind='barh', color='#E59913', edgecolor='#A86A00')
        plt.title("Most Used Social Media Platforms")
        plt.xlabel("Teen Count")
        plt.ylabel("Platform")
        plt.tight_layout()
        plt.savefig(chart_path, dpi=130)
        plt.close()

        return chart_path

    def risk_chart(self, filename=None):
        filename = filename or f'risk_chart_{self.chart_id}.png'
        chart_path = os.path.join(self.output_dir, filename)
        risk_metrics = {
            'High stress': int((self.df['stress_level'] >= 8).sum()),
            'High anxiety': int((self.df['anxiety_level'] >= 8).sum()),
            'Depression label': int((self.df['depression_label'] == 1).sum())
        }

        plt.figure(figsize=(8, 5))
        plt.bar(risk_metrics.keys(), risk_metrics.values(), color=['#0C4498', '#3B67C2', '#E59913'])
        plt.title("Mental Health Risk Indicators")
        plt.xlabel("Indicator")
        plt.ylabel("Teen Count")
        plt.xticks(rotation=10)
        plt.tight_layout()
        plt.savefig(chart_path, dpi=130)
        plt.close()

        return chart_path

    def generate_dashboard_charts(self):
        return {
            'stress_chart': self._static_path(self.stress_chart()),
            'sleep_chart': self._static_path(self.sleep_chart()),
            'social_media_chart': self._static_path(self.social_media_chart()),
            'risk_chart': self._static_path(self.risk_chart())
        }

    def _empty_chart(self, title, chart_path):
        plt.figure(figsize=(8, 5))
        plt.title(title)
        plt.text(
            0.5,
            0.5,
            'No data available for the selected filters',
            ha='center',
            va='center',
            transform=plt.gca().transAxes
        )
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(chart_path, dpi=130)
        plt.close()

    @staticmethod
    def _static_path(chart_path):
        normalized_path = chart_path.replace('\\', '/')
        return normalized_path.split('static/', 1)[-1]
