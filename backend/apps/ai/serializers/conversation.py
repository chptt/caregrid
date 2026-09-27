from rest_framework import serializers


class ConversationListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    agent_type = serializers.CharField()
    title = serializers.CharField()
    patient_name = serializers.CharField(source='patient.name', allow_null=True)
    patient_id = serializers.IntegerField(source='patient.id', allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    is_active = serializers.BooleanField()
    message_count = serializers.SerializerMethodField()

    def get_message_count(self, obj):
        return getattr(obj, 'message_count', 0)


class MessageSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    role = serializers.CharField()
    content = serializers.CharField()
    tokens_used = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class ConversationDetailSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(source='id')
    agent_type = serializers.CharField()
    title = serializers.CharField()
    patient_name = serializers.CharField(source='patient.name', allow_null=True)
    patient_id = serializers.IntegerField(source='patient.id', allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    messages = serializers.SerializerMethodField()

    def get_messages(self, obj):
        from backend.apps.ai.models import Message
        messages = Message.objects.filter(conversation=obj).order_by('created_at')
        return MessageSerializer(messages, many=True).data
