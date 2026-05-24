import pandas as pd


class DataProcessor:

    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None
        self.original_rows = 0
        self.cleaned_rows = 0

    def load_data(self):
        self.df = pd.read_csv(self.filepath)
        self.original_rows = len(self.df)

    def clean_data(self):
        if self.df is None:
            raise ValueError("Load the dataset before cleaning it.")

        self.df.columns = self.df.columns.str.strip().str.lower()

        text_columns = self.df.select_dtypes(include='object').columns
        for column in text_columns:
            self.df[column] = self.df[column].astype(str).str.strip().str.lower()
            self.df[column] = self.df[column].replace({'': pd.NA, 'nan': pd.NA, 'none': pd.NA})

        numeric_columns = [
            'age',
            'daily_social_media_hours',
            'sleep_hours',
            'screen_time_before_sleep',
            'academic_performance',
            'physical_activity',
            'stress_level',
            'anxiety_level',
            'addiction_level',
            'depression_label'
        ]

        for column in numeric_columns:
            if column in self.df.columns:
                self.df[column] = pd.to_numeric(self.df[column], errors='coerce')

        for column in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[column]):
                fill_value = self.df[column].median()
                if pd.isna(fill_value):
                    fill_value = 0
                self.df[column] = self.df[column].fillna(fill_value)
            else:
                mode_values = self.df[column].mode(dropna=True)
                fill_value = mode_values.iloc[0] if not mode_values.empty else 'unknown'
                self.df[column] = self.df[column].fillna(fill_value)

        self.df.drop_duplicates(inplace=True)
        self.cleaned_rows = len(self.df)

    def get_data(self):
        return self.df

    def cleaning_summary(self):
        return {
            'original_rows': self.original_rows,
            'cleaned_rows': self.cleaned_rows,
            'removed_rows': max(self.original_rows - self.cleaned_rows, 0)
        }


class TeenMentalHealthAnalyzer:

    def __init__(self, df):
        self.df = df.copy()

    def filter_data(self, gender='', age_min='', age_max=''):
        filtered_df = self.df.copy()

        if gender:
            filtered_df = filtered_df[filtered_df['gender'].str.lower() == gender.lower()]

        parsed_min = self._parse_int(age_min)
        parsed_max = self._parse_int(age_max)

        if parsed_min is not None and parsed_max is not None and parsed_min > parsed_max:
            parsed_min, parsed_max = parsed_max, parsed_min

        if parsed_min is not None:
            filtered_df = filtered_df[filtered_df['age'] >= parsed_min]

        if parsed_max is not None:
            filtered_df = filtered_df[filtered_df['age'] <= parsed_max]

        return filtered_df

    def summary(self, filtered_df):
        total_records = len(filtered_df)

        if total_records == 0:
            return {
                'total_records': 0,
                'avg_sleep': 0,
                'avg_stress': 0,
                'depression_rate': 0,
                'avg_social_media': 0,
                'high_risk_count': 0
            }

        high_risk = filtered_df[
            (filtered_df['stress_level'] >= 8)
            | (filtered_df['anxiety_level'] >= 8)
            | (filtered_df['depression_label'] == 1)
        ]

        return {
            'total_records': total_records,
            'avg_sleep': float(round(filtered_df['sleep_hours'].mean(), 1)),
            'avg_stress': float(round(filtered_df['stress_level'].mean(), 1)),
            'depression_rate': float(round(filtered_df['depression_label'].mean() * 100, 1)),
            'avg_social_media': float(round(filtered_df['daily_social_media_hours'].mean(), 1)),
            'high_risk_count': len(high_risk)
        }

    def age_bounds(self):
        return int(self.df['age'].min()), int(self.df['age'].max())

    @staticmethod
    def _parse_int(value):
        try:
            return int(value) if value != '' else None
        except (TypeError, ValueError):
            return None
