from rest_framework import serializers


class AssistantChatSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500, trim_whitespace=True)
    history = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True, max_length=8
    )

    def validate_question(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Escribe una pregunta un poco más larga.")
        return value

    def validate_history(self, value):
        cleaned = []
        for message in value:
            role = message.get("role")
            content = message.get("content")
            if role not in {"user", "assistant"}:
                raise serializers.ValidationError("El historial contiene un rol inválido.")
            if not isinstance(content, str) or not content.strip() or len(content) > 700:
                raise serializers.ValidationError("Un mensaje del historial no es válido.")
            cleaned.append({"role": role, "content": content.strip()})
        return cleaned
