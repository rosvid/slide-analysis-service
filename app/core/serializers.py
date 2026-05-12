"""
Serialise the data to a readable JSON format to present the analysis results through the API.
"""

from rest_framework import serializers


class FileInfoDtoSerializer(serializers.Serializer):
    file_name = serializers.CharField()
    file_size = serializers.CharField()
    total_slides = serializers.IntegerField()


class SummaryDtoSerializer(serializers.Serializer):
    total_issues_found = serializers.IntegerField()
    slides_with_issues = serializers.IntegerField()
    rules_checked = serializers.ListField(child=serializers.CharField())


class IssueDtoSerializer(serializers.Serializer):
    rule_id = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField()


class SlideResultDtoSerializer(serializers.Serializer):
    slide_number = serializers.IntegerField()
    has_issues = serializers.BooleanField()
    issues = IssueDtoSerializer(many=True)


class AnalysisResultDtoSerializer(serializers.Serializer):
    analysis_id = serializers.CharField()
    analysis_timestamp = serializers.CharField()
    file_info = FileInfoDtoSerializer()
    summary = SummaryDtoSerializer()
    global_issues = IssueDtoSerializer(many=True)
    slide_results = SlideResultDtoSerializer(many=True)
