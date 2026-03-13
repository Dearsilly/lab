from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
from model import EssayScorer

app = Flask(__name__)
api = Api(app)

# Initialize the scorer
scorer = EssayScorer()

# Request parser for validation
essay_parser = reqparse.RequestParser()
essay_parser.add_argument('essay', type=str, required=True, help='Essay text is required')
essay_parser.add_argument('essay_set', type=int, choices=[1,2,3,4,5,6,7,8], help='Essay set must be 1-8')


class EssayScore(Resource):
    """Resource for predicting essay scores."""
    
    def post(self):
        """POST /predict - Predict essay score from JSON request.
        
        Request Body:
            {
                "essay": "Your essay text here...",
                "essay_set": 1  (optional, auto-detected if not provided)
            }
        
        Response:
            {
                "predicted_score": 8.5,
                "essay_set": 1,
                "score_range": [2, 12]
            }
        """
        args = essay_parser.parse_args()
        
        try:
            result = scorer.predict(args['essay'], args.get('essay_set'))
            return jsonify(result)
        except Exception as e:
            return {'error': str(e)}, 500


class Health(Resource):
    """Resource for health check."""
    
    def get(self):
        """GET /health - Check API health status."""
        return {
            'status': 'healthy',
            'device': str(scorer.device),
            'model_loaded': scorer.model is not None
        }


class ScoreRange(Resource):
    """Resource for getting score ranges by essay set."""
    
    def get(self, essay_set):
        """GET /score-range/<int:essay_set> - Get score range for a specific set.
        
        Parameters:
            essay_set (int): Essay set number (1-8)
        
        Response:
            {
                "essay_set": 1,
                "score_range": [2, 12],
                "description": "Set 1 score range"
            }
        """
        if essay_set not in scorer.score_ranges:
            return {'error': f'Invalid essay_set: {essay_set}. Must be 1-8.'}, 400
        
        score_min, score_max = scorer.score_ranges[essay_set]
        return {
            'essay_set': essay_set,
            'score_range': [score_min, score_max],
            'description': f'Set {essay_set} score range: {score_min}-{score_max}'
        }


class AllScoreRanges(Resource):
    """Resource for getting all score ranges."""
    
    def get(self):
        """GET /score-ranges - Get score ranges for all essay sets."""
        return {
            'score_ranges': {
                str(k): list(v) for k, v in scorer.score_ranges.items()
            }
        }


# API Routes
api.add_resource(EssayScore, '/predict')
api.add_resource(Health, '/health')
api.add_resource(ScoreRange, '/score-range/<int:essay_set>')
api.add_resource(AllScoreRanges, '/score-ranges')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
