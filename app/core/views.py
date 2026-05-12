import logging

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import AnalysisResultDtoSerializer
from core.services import AnalyserService, RulesService

logger = logging.getLogger(__name__)


class AnalysisView(APIView):
    """
    View for analysing a presentation file.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Accepts a file upload, analyses it using AnalyserService and returns the analysis results as JSON.
        """
        if "file" not in request.data:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.data["file"]
        rules_config = request.data.getlist("rules")

        try:
            analyser_service = AnalyserService()
            analysis_result = analyser_service.analyse(uploaded_file, rules_config)
            serializer = AnalysisResultDtoSerializer(analysis_result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.exception(f"Validation error during analysis: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("An unexpected error occurred during presentation analysis.")
            return Response({"error": "An unexpected error occurred during presentation analysis."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RulesView(APIView):
    """
    View for retrieving the rules used in the analysis.
    """
    def get(self, request, rule_id=None, *args, **kwargs):
        """
        Returns all rules or a single rule by its ID as JSON.
        """
        try:
            rules_service = RulesService()
            if rule_id:
                rule_id = rule_id.upper()
                rule = rules_service.get_rule_by_id(rule_id)
                if rule:
                    return Response(rule, status=status.HTTP_200_OK)
                else:
                    return Response({"error": f"Rule with id {rule_id} not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                rules = rules_service.get_rules()
                return Response(rules, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "An unexpected error occurred while retrieving rules."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
