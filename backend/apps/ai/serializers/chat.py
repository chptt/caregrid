from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=10000, min_length=1)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    patient_id = serializers.IntegerField(required=False, allow_null=True)


class ExplanationSerializer(serializers.Serializer):
    reasoning = serializers.CharField()
    confidence = serializers.CharField()
    disclaimer = serializers.CharField()
    follow_up = serializers.CharField()


class ChatResponseSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()
    response = serializers.CharField()
    agent_type = serializers.CharField()
    tokens_used = serializers.IntegerField()
    explanation = ExplanationSerializer(required=False)
