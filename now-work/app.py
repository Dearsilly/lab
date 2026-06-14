from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
from model import EssayScorer
from flask_cors import CORS
import logging

# 配置日志（打印请求参数）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
api = Api(app)

# Initialize the scorer
scorer = EssayScorer()
# # ========== 新增：验证模型加载 ==========
# logger.info("Initializing EssayScorer...")
# # 打印模型加载状态（关键！）
# logger.info(f"Model loaded: {scorer.model is not None}")
# logger.info(f"Score ranges: {scorer.score_ranges}")  # 确认Set1的分数范围是[2,12]
# logger.info(f"Device: {scorer.device}")

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

        # ===== 新增：打印接收到的原始请求数据 =====
        logger.info(f"Received request data: {request.get_json()}")
        args = essay_parser.parse_args()
        # ===== 新增：打印解析后的参数 =====
        logger.info(f"Parsed args - essay: {args['essay'][:50]}... (len: {len(args['essay'])}) | essay_set: {args.get('essay_set')}")
        
        try:
"""            # 直接在Flask中调用predict，打印中间结果
            logger.info("=== Local test predict start ===")
            # 复制本地测试时的文本（简化版，测试模型是否真的能预测非2分）
            test_text = "This is a test essay about computers. Computers help us learn and communicate with others. They are important tools in modern life."
            test_result = scorer.predict(test_text, 1)
            logger.info(f"Test text predict result: {test_result}")"""
            # 正式预测
            result = scorer.predict(args['essay'], args.get('essay_set'))
            logger.info(f"Prediction result: {result}")  # 打印预测结果
            return jsonify(result)
        except Exception as e:
            logger.info(f"Prediction result: {result}")  # 打印预测结果
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
