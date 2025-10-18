"""
Machine Learning Predictor Module
Predicts injury return timelines and recovery dates using historical data
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os
from injury_database import InjuryDatabase


class InjuryPredictor:
    """ML-based injury return timeline predictor"""

    def __init__(self, db: InjuryDatabase, model_path: str = "models/injury_predictor.pkl"):
        """
        Initialize the injury predictor

        Args:
            db: InjuryDatabase instance
            model_path: Path to save/load trained model
        """
        self.db = db
        self.model_path = model_path
        self.model = None
        self.feature_columns = []
        self.is_trained = False

        # Ensure models directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Try to load existing model
        self._load_model()

    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from historical injury database

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        # Query all injuries with resolved recovery times
        query = '''
            SELECT
                player_name,
                position,
                team,
                injury_status,
                injury_body_part,
                days_missed,
                season,
                week
            FROM injuries
            WHERE days_missed IS NOT NULL
            AND days_missed > 0
            AND injury_body_part IS NOT NULL
        '''

        self.db.cursor.execute(query)
        rows = self.db.cursor.fetchall()

        if not rows:
            raise ValueError("No training data available. Please load historical data first.")

        # Convert to DataFrame
        data = pd.DataFrame([dict(row) for row in rows])

        # Feature engineering
        # 1. Encode injury body part
        data['body_part_encoded'] = pd.Categorical(data['injury_body_part']).codes

        # 2. Encode position
        data['position_encoded'] = pd.Categorical(data['position']).codes

        # 3. Encode injury status
        status_severity = {
            'Questionable': 1,
            'Doubtful': 2,
            'Out': 3,
            'PUP': 4,
            'IR': 5,
            'Suspended': 0  # Different category
        }
        data['status_severity'] = data['injury_status'].map(status_severity).fillna(0)

        # 4. Get player's injury history (number of previous injuries)
        data['player_injury_count'] = data['player_name'].apply(
            lambda name: len(self.db.get_player_injury_history(name))
        )

        # 5. Check for recurring injuries (same body part)
        def get_recurrence_count(row):
            recurring = self.db.get_recurring_injuries(row['player_name'])
            return recurring.get(row['injury_body_part'], 1)

        data['recurrence_count'] = data.apply(get_recurrence_count, axis=1)

        # 6. Time of season (early/late season injuries may differ)
        data['season_progress'] = data['week'] / 18.0  # Normalize to 0-1

        # Select features
        feature_cols = [
            'body_part_encoded',
            'position_encoded',
            'status_severity',
            'player_injury_count',
            'recurrence_count',
            'season_progress'
        ]

        X = data[feature_cols]
        y = data['days_missed']

        self.feature_columns = feature_cols

        # Store encodings for later use
        self.body_part_mapping = dict(enumerate(pd.Categorical(data['injury_body_part']).categories))
        self.position_mapping = dict(enumerate(pd.Categorical(data['position']).categories))

        return X, y

    def train_model(self, test_size: float = 0.2, random_state: int = 42):
        """
        Train the Random Forest model

        Args:
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility
        """
        print("\n" + "="*60)
        print("TRAINING INJURY RETURN TIMELINE PREDICTOR")
        print("="*60 + "\n")

        # Prepare data
        print("Preparing training data...")
        X, y = self.prepare_training_data()

        print(f"Total training samples: {len(X)}")
        print(f"Features: {self.feature_columns}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        print(f"Training samples: {len(X_train)}")
        print(f"Testing samples: {len(X_test)}")

        # Train Random Forest
        print("\nTraining Random Forest Regressor...")
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        print("\nEvaluating model...")
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)

        print("\nModel Performance:")
        print(f"  Training MAE: {train_mae:.2f} days")
        print(f"  Testing MAE: {test_mae:.2f} days")
        print(f"  Training R²: {train_r2:.3f}")
        print(f"  Testing R²: {test_r2:.3f}")

        # Feature importance
        print("\nFeature Importance:")
        importances = self.model.feature_importances_
        for feature, importance in sorted(zip(self.feature_columns, importances),
                                         key=lambda x: x[1], reverse=True):
            print(f"  {feature}: {importance:.3f}")

        self.is_trained = True

        # Save model
        self._save_model()

        print("\n" + "="*60)
        print("MODEL TRAINING COMPLETE")
        print("="*60)

    def predict_recovery_time(self, injury_data: Dict) -> Dict:
        """
        Predict recovery time for an injury

        Args:
            injury_data: Dictionary with injury information

        Returns:
            Dictionary with prediction and confidence intervals
        """
        if not self.is_trained and self.model is None:
            # Try to load model
            if not self._load_model():
                return {
                    'predicted_days': None,
                    'confidence_low': None,
                    'confidence_high': None,
                    'error': 'Model not trained. Please train the model first.'
                }

        # Encode features
        features = self._encode_injury(injury_data)

        if features is None:
            return {
                'predicted_days': None,
                'confidence_low': None,
                'confidence_high': None,
                'error': 'Could not encode injury features'
            }

        # Make prediction
        predicted_days = self.model.predict([features])[0]

        # Get prediction intervals from individual trees
        tree_predictions = np.array([tree.predict([features])[0]
                                    for tree in self.model.estimators_])

        confidence_low = np.percentile(tree_predictions, 10)
        confidence_high = np.percentile(tree_predictions, 90)

        # Apply injury status constraints (NFL rules)
        injury_status = injury_data.get('injury_status', '')

        # IR/PUP requires minimum 4 games (approximately 4 weeks = 28 days)
        if injury_status in ['IR', 'PUP']:
            min_days = 28  # 4 weeks minimum
            predicted_days = max(predicted_days, min_days)
            confidence_low = max(confidence_low, min_days)
            confidence_high = max(confidence_high, min_days + 14)  # At least 4-6 weeks

        # Out status typically means at least 1 week
        elif injury_status == 'Out':
            min_days = 7  # At least 1 week
            predicted_days = max(predicted_days, min_days)
            confidence_low = max(confidence_low, 3)

        # Suspended has exact timelines (use prediction as-is)
        # Questionable/Doubtful are short-term (use prediction as-is)

        # Calculate expected return date
        expected_return = datetime.now() + timedelta(days=int(predicted_days))

        # Convert to NFL weeks correctly
        # Formula: current week + ceil(days_out / 7)
        # Example: 19 days = current week + 3 weeks = Week (current + 3)
        current_week = self._get_current_week()
        weeks_to_add = int(np.ceil(predicted_days / 7.0))  # Round UP
        return_week = current_week + weeks_to_add

        return {
            'predicted_days': int(predicted_days),
            'confidence_low': int(confidence_low),
            'confidence_high': int(confidence_high),
            'expected_return_date': expected_return.strftime('%Y-%m-%d'),
            'weeks_out': weeks_to_add,  # How many weeks from now
            'return_week': return_week,  # Which NFL week they return
            'current_week': current_week,
            'confidence_level': 80,  # Based on 10th-90th percentile
            'injury_status': injury_status  # Include for reference
        }

    def _encode_injury(self, injury_data: Dict) -> Optional[List]:
        """
        Encode injury data into feature vector

        Args:
            injury_data: Dictionary with injury information

        Returns:
            Feature vector or None if encoding fails
        """
        try:
            # Get injury body part encoding
            body_part = injury_data.get('injury_body_part')
            if not body_part:
                return None

            # Find matching body part in our mapping
            body_part_code = None
            for code, name in self.body_part_mapping.items():
                if name.lower() == body_part.lower():
                    body_part_code = code
                    break

            if body_part_code is None:
                # Use average encoding for unknown body parts
                body_part_code = len(self.body_part_mapping) // 2

            # Get position encoding
            position = injury_data.get('position')
            position_code = None
            for code, pos in self.position_mapping.items():
                if pos == position:
                    position_code = code
                    break

            if position_code is None:
                position_code = 0

            # Status severity
            status_severity_map = {
                'Questionable': 1,
                'Doubtful': 2,
                'Out': 3,
                'PUP': 4,
                'IR': 5,
                'Suspended': 0
            }
            status_severity = status_severity_map.get(
                injury_data.get('injury_status', 'Questionable'), 1
            )

            # Player injury history
            player_name = injury_data.get('name')
            if player_name:
                history = self.db.get_player_injury_history(player_name)
                player_injury_count = len(history)

                # Recurrence count
                recurring = self.db.get_recurring_injuries(player_name)
                recurrence_count = recurring.get(body_part, 1)
            else:
                player_injury_count = 0
                recurrence_count = 1

            # Season progress (assume current week)
            current_week = self._get_current_week()
            season_progress = current_week / 18.0

            # Build feature vector
            features = [
                body_part_code,
                position_code,
                status_severity,
                player_injury_count,
                recurrence_count,
                season_progress
            ]

            return features

        except Exception as e:
            print(f"Error encoding injury: {e}")
            return None

    def _get_current_week(self) -> int:
        """Get current NFL week"""
        now = datetime.now()
        season_start = datetime(now.year if now.month >= 9 else now.year - 1, 9, 1)

        if now < season_start:
            return 1

        weeks_elapsed = (now - season_start).days // 7
        return min(weeks_elapsed + 1, 18)

    def _save_model(self):
        """Save trained model to disk"""
        try:
            model_data = {
                'model': self.model,
                'feature_columns': self.feature_columns,
                'body_part_mapping': self.body_part_mapping,
                'position_mapping': self.position_mapping,
                'is_trained': self.is_trained
            }

            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)

            print(f"\nModel saved to {self.model_path}")

        except Exception as e:
            print(f"Error saving model: {e}")

    def _load_model(self) -> bool:
        """
        Load trained model from disk

        Returns:
            True if model loaded successfully, False otherwise
        """
        if not os.path.exists(self.model_path):
            return False

        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.model = model_data['model']
            self.feature_columns = model_data['feature_columns']
            self.body_part_mapping = model_data.get('body_part_mapping', {})
            self.position_mapping = model_data.get('position_mapping', {})
            self.is_trained = model_data.get('is_trained', True)

            print(f"Model loaded from {self.model_path}")
            return True

        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def get_historical_comparison(self, injury_data: Dict, limit: int = 5) -> List[Dict]:
        """
        Find similar historical injuries for comparison

        Args:
            injury_data: Current injury information
            limit: Number of similar injuries to return

        Returns:
            List of similar injury records
        """
        body_part = injury_data.get('injury_body_part')
        position = injury_data.get('position')

        if not body_part or not position:
            return []

        similar = self.db.get_similar_injuries(body_part, position, limit)

        return similar


def main():
    """Main entry point for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Train and use injury predictor')
    parser.add_argument('--train', action='store_true', help='Train the model')
    parser.add_argument('--predict', action='store_true', help='Test prediction')

    args = parser.parse_args()

    with InjuryDatabase() as db:
        predictor = InjuryPredictor(db)

        if args.train:
            try:
                predictor.train_model()
            except ValueError as e:
                print(f"\nError: {e}")
                print("Please run 'python historical_data_loader.py --init' first")

        elif args.predict:
            # Test prediction with sample data
            test_injury = {
                'name': 'Test Player',
                'position': 'RB',
                'injury_status': 'Out',
                'injury_body_part': 'Hamstring'
            }

            print("\nTesting prediction with sample injury:")
            print(f"  Position: {test_injury['position']}")
            print(f"  Body Part: {test_injury['injury_body_part']}")
            print(f"  Status: {test_injury['injury_status']}")

            prediction = predictor.predict_recovery_time(test_injury)

            if prediction.get('error'):
                print(f"\nError: {prediction['error']}")
            else:
                print(f"\nPrediction:")
                print(f"  Expected days out: {prediction['predicted_days']}")
                print(f"  Range: {prediction['confidence_low']}-{prediction['confidence_high']} days")
                print(f"  Weeks out: {prediction['weeks_out']}")
                print(f"  Expected return: {prediction['expected_return_date']}")

        else:
            print("Please specify --train or --predict")
            print("Use --help for more information")


if __name__ == "__main__":
    main()
